"""
Admin Background Jobs API
"""

import threading
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..config import settings
from ..services.db import SchemeStore

router = APIRouter()
store = SchemeStore()


class AdminCrawlPayload(BaseModel):
    limit: int = 200


class AdminCompilePayload(BaseModel):
    force: bool = False


def _verify_admin(token: Optional[str] = Header(None, alias="X-Admin-Token")):
    if not settings.ADMIN_TOKEN:
        return
    if not token or token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin authorization token.")


@router.post("/admin/crawl", status_code=202)
def trigger_crawl(payload: AdminCrawlPayload, background_tasks: BackgroundTasks, _: None = Header(None, alias="X-Admin-Token")):
    job_id = store.create_job("crawl")

    def run_crawl_job():
        from Crawler.crawler import SchemeCrawler
        store.update_job(job_id, "running", 10, "Crawl starting")
        try:
            crawler = SchemeCrawler(db_path=settings.DATABASE_PATH, concurrency=settings.CRAWL_CONCURRENCY)
            count = crawler.run_crawl(target_count=payload.limit)
            store.update_job(job_id, "completed", 100, f"Successfully crawled {count} schemes")
        except Exception as e:
            store.update_job(job_id, "failed", 0, "Crawl failed", error=str(e))

    background_tasks.add_task(run_crawl_job)
    return {"job_id": job_id, "status": "accepted"}


@router.post("/admin/compile", status_code=202)
def trigger_compile(payload: AdminCompilePayload, background_tasks: BackgroundTasks, _: None = Header(None, alias="X-Admin-Token")):
    job_id = store.create_job("compile")

    def run_compile_job():
        from ..compiler.seed_criteria import compile_all_schemes
        store.update_job(job_id, "running", 20, "Batch rule compilation starting")
        try:
            count = compile_all_schemes(settings.DATABASE_PATH)
            store.update_job(job_id, "completed", 100, f"Compiled {count} verified criteria")
        except Exception as e:
            store.update_job(job_id, "failed", 0, "Compilation failed", error=str(e))

    background_tasks.add_task(run_compile_job)
    return {"job_id": job_id, "status": "accepted"}


@router.get("/admin/jobs/{job_id}")
def get_job_status(job_id: str, _: None = Header(None, alias="X-Admin-Token")):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
