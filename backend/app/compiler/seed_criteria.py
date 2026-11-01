"""
Seed Criteria Tool
Compiles and seeds verified criteria into SQLite.
"""

import datetime
import json
import sqlite3
from .rule_compiler import RuleCompiler
from .verifier import verify_scheme_criteria


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
        """)


def compile_all_schemes(db_path: str = "Datasets/schemes.db") -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_criteria_tables(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT slug, content_hash FROM schemes ORDER BY slug ASC")
    schemes = cursor.fetchall()
    compiler = RuleCompiler()
    total_criteria = 0

    with conn:
        conn.execute("DELETE FROM scheme_criteria")
        conn.execute("DELETE FROM scheme_compilation_trace")

        for s in schemes:
            slug = s["slug"]
            chash = s["content_hash"]

            cursor.execute(
                "SELECT line_index, line_text, 'eligibility' as section_name FROM scheme_sections WHERE slug = ? AND section_name = 'eligibility' ORDER BY line_index ASC",
                (slug,)
            )
            elig_lines = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                "SELECT line_index, line_text, 'exclusions' as section_name FROM scheme_sections WHERE slug = ? AND section_name = 'exclusions' ORDER BY line_index ASC",
                (slug,)
            )
            excl_lines = [dict(row) for row in cursor.fetchall()]

            criteria = []
            elig_crit = compiler.compile_section_lines(slug, "eligibility", elig_lines, start_counter=1)
            criteria.extend(elig_crit)
            excl_crit = compiler.compile_section_lines(slug, "exclusions", excl_lines, start_counter=len(criteria) + 1)
            criteria.extend(excl_crit)

            all_lines = elig_lines + excl_lines
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
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            trace_json = json.dumps([{"attempt": 1, "issues": issues}])
            conn.execute("""
            INSERT INTO scheme_compilation_trace (
                slug, content_hash, status, verified_ratio, attempts, trace, compiled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (slug, chash, status, verified_ratio, 1, trace_json, now))

    conn.close()
    return total_criteria
