"""
Database Service and SchemeStore
Provides thread-safe connections, FastAPI dependencies, and scheme query helpers.
"""

import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, Generator, List, Optional
from ..config import settings, Settings, get_settings


def get_db() -> Generator[sqlite3.Connection, None, None]:
    db_path = settings.resolved_database_path
    try:
        # Open in read-only and immutable mode (disables all file locks & journal creation in serverless)
        uri = f"file:{db_path.resolve().as_posix()}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    except Exception:
        # Fallback to standard connect
        conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_db_connection() -> sqlite3.Connection:
    db_path = settings.resolved_database_path
    try:
        uri = f"file:{db_path.resolve().as_posix()}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    except Exception:
        conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class SchemeStore:
    def __init__(self, settings_obj: Optional[Settings] = None):
        self.settings = settings_obj or get_settings()
        self.path = self.settings.resolved_database_path.resolve()
        self._lock = threading.Lock()

    def connect(self, readonly: bool = False) -> sqlite3.Connection:
        if readonly:
            conn = sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True, timeout=5)
        else:
            conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def list_schemes(self) -> List[Dict[str, Any]]:
        with self.connect(readonly=True) as conn:
            cursor = conn.execute("SELECT * FROM schemes ORDER BY name ASC")
            schemes = []
            for row in cursor.fetchall():
                d = dict(row)
                d["beneficiary_states"] = json.loads(d["beneficiary_states"]) if d.get("beneficiary_states") else []
                d["categories"] = json.loads(d["categories"]) if d.get("categories") else []
                schemes.append(d)
            return schemes

    def get_scheme(self, slug: str) -> Optional[Dict[str, Any]]:
        with self.connect(readonly=True) as conn:
            cursor = conn.execute("SELECT * FROM schemes WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["beneficiary_states"] = json.loads(d["beneficiary_states"]) if d.get("beneficiary_states") else []
            d["categories"] = json.loads(d["categories"]) if d.get("categories") else []
            return d

    def create_job(self, kind: str) -> str:
        import uuid
        import datetime
        job_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO jobs (id, kind, status, progress, message, created_at, updated_at) "
                "VALUES (?, ?, 'pending', 0, 'Job queued', ?, ?)",
                (job_id, kind, now, now),
            )
        return job_id

    def update_job(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        message: str = "",
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                "UPDATE jobs SET status=?, progress=?, message=?, result=?, error=?, updated_at=? WHERE id=?",
                (status, progress, message, result, error, now, job_id),
            )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.connect(readonly=True) as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return dict(row) if row else None
