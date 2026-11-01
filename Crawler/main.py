"""
Crawler CLI entry point
"""

import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Crawler.crawler import SchemeCrawler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="JanSevaAI Scheme Crawler")
    parser.add_argument("--limit", type=int, default=200, help="Number of schemes to crawl (default: 200)")
    parser.add_argument("--db-path", type=str, default="Datasets/schemes.db", help="Path to SQLite database")
    parser.add_argument("--export-json", type=str, default="Datasets/schemes.json", help="Path to exported JSON file")
    parser.add_argument("--concurrency", type=int, default=3, help="Detail-fetch workers")
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between requests in seconds")

    args = parser.parse_args()

    crawler = SchemeCrawler(
        db_path=args.db_path,
        concurrency=args.concurrency,
        delay_seconds=args.delay
    )
    count = crawler.run_crawl(target_count=args.limit, export_json_path=args.export_json)
    print(f"Crawl completed. Ingested {count} schemes.")


if __name__ == "__main__":
    main()
