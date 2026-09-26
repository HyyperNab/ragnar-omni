# API contracts — FastAPI wrapper, operator routes, and the public demo surface.
"""The leverage layer: a CLI serves one user; an API serves the operation;
the demo surface serves the showcase — same engine, honest limits."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import ragnar.api as api_module  # noqa: E402
from ragnar.api import app  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_demo_buckets() -> None:
    api_module._DEMO_BUCKETS.clear()  # module state must never leak between tests
    yield
    api_module._DEMO_BUCKETS.clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


_THREAT = {"domain": "auto_abo", "opponent": "DFD", "claim": 2100.0, "basis": "§ 249 BGB"}


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "citation_reverify_due" in body  # the shelf life is first-class


def test_root_serves_showcase_page(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "RAGNAR" in r.text
    assert "demo/decide" in r.text  # the page talks to the live endpoints
    assert "not legal advice" in r.text.lower() or "Not legal advice" in r.text


def test_decide_and_get_plan(client: TestClient) -> None:
    r = client.post("/decide", json=_THREAT)
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


# --------------------------------------------------------------------------- #
# Public demo surface — no key, throttled, capped
# --------------------------------------------------------------------------- #


def test_demo_decide_runs_full_pipeline_without_key(client: TestClient) -> None:
    r = client.post(
        "/demo/decide",
        json={
            "domain": "auto_abo",
            "opponent": "Muster-Abo GmbH",
            "claim": 3160.0,
            "basis": "Minderwert aus Reparaturkostensumme",
            "verjaehrung_date": "2026-12-25",
            "correspondence": [
                "Mahnung 1",
                "Mahnung 2",
                "Mahnung 3: Umsatzsteuer 19% auf fiktive Kosten",
            ],
        },
    )
    assert r.status_code == 200
    plan = r.json()
    assert plan["maneuver"]["id"]
    assert plan["spofs"]
    assert abs(sum(plan["victory_projection"].values()) - 1.0) < 1e-6
    assert plan["documents"]
    assert "plan_id" not in plan  # demo runs are not stored


def test_demo_decide_rejects_unknown_domain(client: TestClient) -> None:
    r = client.post(
        "/demo/decide", json={"domain": "warp", "opponent": "X", "claim": 1.0, "basis": "b"}
    )
    assert r.status_code == 422


def test_demo_decide_enforces_field_caps(client: TestClient) -> None:
    r = client.post(
        "/demo/decide",
        json={
            "domain": "auto_abo",
            "opponent": "X" * 500,
            "claim": 10.0,
            "basis": "b",
        },
    )
    assert r.status_code == 422
    assert "opponent" in r.json()["detail"]


def test_demo_decide_enforces_claim_cap(client: TestClient) -> None:
    r = client.post(
        "/demo/decide",
        json={
            "domain": "auto_abo",
            "opponent": "X",
            "claim": 10_000_000.0,
            "basis": "b",
        },
    )
    assert r.status_code == 422
    assert "claim" in r.json()["detail"]


def test_demo_rate_limit_throttles(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_module, "_DEMO_RATE_LIMIT", 2)
    threat = {"domain": "auto_abo", "opponent": "X", "claim": 10.0, "basis": "b"}
    assert client.post("/demo/decide", json=threat).status_code == 200
    assert client.post("/demo/decide", json=threat).status_code == 200
    assert client.post("/demo/decide", json=threat).status_code == 429  # hibernation


def test_demo_ingest_fires_and_negation_guard(client: TestClient) -> None:
    r = client.post("/demo/ingest", json={"text": "Klage wird erhoben."})
    assert r.status_code == 200
    ev = r.json()["event"]
    assert ev is not None and ev["type"] == "klage"
    r2 = client.post("/demo/ingest", json={"text": "Wir bestätigen: keine SCHUFA-Meldung erfolgt."})
    assert r2.status_code == 200
    assert r2.json()["event"] is None  # C19: negations never fire


def test_demo_ingest_caps_text(client: TestClient) -> None:
    r = client.post("/demo/ingest", json={"text": "x" * 2000})
    assert r.status_code == 422


def test_demo_ingest_requires_text(client: TestClient) -> None:
    r = client.post("/demo/ingest", json={"text": "  "})
    assert r.status_code == 422
