"""End-to-end API tests using FastAPI's TestClient. No live database or
Qdrant instance is required: every data-source tool degrades to an
"unreachable"/"error" string when it can't connect (see ADR-0001), which
is exactly what a demo-mode deployment with no configured databases looks
like -- these tests exercise that exact path.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import rate_limit
from app.main import app


@pytest.fixture()
def client():
    rate_limit.reset_all()
    with TestClient(app) as c:
        yield c
    rate_limit.reset_all()


def test_root_serves_the_landing_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SupportGraph" in response.text


def test_health_reports_demo_mode(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True
    assert body["llm_provider"] == "mock"


def test_ask_rejects_empty_question(client):
    response = client.post("/api/ask", json={"question": ""})

    assert response.status_code == 422


def test_ask_rejects_non_positive_customer_id(client):
    response = client.post("/api/ask", json={"question": "hi", "customer_id": 0})

    assert response.status_code == 422


def test_ask_returns_an_answer_in_demo_mode(client):
    response = client.post("/api/ask", json={"question": "What is your return policy?"})

    assert response.status_code == 200
    body = response.json()
    assert body["demo_mode"] is True
    assert isinstance(body["answer"], str) and body["answer"]
    assert "rag" in body["routes"]


def test_ask_is_rate_limited_after_too_many_requests(client):
    for _ in range(rate_limit.DEFAULT_MAX_REQUESTS):
        response = client.post("/api/ask", json={"question": "What is your return policy?"})
        assert response.status_code == 200

    response = client.post("/api/ask", json={"question": "What is your return policy?"})

    assert response.status_code == 429
    assert "Retry-After" in response.headers
