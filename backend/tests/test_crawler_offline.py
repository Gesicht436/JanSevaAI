"""
Unit Tests for Offline Scheme Crawler & ETL Ingestion Pipeline (P1.1, P1.2)
Verifies pagination, deduplication by slug, and canonical database persistence with mock guard.
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Tuple
from Crawler.crawler import SchemeCrawler


class MockGuard:
    def __init__(self, pages: dict, details: dict):
        self.pages = pages
        self.details = details
        self.calls = []

    def fetch(self, url: str, check_robots: bool = True) -> Tuple[int, bytes, str]:
        self.calls.append(url)
        if "schemes?page=" in url:
            for page_num, data in self.pages.items():
                if f"page={page_num}&" in url:
                    return 200, json.dumps(data).encode("utf-8"), "application/json"
            # Past last page: empty hits
            return 200, json.dumps({"data": {"hits": {"items": []}}}).encode("utf-8"), "application/json"

        # Detail url
        slug = url.split("/")[-1]
        if slug in self.details:
            return 200, json.dumps(self.details[slug]).encode("utf-8"), "application/json"

        return 404, b"Not Found", "application/json"


def test_crawler_pagination_exhaustion_and_deduplication():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name

    try:
        pages = {
            0: {
                "data": {
                    "hits": {
                        "items": [
                            {"fields": {"slug": "scheme-1"}},
                            {"fields": {"slug": "scheme-2"}},
                            {"fields": {"slug": "scheme-1"}}  # Duplicate slug on same page
                        ]
                    }
                }
            },
            1: {
                "data": {
                    "hits": {
                        "items": [
                            {"fields": {"slug": "scheme-3"}},
                            {"fields": {"slug": "scheme-2"}}  # Duplicate slug across pages
                        ]
                    }
                }
            }
            # Page 2 has no hits -> ends pagination
        }

        details = {
            "scheme-1": {
                "fields": {
                    "schemeName": "Scheme 1",
                    "level": "Central",
                    "isAllState": True,
                    "eligibilityCriteria": "Applicant must be an Indian citizen.",
                    "documentsRequired": ["Aadhaar Card"]
                }
            },
            "scheme-2": {
                "fields": {
                    "schemeName": "Scheme 2",
                    "level": "State",
                    "beneficiaryState": ["Gujarat"],
                    "isAllState": False,
                    "eligibilityCriteria": "Must be resident of Gujarat.",
                    "documentsRequired": ["Ration Card"]
                }
            },
            "scheme-3": {
                "fields": {
                    "schemeName": "Scheme 3",
                    "level": "Central",
                    "isAllState": True,
                    "eligibilityCriteria": "Must be 18 years or older.",
                    "documentsRequired": []
                }
            }
        }

        crawler = SchemeCrawler(db_path=tmp_db, concurrency=1, delay_seconds=0.0)
        crawler.guard = MockGuard(pages, details)

        # Run crawl until catalog exhausted (target_count=None)
        count = crawler.run_crawl(target_count=None)
        assert count == 3, f"Expected 3 unique schemes ingested, got {count}"

        conn = sqlite3.connect(tmp_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT slug, name, all_states FROM schemes ORDER BY slug ASC")
        rows = cur.fetchall()
        assert len(rows) == 3
        assert [r["slug"] for r in rows] == ["scheme-1", "scheme-2", "scheme-3"]

        cur.execute("SELECT slug, line_text FROM scheme_sections WHERE section_name = 'eligibility' ORDER BY slug ASC")
        sec_rows = cur.fetchall()
        assert len(sec_rows) == 3

        cur.execute("SELECT slug, document_text, doc_type FROM scheme_documents ORDER BY slug ASC")
        doc_rows = cur.fetchall()
        assert len(doc_rows) == 2
        assert doc_rows[0]["doc_type"] == "aadhaar"
        assert doc_rows[1]["doc_type"] == "ration_card"

        conn.close()
        crawler.db.close()
    finally:
        try:
            Path(tmp_db).unlink(missing_ok=True)
        except Exception:
            pass
