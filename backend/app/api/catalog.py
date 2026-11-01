"""
Catalog Status API
"""

import sqlite3
from fastapi import APIRouter, Depends
from ..services.db import get_db

router = APIRouter()


@router.get("/catalog/status")
def get_catalog_status(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM schemes")
    total_schemes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT slug) FROM scheme_criteria")
    compiled_schemes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scheme_criteria")
    total_criteria = cursor.fetchone()[0]

    return {
        "status": "ready" if total_schemes > 0 else "empty",
        "total_schemes": total_schemes,
        "compiled_schemes": compiled_schemes,
        "total_criteria": total_criteria
    }
