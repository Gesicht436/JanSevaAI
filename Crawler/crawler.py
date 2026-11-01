"""
Scheme Crawler Implementation (Rule L1, L2, L3, L4, L20)
Crawls scheme catalogs from myScheme APIs, extracts sections and documents,
computes deterministic content hashes, and persists structured records into SQLite and JSON.
"""

import concurrent.futures
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from Crawler.guard import RequestGuard, DEFAULT_USER_AGENT
from Crawler.flattener import flatten_rich_text, clean_line_text
from Crawler.db import SchemeDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Crawler")


def compute_content_hash(
    eligibility_lines: List[str],
    exclusions_lines: List[str],
    benefits_lines: List[str],
    process_lines: List[str],
    documents_lines: List[str]
) -> str:
    """Computes a deterministic SHA-256 hash across all criteria-bearing lines."""
    hasher = hashlib.sha256()
    payload = {
        "eligibility": eligibility_lines,
        "exclusions": exclusions_lines,
        "benefits": benefits_lines,
        "application_process": process_lines,
        "documents_required": documents_lines
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    hasher.update(encoded)
    return hasher.hexdigest()


class SchemeCrawler:
    def __init__(
        self,
        db_path: str = "Datasets/schemes.db",
        concurrency: int = 3,
        delay_seconds: float = 0.35,
        user_agent: Optional[str] = None
    ):
        self.db = SchemeDatabase(db_path=db_path)
        self.concurrency = concurrency
        self.delay_seconds = delay_seconds
        self.guard = RequestGuard(
            user_agent=user_agent or DEFAULT_USER_AGENT,
            delay_seconds=delay_seconds
        )

    def run_crawl(
        self,
        target_count: int = 200,
        export_json_path: str = "Datasets/schemes.json"
    ) -> int:
        logger.info(f"Starting crawl targeting {target_count} schemes...")
        base_url = "https://www.myscheme.gov.in"
        page_size = 100
        page = 0
        items_crawled = 0
        export_records = []

        while items_crawled < target_count:
            list_url = f"{base_url}/api/v1/schemes?page={page}&size={page_size}"
            logger.info(f"Fetching list page {page}...")
            try:
                status, body, _ = self.guard.fetch(list_url, check_robots=True)
                if status != 200:
                    logger.warning(f"List page {page} returned status {status}. Halting.")
                    break
                doc = json.loads(body.decode("utf-8"))
            except Exception as e:
                logger.error(f"Failed to fetch list page {page}: {e}")
                break

            items = doc.get("data", {}).get("hits", {}).get("items", [])
            if not items:
                logger.info("No more items found in catalog.")
                break

            for item in items:
                if items_crawled >= target_count:
                    break
                fields = item.get("fields", {})
                slug = fields.get("slug")
                if not slug:
                    continue

                detail_url = f"{base_url}/api/v1/schemes/{slug}"
                try:
                    d_status, d_body, _ = self.guard.fetch(detail_url, check_robots=True)
                    if d_status == 200:
                        detail = json.loads(d_body.decode("utf-8"))
                        export_records.append(detail)
                        items_crawled += 1
                        if items_crawled % 25 == 0:
                            logger.info(f"Crawled {items_crawled}/{target_count} schemes...")
                except Exception as e:
                    logger.warning(f"Failed to fetch scheme {slug}: {e}")

            page += 1

        if export_records and export_json_path:
            os.makedirs(os.path.dirname(os.path.abspath(export_json_path)), exist_ok=True)
            with open(export_json_path, "w", encoding="utf-8") as f:
                json.dump(export_records, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(export_records)} records to {export_json_path}")

        return items_crawled
