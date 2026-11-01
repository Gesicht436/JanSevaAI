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
