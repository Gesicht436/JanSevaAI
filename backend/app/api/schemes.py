"""
Scheme Details, Criteria & Change Audit API
"""

import json
import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from ..config import settings
from ..services.db import get_db

router = APIRouter()


@router.get("/schemes")
def list_schemes(limit: int = 50, offset: int = 0, db: sqlite3.Connection = Depends(get_db)):
    """List schemes with pagination."""
    cursor = db.cursor()
    cursor.execute("SELECT slug, name, COALESCE(ministry, department, '') AS ministry_or_department, level FROM schemes ORDER BY name ASC, slug ASC LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    return {"schemes": [dict(r) for r in rows], "limit": limit, "offset": offset}


@router.get("/schemes/{slug}")
def get_scheme_by_slug(slug: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM schemes WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Scheme '{slug}' not found.")

    scheme = dict(row)
    for col in ("beneficiary_states", "categories", "sub_categories", "tags"):
        if scheme.get(col):
            try:
                scheme[col] = json.loads(scheme[col])
            except Exception:
                scheme[col] = []

    # Fetch sections
    cursor.execute("SELECT section_name, line_index, line_text FROM scheme_sections WHERE slug = ? ORDER BY section_name, line_index", (slug,))
    sections = {}
    for r in cursor.fetchall():
        sec = r["section_name"]
        sections.setdefault(sec, []).append(r["line_text"])
    scheme["sections"] = sections

    # Fetch documents
    cursor.execute("SELECT line_index, document_text FROM scheme_documents WHERE slug = ? ORDER BY line_index", (slug,))
    scheme["documents"] = [dict(r) for r in cursor.fetchall()]
    scheme["myscheme_url"] = f"{settings.MYSCHEME_BASE_URL.rstrip('/')}/schemes/{slug}"
    scheme["description"] = scheme.get("brief_description") or ""

    return scheme


@router.get("/schemes/{slug}/criteria")
def get_scheme_criteria(slug: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM scheme_criteria WHERE slug = ? ORDER BY group_id, criterion_id", (slug,))
    rows = cursor.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No compiled criteria for '{slug}'.")

    criteria = []
    for r in rows:
        d = dict(r)
        d["value"] = json.loads(d["value"]) if d.get("value") is not None else None
        criteria.append(d)

    cursor.execute("SELECT * FROM scheme_compilation_trace WHERE slug = ?", (slug,))
    trace_row = cursor.fetchone()
    trace_data = dict(trace_row) if trace_row else {}

    return {
        "slug": slug,
        "criteria": criteria,
        "verified_ratio": trace_data.get("verified_ratio", 1.0),
        "status": trace_data.get("status", "compiled")
    }


@router.get("/schemes/{slug}/changes")
def get_scheme_changes(slug: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM scheme_versions WHERE slug = ? ORDER BY id DESC", (slug,))
    rows = cursor.fetchall()
    return {"slug": slug, "versions": [dict(r) for r in rows]}
