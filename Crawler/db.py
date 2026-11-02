"""
Database Access Layer for Scheme Ingestion (Canonical Schema)
Manages SQLite canonical schema creation, migrations, and transactional inserts.
Matches backend production schema exactly.
"""

import json
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional


class SchemeDatabase:
    def __init__(self, db_path: str = "backend/Datasets/schemes.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self.conn:
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS schemes (
                slug TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                short_title TEXT,
                ministry TEXT,
                department TEXT,
                level TEXT NOT NULL,
                beneficiary_states TEXT NOT NULL, -- JSON list
                all_states INTEGER NOT NULL,      -- 1 or 0
                categories TEXT NOT NULL,         -- JSON list
                sub_categories TEXT,              -- JSON list
                scheme_type TEXT,
                benefit_type TEXT,
                tags TEXT,                        -- JSON list
                brief_description TEXT,
                close_date TEXT,
                open_date TEXT,
                sections TEXT NOT NULL,           -- JSON object: details, benefits, eligibility, exclusions, documents_required, faqs
                application_process TEXT NOT NULL,-- JSON list of {mode, lines, links, url}
                source_links TEXT NOT NULL,       -- JSON list of {label, url}
                content_hash TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                list_fetched_at TEXT NOT NULL,
                fetch_strategy TEXT NOT NULL DEFAULT 'api'
            );

            CREATE TABLE IF NOT EXISTS scheme_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                sections TEXT NOT NULL,
                application_process TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                UNIQUE(slug, content_hash)
            );

            CREATE TABLE IF NOT EXISTS scheme_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                section_name TEXT NOT NULL,
                line_index INTEGER NOT NULL,
                line_text TEXT NOT NULL,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
            );

            CREATE TABLE IF NOT EXISTS scheme_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                line_index INTEGER NOT NULL,
                document_text TEXT NOT NULL,
                doc_type TEXT,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
            );

            CREATE TABLE IF NOT EXISTS scheme_faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                faq_index INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
            );

            CREATE TABLE IF NOT EXISTS list_pages (
                offset INTEGER NOT NULL,
                size INTEGER NOT NULL,
                fetched_at TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                PRIMARY KEY (offset, size)
            );

            CREATE TABLE IF NOT EXISTS scheme_raw (
                slug TEXT PRIMARY KEY,
                fetched_at TEXT NOT NULL,
                raw_detail TEXT NOT NULL,
                raw_documents TEXT,
                raw_faqs TEXT
            );

            CREATE TABLE IF NOT EXISTS scheme_criteria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                criterion_id TEXT NOT NULL,
                group_id INTEGER NOT NULL DEFAULT 1,
                kind TEXT NOT NULL, -- requirement or exclusion
                field TEXT,         -- CitizenProfile field name or null
                operator TEXT NOT NULL,
                value TEXT,         -- JSON encoded value
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
                status TEXT NOT NULL, -- compiled, partial, failed
                verified_ratio REAL NOT NULL,
                attempts INTEGER NOT NULL,
                trace TEXT NOT NULL,
                compiled_at TEXT NOT NULL,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
            );

            -- Indexes for production performance (P1.1)
            CREATE INDEX IF NOT EXISTS idx_schemes_name_slug ON schemes(name, slug);
            CREATE INDEX IF NOT EXISTS idx_schemes_level ON schemes(level);
            CREATE INDEX IF NOT EXISTS idx_schemes_close_date ON schemes(close_date);
            CREATE INDEX IF NOT EXISTS idx_scheme_sections_slug_section_line ON scheme_sections(slug, section_name, line_index);
            CREATE INDEX IF NOT EXISTS idx_scheme_documents_slug_line ON scheme_documents(slug, line_index);
            CREATE INDEX IF NOT EXISTS idx_scheme_criteria_slug_group_criterion ON scheme_criteria(slug, group_id, criterion_id);
            CREATE INDEX IF NOT EXISTS idx_scheme_versions_slug_id ON scheme_versions(slug, id DESC);
            CREATE INDEX IF NOT EXISTS idx_criteria_field ON scheme_criteria(field);
            """)

    def insert_scheme(
        self,
        slug: str,
        name: str,
        short_title: Optional[str],
        ministry: Optional[str],
        department: Optional[str],
        level: str,
        beneficiary_states: List[str],
        all_states: bool,
        categories: List[str],
        sub_categories: List[str],
        scheme_type: Optional[str],
        benefit_type: Optional[str],
        tags: List[str],
        brief_description: Optional[str],
        close_date: Optional[str],
        open_date: Optional[str],
        sections: Dict[str, List[str]],
        application_process: List[Any],
        source_links: List[Any],
        content_hash: str,
        fetched_at: str,
        raw_detail_json: str,
        doc_type_map: Optional[Dict[str, Optional[str]]] = None
    ) -> None:
        """Atomically inserts or updates a crawled scheme and its normalized sections."""
        with self._lock, self.conn:
            # 1. Insert scheme
            self.conn.execute("""
            INSERT OR REPLACE INTO schemes (
                slug, name, short_title, ministry, department, level,
                beneficiary_states, all_states, categories, sub_categories,
                scheme_type, benefit_type, tags, brief_description,
                close_date, open_date, sections, application_process,
                source_links, content_hash, fetched_at, list_fetched_at, fetch_strategy
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slug, name, short_title, ministry, department, level,
                json.dumps(beneficiary_states), 1 if all_states else 0,
                json.dumps(categories), json.dumps(sub_categories),
                scheme_type, benefit_type, json.dumps(tags), brief_description,
                close_date, open_date, json.dumps(sections),
                json.dumps(application_process), json.dumps(source_links),
                content_hash, fetched_at, fetched_at, "api"
            ))

            # 2. Insert scheme raw
            self.conn.execute("""
            INSERT OR REPLACE INTO scheme_raw (slug, fetched_at, raw_detail)
            VALUES (?, ?, ?)
            """, (slug, fetched_at, raw_detail_json))

            # 3. Clean and insert sections
            self.conn.execute("DELETE FROM scheme_sections WHERE slug = ?", (slug,))
            for sec_name, lines in sections.items():
                if sec_name in ("eligibility", "exclusions", "benefits", "details"):
                    for idx, line in enumerate(lines):
                        self.conn.execute("""
                        INSERT INTO scheme_sections (slug, section_name, line_index, line_text)
                        VALUES (?, ?, ?, ?)
                        """, (slug, sec_name, idx, line))

            # 4. Clean and insert documents
            self.conn.execute("DELETE FROM scheme_documents WHERE slug = ?", (slug,))
            doc_lines = sections.get("documents_required", [])
            for idx, doc_text in enumerate(doc_lines):
                dtype = doc_type_map.get(doc_text) if doc_type_map else None
                self.conn.execute("""
                INSERT INTO scheme_documents (slug, line_index, document_text, doc_type)
                VALUES (?, ?, ?, ?)
                """, (slug, idx, doc_text, dtype))

    def close(self) -> None:
        self.conn.close()
