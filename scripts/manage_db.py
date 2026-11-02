"""
Database Optimization, Indexing, and Verification Script
Runs EXPLAIN QUERY PLAN, builds composite indexes, populates doc_type,
and verifies SQLite database integrity.
"""

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.models.documents import normalize_document_text

CANONICAL_DB_PATH = PROJECT_ROOT / "backend" / "Datasets" / "schemes.db"


def run_explain_plans(conn: sqlite3.Connection, stage: str = "BEFORE"):
    print(f"\n--- EXPLAIN QUERY PLAN ({stage} INDEXING) ---")
    queries = [
        ("Scheme Catalog Order", "EXPLAIN QUERY PLAN SELECT slug, name, COALESCE(ministry, department, ''), level FROM schemes ORDER BY name, slug LIMIT 50 OFFSET 0;"),
        ("Sections Lookup", "EXPLAIN QUERY PLAN SELECT section_name, line_index, line_text FROM scheme_sections WHERE slug = 'aspfts12ps' ORDER BY section_name, line_index;"),
        ("Documents Lookup", "EXPLAIN QUERY PLAN SELECT line_index, document_text FROM scheme_documents WHERE slug = 'aspfts12ps' ORDER BY line_index;"),
        ("Criteria Lookup", "EXPLAIN QUERY PLAN SELECT * FROM scheme_criteria WHERE slug = 'aspfts12ps' ORDER BY group_id, criterion_id;"),
        ("Versions Lookup", "EXPLAIN QUERY PLAN SELECT * FROM scheme_versions WHERE slug = 'aspfts12ps' ORDER BY id DESC;")
    ]
    cur = conn.cursor()
    for name, q in queries:
        cur.execute(q)
        plan = " | ".join(row[3] for row in cur.fetchall())
        print(f"  [{name}]: {plan}")


def add_composite_indexes_and_doc_types(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Show query plan before
    run_explain_plans(conn, stage="BEFORE")

    with conn:
        # 1. Add doc_type column to scheme_documents if not present
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(scheme_documents)")
        cols = [r["name"] for r in cur.fetchall()]
        if "doc_type" not in cols:
            print("\nAdding 'doc_type' column to scheme_documents...")
            conn.execute("ALTER TABLE scheme_documents ADD COLUMN doc_type TEXT")

        # 2. Populate doc_type
        print("Populating 'doc_type' with normalized document types...")
        cur.execute("SELECT id, document_text FROM scheme_documents")
        updates = []
        for r in cur.fetchall():
            norm = normalize_document_text(r["document_text"])
            updates.append((norm, r["id"]))
        cur.executemany("UPDATE scheme_documents SET doc_type = ? WHERE id = ?", updates)
        print(f"Updated {len(updates)} documents with normalized doc_type.")

        # 3. Create composite indexes
        print("\nCreating composite indexes...")
        conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_schemes_name_slug
            ON schemes(name, slug);

        CREATE INDEX IF NOT EXISTS idx_scheme_sections_slug_section_line
            ON scheme_sections(slug, section_name, line_index);

        CREATE INDEX IF NOT EXISTS idx_scheme_documents_slug_line
            ON scheme_documents(slug, line_index);

        CREATE INDEX IF NOT EXISTS idx_scheme_criteria_slug_group_criterion
            ON scheme_criteria(slug, group_id, criterion_id);

        CREATE INDEX IF NOT EXISTS idx_scheme_versions_slug_id
            ON scheme_versions(slug, id DESC);
        """)

    # Show query plan after
    run_explain_plans(conn, stage="AFTER")

    # Run integrity and foreign key checks
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchone()[0]
    print(f"\nPRAGMA integrity_check: {integrity}")
    assert integrity == "ok", f"Integrity check failed: {integrity}"

    cur.execute("PRAGMA foreign_key_check;")
    fk_violations = cur.fetchall()
    print(f"PRAGMA foreign_key_check violations: {len(fk_violations)}")

    # Checkpoint WAL
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()


def generate_database_report(db_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM schemes")
    total_schemes = cur.fetchone()[0]

    cur.execute("SELECT categories FROM schemes WHERE categories IS NOT NULL")
    all_cats = set()
    for r in cur.fetchall():
        try:
            cats = json.loads(r[0])
            for c in cats:
                all_cats.add(c)
        except Exception:
            pass

    cur.execute("SELECT COUNT(*) FROM scheme_criteria")
    total_criteria = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM scheme_criteria WHERE quote_verified = 1")
    verified_quotes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM scheme_criteria WHERE operator != 'unverifiable' AND field IS NOT NULL")
    evaluable_criteria = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM scheme_criteria WHERE operator = 'unverifiable' OR field IS NULL")
    unresolved_criteria = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM scheme_documents")
    total_docs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM scheme_documents WHERE doc_type IS NOT NULL")
    normalized_docs = cur.fetchone()[0]

    cur.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    indexes = [r[0] for r in cur.fetchall()]

    # File size and SHA256
    file_size_bytes = db_path.stat().st_size
    hasher = hashlib.sha256()
    with open(db_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    file_hash = hasher.hexdigest()

    conn.close()

    report = {
        "database_path": str(db_path),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
        "sha256": file_hash,
        "total_schemes": total_schemes,
        "distinct_category_count": len(all_cats),
        "categories": sorted(list(all_cats)),
        "total_criteria": total_criteria,
        "quote_verified_count": verified_quotes,
        "quote_verified_ratio": round(verified_quotes / total_criteria, 4) if total_criteria else 0,
        "evaluable_criteria_count": evaluable_criteria,
        "evaluable_ratio": round(evaluable_criteria / total_criteria, 4) if total_criteria else 0,
        "unresolved_criteria_count": unresolved_criteria,
        "unresolved_ratio": round(unresolved_criteria / total_criteria, 4) if total_criteria else 0,
        "total_documents": total_docs,
        "normalized_documents_count": normalized_docs,
        "indexes": sorted(indexes)
    }

    print("\n================ DATABASE BUILD REPORT ================")
    print(f"Path:                      {report['database_path']}")
    print(f"Size:                      {report['file_size_mb']} MB ({report['file_size_bytes']} bytes)")
    print(f"SHA256:                    {report['sha256']}")
    print(f"Total Schemes:             {report['total_schemes']}")
    print(f"Distinct Categories:       {report['distinct_category_count']}")
    print(f"Total Criteria:            {report['total_criteria']}")
    print(f"Quote Verified Ratio:      {report['quote_verified_ratio']:.2%}")
    print(f"Evaluable Ratio:           {report['evaluable_ratio']:.2%}")
    print(f"Unresolved/Unverifiable:   {report['unresolved_ratio']:.2%}")
    print(f"Total Required Documents:  {report['total_documents']} ({report['normalized_documents_count']} normalized)")
    print(f"Total Indexes:             {len(report['indexes'])}")
    print("=======================================================\n")

    return report


if __name__ == "__main__":
    db_file = CANONICAL_DB_PATH
    print(f"Processing canonical database at: {db_file}")
    add_composite_indexes_and_doc_types(db_file)
    rep = generate_database_report(db_file)
    with open(PROJECT_ROOT / "database_report.json", "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print("Report saved to database_report.json")
