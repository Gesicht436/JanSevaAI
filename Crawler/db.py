"""
Database Access Layer for Scheme Ingestion
Manages SQLite schema creation, migrations, and transactional inserts.
"""

import json
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional


class SchemeDatabase:
    def __init__(self, db_path: str = "Datasets/schemes.db"):
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
                scheme_for TEXT,
                priority INTEGER,
                level TEXT NOT NULL,
                beneficiary_states TEXT NOT NULL, -- JSON list
                all_states INTEGER NOT NULL,      -- 1 or 0
                categories TEXT NOT NULL,          -- JSON list
                sub_categories TEXT NOT NULL,      -- JSON list
                tags TEXT NOT NULL,                -- JSON list
                target_beneficiaries TEXT,
                brief_description TEXT,
                open_date TEXT,
                close_date TEXT,
                scheme_url TEXT NOT NULL,
                application_url TEXT,
                content_hash TEXT NOT NULL,
                crawled_at TEXT NOT NULL,
                last_modified_date TEXT
            );

            CREATE TABLE IF NOT EXISTS scheme_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                crawled_at TEXT NOT NULL,
                summary_diff TEXT,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
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
                doc_type TEXT,
                doc_text TEXT NOT NULL,
                is_mandatory INTEGER NOT NULL,
                source_line INTEGER,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
            );

            CREATE TABLE IF NOT EXISTS scheme_faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                faq_index INTEGER NOT NULL,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
            );

            CREATE TABLE IF NOT EXISTS list_pages (
                page_number INTEGER PRIMARY KEY,
                crawled_at TEXT NOT NULL,
                raw_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scheme_raw (
                slug TEXT PRIMARY KEY,
                crawled_at TEXT NOT NULL,
                raw_detail_json TEXT NOT NULL,
                raw_docs_json TEXT,
                raw_faqs_json TEXT,
                FOREIGN KEY (slug) REFERENCES schemes(slug)
            );

            CREATE TABLE IF NOT EXISTS criteria_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                verified_ratio REAL NOT NULL DEFAULT 0,
                evaluable_ratio REAL NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0,
                trace TEXT NOT NULL DEFAULT '[]',
                required_documents TEXT NOT NULL DEFAULT '[]',
                criteria TEXT NOT NULL DEFAULT '[]',
                model TEXT,
                prompt_version TEXT,
                compiled_at TEXT NOT NULL,
                UNIQUE(slug, content_hash)
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                message TEXT NOT NULL DEFAULT '',
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_scheme_sections_slug ON scheme_sections(slug);
            CREATE INDEX IF NOT EXISTS idx_scheme_documents_slug ON scheme_documents(slug);
            CREATE INDEX IF NOT EXISTS idx_criteria_sets_slug ON criteria_sets(slug);
            """)

    def _ensure_column(self, table: str, column: str, col_type: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row["name"] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def close(self) -> None:
        self.conn.close()
