# API contracts — the FastAPI wrapper (skipped cleanly if extra not installed).
"""The leverage layer: a CLI serves one user; an API serves the operation."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from ragnar.api import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "citation_reverify_due" in body  # the shelf life is first-class


def test_decide_and_get_plan(client: TestClient) -> None:
    threat = {"domain": "auto_abo", "opponent": "DFD", "claim": 2100.0, "basis": "§ 249 BGB"}
    r = client.post("/decide", json=threat)
    assert r.status_code == 200
    plan = r.json()
    assert plan["threat"]["opponent"] == "DFD"
    assert abs(sum(plan["victory_projection"].values()) - 1.0) < 1e-6
    r2 = client.get(f"/plan/{plan['plan_id']}")
    assert r2.status_code == 200
    assert r2.json()["plan_id"] == plan["plan_id"]


def test_decide_rejects_bad_domain(client: TestClient) -> None:
    r = client.post(
        "/decide", json={"domain": "nonsense", "opponent": "X", "claim": 1.0, "basis": "b"}
    )
    assert r.status_code == 422


def test_ingest_detects_klage(client: TestClient) -> None:
    r = client.post("/ingest", json={"text": "Hiermit wird Klage erhoben."})
    assert r.status_code == 200
    body = r.json()
    assert body["event"] is not None
    assert body["event"]["type"] == "klage"
    assert body["break_cryptobiosis"] is True


def test_ingest_neutral_text(client: TestClient) -> None:
    r = client.post("/ingest", json={"text": "Wir nehmen Kenntnis."})
    assert r.status_code == 200
    assert r.json()["event"] is None


def test_ingest_requires_text(client: TestClient) -> None:
    r = client.post("/ingest", json={"text": "   "})
    assert r.status_code == 422


def test_plan_not_found(client: TestClient) -> None:
    r = client.get("/plan/does-not-exist")
    assert r.status_code == 404
