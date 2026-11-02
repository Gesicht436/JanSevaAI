"""
Integration Tests for Unified FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_catalog_status():
    res = client.get("/api/catalog/status")
    assert res.status_code == 200
    data = res.json()
    assert data["total_schemes"] >= 200
    assert data["compiled_schemes"] >= 200


def test_profile_extract():
    payload = {"text": "I am a 26 year old fellow, bachelor in IT, with some experience in IT sector, looking for a loan in Gujarat."}
    res = client.post("/api/profile/extract", json=payload)
    assert res.status_code == 200
    profile = res.json()["profile"]
    assert profile["age"] == 26
    assert profile["gender"] == "male"
    assert profile["qualification"] == "graduate"
    assert profile["current_sector"] == "it_tech"
    assert profile["state_ut"] == "Gujarat"
    assert profile["benefit_intent"] == "credit_loan"


def test_match_unconfirmed_enforces_rule_e9():
    payload = {
        "profile": {
            "state_ut": "Gujarat",
            "age": 26,
            "confirmed": False
        }
    }
    res = client.post("/api/match", json=payload)
    assert res.status_code == 400
    assert "rule e9" in res.json()["detail"].lower()


def test_match_confirmed_succeeds_and_tiers():
    payload = {
        "profile": {
            "state_ut": "Gujarat",
            "age": 26,
            "gender": "male",
            "caste_category": "sc",
            "qualification": "graduate",
            "current_sector": "it_tech",
            "annual_family_income_inr": 180000,
            "confirmed": True
        }
    }
    res = client.post("/api/match", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "counts" in data
    assert "results" in data
    assert data["counts"]["eligible"] > 0
    assert len(data["followup_fields"]) > 0
    first_eligible = data["results"]["eligible"][0]
    assert "myscheme.gov.in" in first_eligible["myscheme_url"]
    assert "description" in first_eligible
    assert isinstance(first_eligible["required_documents"], list)
    assert isinstance(first_eligible["specialized_criteria"], list)


def test_unknown_api_route_returns_404():
    res = client.get("/api/nonexistent-route-xyz")
    assert res.status_code == 404
    assert "not found" in res.json().get("detail", "").lower()


def test_admin_routes_removed_from_production():
    # Admin crawl / compile routes must not exist in production
    res1 = client.post("/api/admin/crawl", json={"limit": 10})
    assert res1.status_code == 404
    res2 = client.post("/api/admin/compile", json={"force": True})
    assert res2.status_code == 404


def test_explain_requires_confirmed_profile():
    payload = {
        "slug": "aspfts12ps",
        "profile": {
            "state_ut": "Gujarat",
            "age": 26,
            "confirmed": False
        }
    }
    res = client.post("/api/explain", json=payload)
    assert res.status_code == 400
    assert "confirmed" in res.json()["detail"].lower()


def test_explain_single_scheme_success_and_404():
    # Valid scheme with confirmed profile
    payload = {
        "slug": "aspfts12ps",
        "profile": {
            "state_ut": "Gujarat",
            "age": 26,
            "gender": "male",
            "caste_category": "sc",
            "qualification": "graduate",
            "current_sector": "it_tech",
            "annual_family_income_inr": 180000,
            "confirmed": True
        }
    }
    res = client.post("/api/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == "aspfts12ps"
    assert "explanation" in data
    assert isinstance(data["source_citations"], list)

    # 404 for nonexistent scheme
    payload["slug"] = "totally-fake-scheme-slug-12345"
    res404 = client.post("/api/explain", json=payload)
    assert res404.status_code == 404


def test_readonly_database_rejects_writes():
    from backend.app.services.db import get_db_connection
    import sqlite3
    conn = get_db_connection()

    # Invariant: PRAGMA query_only must be 1
    cur = conn.cursor()
    cur.execute("PRAGMA query_only;")
    assert cur.fetchone()[0] == 1

    # Invariant: write attempts must fail
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("INSERT INTO schemes (slug, name, level, beneficiary_states, all_states, categories, sections, application_process, source_links, content_hash, fetched_at, list_fetched_at) VALUES ('fake', 'fake', 'Central', '[]', 1, '[]', '{}', '[]', '[]', 'hash', 'now', 'now');")

    with pytest.raises(sqlite3.OperationalError):
        conn.execute("CREATE TABLE test_table (id INT);")


def test_audio_upload_bounded():
    # Oversized payload exceeding 5MB
    oversized = b"0" * (5 * 1024 * 1024 + 10)
    files = {"audio": ("test.webm", oversized, "audio/webm")}
    res = client.post("/api/profile/extract-audio", files=files)
    assert res.status_code == 413
    assert "maximum size limit" in res.json()["detail"].lower()

    # Empty payload
    empty_files = {"audio": ("empty.webm", b"", "audio/webm")}
    res_empty = client.post("/api/profile/extract-audio", files=empty_files)
    assert res_empty.status_code == 400

    # Unsupported format
    unsupported_files = {"audio": ("bad.exe", b"xyz", "application/x-msdownload")}
    res_unsupported = client.post("/api/profile/extract-audio", files=unsupported_files)
    assert res_unsupported.status_code == 415
