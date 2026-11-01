"""
JanSeva AI - Main FastAPI Application
Assembles API routers, security middleware, request logging,
and SPA static frontend distribution.
"""

import logging
from pathlib import Path
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import health, catalog, schemes, profile, match, explain, tts, admin
from .config import settings
from .errors import AppError, app_error_handler, validation_error_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("janseva.api")


def create_app() -> FastAPI:
    app = FastAPI(
        title="JanSeva AI API",
        description="Verifiable, Hallucination-Free Government Scheme Matching for Indian Citizens",
        version="1.0.0"
    )

    # CORS Middleware
    origins = settings.cors_origin_list
    if not origins or "*" in origins:
        origins = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Standard Exception Handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # Request Logging & Tracing Middleware
    @app.middleware("http")
    async def request_trace_log(request: Request, call_next):
        req_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            latency = (time.perf_counter() - start_time) * 1000
            logger.exception(f"request_id={req_id} method={request.method} path={request.url.path} status=500 latency_ms={latency:.2f}")
            raise

        latency = (time.perf_counter() - start_time) * 1000
        logger.info(f"request_id={req_id} method={request.method} path={request.url.path} status={response.status_code} latency_ms={latency:.2f}")
        response.headers["X-Request-ID"] = req_id
        return response

    # Register API Endpoints
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(catalog.router, prefix="/api", tags=["catalog"])
    app.include_router(schemes.router, prefix="/api", tags=["schemes"])
    app.include_router(profile.router, prefix="/api", tags=["profile"])
    app.include_router(match.router, prefix="/api", tags=["match"])
    app.include_router(explain.router, prefix="/api", tags=["explain"])
    app.include_router(tts.router, prefix="/api", tags=["tts"])
    app.include_router(admin.router, prefix="/api", tags=["admin"])

    # Mount built SPA frontend if present
    dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if dist_dir.exists():
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa_frontend(full_path: str):
            if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
                return None
            index_path = dist_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return JSONResponse({"message": "Frontend distribution file not found."})
    else:
        @app.get("/")
        def api_root():
            return {
                "message": "JanSeva AI Backend API is running.",
                "docs": "/docs",
                "health": "/api/health",
                "catalog": "/api/catalog/status"
            }

    return app


app = create_app()
