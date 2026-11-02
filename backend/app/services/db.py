"""
Database Service and SchemeStore (Rule L1, L10, Strict Read-Only Serverless)
Provides thread-safe read-only connections, process-level caching,
and PRAGMA query_only = ON enforcement for serverless deployment.
"""

import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, Generator, List, Optional

from ..config import settings, Settings, get_settings

_local = threading.local()
_all_conns: List[sqlite3.Connection] = []
_all_conns_lock = threading.Lock()


def open_readonly_connection(db_path: Path) -> sqlite3.Connection:
    """
    Opens SQLite database in strict read-only mode and enforces PRAGMA query_only = ON.
    Fails closed immediately if database is missing, unreadable, or query_only cannot be verified.
    Never falls back to a writable connection.
    """
    resolved = db_path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Database artifact not found at {resolved}. Production requires precompiled database.")

    # SQLite read-only URI mode
    uri = f"file:{resolved.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row

    # Enforce and verify PRAGMA query_only = ON
    conn.execute("PRAGMA query_only = ON;")
    cursor = conn.cursor()
    cursor.execute("PRAGMA query_only;")
    row = cursor.fetchone()
    if not row or row[0] != 1:
        conn.close()
        raise RuntimeError("Failed to verify PRAGMA query_only = ON on SQLite connection.")

    return conn


def get_db_connection() -> sqlite3.Connection:
    """
    Returns a thread-local cached read-only connection.
    Guarantees thread safety across concurrent FastAPI worker threads while reusing
    connections on warm requests without reconnection overhead.
    """
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = open_readonly_connection(settings.resolved_database_path)
        _local.conn = conn
        with _all_conns_lock:
            _all_conns.append(conn)
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency yielding the process-cached read-only database connection.
    Does not close the cached connection in request teardown.
    """
    conn = get_db_connection()
    yield conn


def reset_db_connection() -> None:
    """Closes and clears all cached connections (used for testing or clean shutdown)."""
    global _all_conns
    with _all_conns_lock:
        for c in _all_conns:
            try:
                c.close()
            except Exception:
                pass
        _all_conns.clear()
    if hasattr(_local, "conn"):
        _local.conn = None


class SchemeStore:
    def __init__(self, settings_obj: Optional[Settings] = None):
        self.settings = settings_obj or get_settings()
        self.path = self.settings.resolved_database_path.resolve()

    def connect(self, readonly: bool = True) -> sqlite3.Connection:
        # Production SchemeStore is strictly read-only
        return open_readonly_connection(self.path)

    def list_schemes(self) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM schemes ORDER BY name ASC")
        schemes = []
        for row in cursor.fetchall():
            d = dict(row)
            d["beneficiary_states"] = json.loads(d["beneficiary_states"]) if d.get("beneficiary_states") else []
            d["categories"] = json.loads(d["categories"]) if d.get("categories") else []
            schemes.append(d)
        return schemes

    def get_scheme(self, slug: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM schemes WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["beneficiary_states"] = json.loads(d["beneficiary_states"]) if d.get("beneficiary_states") else []
        d["categories"] = json.loads(d["categories"]) if d.get("categories") else []
        return d
