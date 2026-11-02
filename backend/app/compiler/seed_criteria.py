"""
Seed Criteria Tool (Offline Batch Compiler)
Compiles and seeds verified criteria into SQLite using either
deterministic RuleCompiler or LLM Compiler with retry loop.
"""

import datetime
import json
import sqlite3
from typing import Any, List, Optional
from .rule_compiler import RuleCompiler
from .verifier import verify_scheme_criteria
from .retry_loop import compile_scheme
from .llm_compiler import LLMCompilerClient


def init_criteria_tables(conn: sqlite3.Connection):
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS scheme_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            criterion_id TEXT NOT NULL,
            group_id INTEGER NOT NULL DEFAULT 1,
            kind TEXT NOT NULL,
            field TEXT,
            operator TEXT NOT NULL,
            value TEXT,
            source_section TEXT NOT NULL,
            source_line INTEGER NOT NULL,
            source_quote TEXT NOT NULL,
            quote_verified INTEGER NOT NULL DEFAULT 1,
            note TEXT,
            FOREIGN KEY (slug) REFERENCES schemes(slug)
        );

        CREATE TABLE IF NOT EXISTS scheme_compilation_trace (
            slug TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            verified_ratio REAL NOT NULL,
            attempts INTEGER NOT NULL,
            trace TEXT NOT NULL,
            compiled_at TEXT NOT NULL,
            FOREIGN KEY (slug) REFERENCES schemes(slug)
        );

        CREATE INDEX IF NOT EXISTS idx_criteria_slug ON scheme_criteria(slug);
        CREATE INDEX IF NOT EXISTS idx_criteria_field ON scheme_criteria(field);
        CREATE INDEX IF NOT EXISTS idx_scheme_criteria_slug_group_criterion ON scheme_criteria(slug, group_id, criterion_id);
        """)


def compile_all_schemes(
    db_path: str = "backend/Datasets/schemes.db",
    use_llm: bool = False,
    llm_client: Optional[Any] = None,
    slug_filter: Optional[List[str]] = None
) -> int:
    """
    Offline batch criteria compilation.
    Supports deterministic rule compilation and offline LLM compilation with retry loop.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_criteria_tables(conn)

    cursor = conn.cursor()
    if slug_filter:
        placeholders = ",".join("?" for _ in slug_filter)
        cursor.execute(f"SELECT slug, name, content_hash FROM schemes WHERE slug IN ({placeholders}) ORDER BY slug ASC", slug_filter)
    else:
        cursor.execute("SELECT slug, name, content_hash FROM schemes ORDER BY slug ASC")
    schemes = cursor.fetchall()

    compiler = RuleCompiler()
    client = llm_client or (LLMCompilerClient() if use_llm else None)
    total_criteria = 0

    with conn:
        if not slug_filter:
            conn.execute("DELETE FROM scheme_criteria")
            conn.execute("DELETE FROM scheme_compilation_trace")

        for s in schemes:
            slug = s["slug"]
            name = s["name"]
            chash = s["content_hash"]

            if slug_filter:
                conn.execute("DELETE FROM scheme_criteria WHERE slug = ?", (slug,))
                conn.execute("DELETE FROM scheme_compilation_trace WHERE slug = ?", (slug,))

            cursor.execute(
                "SELECT line_index, line_text FROM scheme_sections WHERE slug = ? AND section_name = 'eligibility' ORDER BY line_index ASC",
                (slug,)
            )
            elig_lines = [r["line_text"] for r in cursor.fetchall()]

            cursor.execute(
                "SELECT line_index, line_text FROM scheme_sections WHERE slug = ? AND section_name = 'exclusions' ORDER BY line_index ASC",
                (slug,)
            )
            excl_lines = [r["line_text"] for r in cursor.fetchall()]

            cursor.execute(
                "SELECT line_index, document_text FROM scheme_documents WHERE slug = ? ORDER BY line_index ASC",
                (slug,)
            )
            doc_lines = [r["document_text"] for r in cursor.fetchall()]

            if use_llm and client:
                # LLM Compilation with retry loop
                scheme_input = {
                    "name": name,
                    "sections": {
                        "eligibility": elig_lines,
                        "exclusions": excl_lines,
                        "documents_required": doc_lines
                    }
                }
                res = compile_scheme(scheme_input, llm_client=client, max_attempts=3)
                criteria_list = res.get("criteria", [])
                status = res.get("status", "partial")
                verified_ratio = res.get("verified_ratio", 0.0)
                attempts = res.get("attempts", 1)
                trace_json = json.dumps(res.get("trace", []))

                for c in criteria_list:
                    val_json = json.dumps(c.get("value")) if c.get("value") is not None else None
                    conn.execute("""
                    INSERT INTO scheme_criteria (
                        slug, criterion_id, group_id, kind, field, operator, value,
                        source_section, source_line, source_quote, quote_verified, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        slug, c["id"], c["group_id"], c["kind"], c.get("field"), c["operator"],
                        val_json, c["source_section"], c["source_line"], c["source_quote"],
                        1 if c.get("quote_verified") else 0, c.get("note")
                    ))
                    total_criteria += 1
            else:
                # Deterministic Regex compilation
                cursor.execute(
                    "SELECT line_index, line_text, 'eligibility' as section_name FROM scheme_sections WHERE slug = ? AND section_name = 'eligibility' ORDER BY line_index ASC",
                    (slug,)
                )
                elig_dicts = [dict(row) for row in cursor.fetchall()]

                cursor.execute(
                    "SELECT line_index, line_text, 'exclusions' as section_name FROM scheme_sections WHERE slug = ? AND section_name = 'exclusions' ORDER BY line_index ASC",
                    (slug,)
                )
                excl_dicts = [dict(row) for row in cursor.fetchall()]

                criteria = []
                elig_crit = compiler.compile_section_lines(slug, "eligibility", elig_dicts, start_counter=1)
                criteria.extend(elig_crit)
                excl_crit = compiler.compile_section_lines(slug, "exclusions", excl_dicts, start_counter=len(criteria) + 1)
                criteria.extend(excl_crit)

                all_lines = elig_dicts + excl_dicts
                is_verified, verified_ratio, issues = verify_scheme_criteria(criteria, all_lines)

                for c in criteria:
                    val_json = json.dumps(c["value"]) if c["value"] is not None else None
                    conn.execute("""
                    INSERT INTO scheme_criteria (
                        slug, criterion_id, group_id, kind, field, operator, value,
                        source_section, source_line, source_quote, quote_verified, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        slug, c["id"], c["group_id"], c["kind"], c["field"], c["operator"],
                        val_json, c["source_section"], c["source_line"], c["source_quote"],
                        1 if c.get("quote_verified") else 0, c.get("note")
                    ))
                    total_criteria += 1

                status = "compiled" if is_verified else "partial"
                attempts = 1
                trace_json = json.dumps([{"attempt": 1, "issues": issues}])

            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            conn.execute("""
            INSERT INTO scheme_compilation_trace (
                slug, content_hash, status, verified_ratio, attempts, trace, compiled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (slug, chash, status, verified_ratio, attempts, trace_json, now))

    conn.close()
    return total_criteria
