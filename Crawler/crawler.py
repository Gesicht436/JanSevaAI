"""
Scheme Crawler Implementation (Rule L1, L2, L3, L4, L20)
Crawls scheme catalogs from myScheme APIs, extracts sections and documents,
computes deterministic content hashes, and persists structured records into SQLite and JSON.
"""

import concurrent.futures
import datetime
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from Crawler.guard import RequestGuard, DEFAULT_USER_AGENT
from Crawler.flattener import flatten_rich_text, clean_line_text
from Crawler.db import SchemeDatabase
from backend.app.models.documents import normalize_document_text

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
        db_path: str = "backend/Datasets/schemes.db",
        concurrency: int = 3,
        delay_seconds: float = 0.35,
        user_agent: Optional[str] = None
    ):
        self.db_path = db_path
        self.db = SchemeDatabase(db_path=db_path)
        self.concurrency = concurrency
        self.delay_seconds = delay_seconds
        self.guard = RequestGuard(
            user_agent=user_agent or DEFAULT_USER_AGENT,
            delay_seconds=delay_seconds
        )

    def run_crawl(
        self,
        target_count: Optional[int] = 200,
        export_json_path: Optional[str] = None
    ) -> int:
        """
        Crawls schemes from myScheme APIs.
        If target_count is None or 0, runs until catalog pagination is exhausted.
        """
        target_desc = f"{target_count} schemes" if target_count else "end-of-catalog"
        logger.info(f"Starting crawl targeting {target_desc}...")
        base_url = "https://www.myscheme.gov.in"
        page_size = 100
        page = 0
        items_crawled = 0
        seen_slugs: Set[str] = set()
        export_records = []

        while True:
            if target_count and items_crawled >= target_count:
                break

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
                logger.info("End of catalog reached: no more items.")
                break

            for item in items:
                if target_count and items_crawled >= target_count:
                    break

                fields = item.get("fields", {})
                slug = fields.get("slug")
                if not slug or slug in seen_slugs:
                    continue
                seen_slugs.add(slug)

                detail_url = f"{base_url}/api/v1/schemes/{slug}"
                try:
                    d_status, d_body, _ = self.guard.fetch(detail_url, check_robots=True)
                    if d_status != 200:
                        logger.warning(f"Scheme {slug} detail returned status {d_status}")
                        continue

                    raw_detail_text = d_body.decode("utf-8")
                    detail = json.loads(raw_detail_text)
                    self._persist_scheme_detail(slug, detail, raw_detail_text)
                    export_records.append(detail)
                    items_crawled += 1

                    if items_crawled % 25 == 0:
                        logger.info(f"Crawled and persisted {items_crawled} schemes...")
                except Exception as e:
                    logger.warning(f"Failed to process scheme {slug}: {e}")

            page += 1

        if export_records and export_json_path:
            os.makedirs(os.path.dirname(os.path.abspath(export_json_path)), exist_ok=True)
            with open(export_json_path, "w", encoding="utf-8") as f:
                json.dump(export_records, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(export_records)} records to {export_json_path}")

        return items_crawled

    def _persist_scheme_detail(self, slug: str, detail: Dict[str, Any], raw_json: str) -> None:
        """Parses and stores scheme detail into canonical SQLite tables."""
        fields = detail.get("fields", detail)
        name = fields.get("schemeName") or fields.get("name") or slug
        short_title = fields.get("schemeShortTitle") or fields.get("short_title")
        level = fields.get("level") or "Central"
        ministry = fields.get("nodalMinistryName") or fields.get("ministry")
        department = fields.get("nodalDepartmentName") or fields.get("department")
        b_states = fields.get("beneficiaryState") or fields.get("beneficiary_states") or []
        if isinstance(b_states, str):
            b_states = [b_states]
        all_states = bool(fields.get("isAllState") or fields.get("all_states") or False)
        categories = fields.get("schemeCategory") or fields.get("categories") or []
        sub_cats = fields.get("schemeSubCategory") or fields.get("sub_categories") or []
        tags = fields.get("tags") or []
        brief = fields.get("briefDescription") or fields.get("brief_description")
        close_date = fields.get("closeDate") or fields.get("close_date")
        open_date = fields.get("openDate") or fields.get("open_date")

        # Extract and flatten sections
        sections_dict: Dict[str, List[str]] = {}
        for sec_key, raw_sec in [
            ("eligibility", fields.get("eligibilityCriteria")),
            ("exclusions", fields.get("exclusions")),
            ("benefits", fields.get("benefits")),
            ("details", fields.get("detailedDescription")),
            ("documents_required", fields.get("documentsRequired"))
        ]:
            lines, _ = flatten_rich_text(raw_sec)
            sections_dict[sec_key] = lines

        # Normalization map for documents
        doc_map = {doc: normalize_document_text(doc) for doc in sections_dict.get("documents_required", [])}

        chash = compute_content_hash(
            eligibility_lines=sections_dict.get("eligibility", []),
            exclusions_lines=sections_dict.get("exclusions", []),
            benefits_lines=sections_dict.get("benefits", []),
            process_lines=sections_dict.get("application_process", []),
            documents_lines=sections_dict.get("documents_required", [])
        )

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.db.insert_scheme(
            slug=slug,
            name=name,
            short_title=short_title,
            ministry=ministry,
            department=department,
            level=level,
            beneficiary_states=b_states,
            all_states=all_states,
            categories=categories,
            sub_categories=sub_cats,
            scheme_type=fields.get("schemeType"),
            benefit_type=fields.get("benefitType"),
            tags=tags,
            brief_description=brief,
            close_date=close_date,
            open_date=open_date,
            sections=sections_dict,
            application_process=fields.get("applicationProcess", []),
            source_links=fields.get("sourceLinks", []),
            content_hash=chash,
            fetched_at=now,
            raw_detail_json=raw_json,
            doc_type_map=doc_map
        )
