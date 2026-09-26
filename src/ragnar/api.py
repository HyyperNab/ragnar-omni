# API — optional FastAPI wrapper: the leverage layer (a CLI serves one user).
"""RAGNAR Ω OMNI v33.0 — FastAPI wrapper.

POST /decide       → threat JSON in, priced Plan JSON out (stored under a plan id)
POST /ingest       → opponent text through the tripwire monitor (with live threat context)
GET  /plan/{id}    → retrieve a stored plan
GET  /health       → liveness + epistemic shelf-life check (reverify date!)

Security model:
- The engine is fail-closed: RAGNAR_OMEGA_KEY gates execution, not drafting.
- Set RAGNAR_API_KEY to require X-API-Key on every route (fail-closed if set).
- The service never persists plans to disk — in-memory only, your audit trail
  stays where you decide it lives.

Run: uvicorn ragnar.api:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from . import __version__
from .citations import reverify_due
from .gen1_foundation import threat_from_json
from .gen4_execution import Ragnar
from .gen5_integration import plan_to_json

app = FastAPI(
    title="RAGNAR Ω OMNI",
    version=__version__,
    description="Asymmetric, zero-trust, game-theoretic legal defense engine",
)

_PLANS: dict[str, dict[str, Any]] = {}


def _authorize(x_api_key: str | None) -> None:
    """Fail-closed API-key gate: if RAGNAR_API_KEY is set, every call must carry it."""
    expected = os.environ.get("RAGNAR_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness + the epistemic shelf-life check (reverify is a production date)."""
    return {
        "status": "ok",
        "version": __version__,
        "citation_reverify_due": reverify_due(),
        "omega_key_present": bool(os.environ.get("RAGNAR_OMEGA_KEY")),
    }


@app.post("/decide")
def decide(threat: dict[str, Any], x_api_key: str | None = Header(default=None)) -> JSONResponse:
    """Encode a threat, run the full pipeline, return the priced plan."""
    _authorize(x_api_key)
    try:
        t = threat_from_json(threat)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"invalid threat: {e}") from e
    engine = Ragnar()
    plan = engine.decide(t)
    plan_id = uuid.uuid4().hex
    payload = plan_to_json(plan)
    payload["plan_id"] = plan_id
    _PLANS[plan_id] = payload
    return JSONResponse(payload)


@app.post("/ingest")
def ingest(body: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    """Run opponent text through the tripwire monitor.

    Body: {"text": "...", "threat": {...optional threat JSON for clock context...}}
    """
    _authorize(x_api_key)
    text = str(body.get("text", ""))
    if not text.strip():
        raise HTTPException(status_code=422, detail="text required")
    engine = Ragnar()
    if isinstance(body.get("threat"), dict):
        try:
            engine.decide(threat_from_json(body["threat"]))
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail=f"invalid threat: {e}") from e
    ev = engine.ingest_incoming(text)
    if ev is None:
        return {"event": None}
    return {
        "event": ev.to_json(),
        "break_cryptobiosis": engine.monitor.should_break_cryptobiosis(ev),
    }


@app.get("/plan/{plan_id}")
def get_plan(plan_id: str, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    """Retrieve a stored plan (in-memory only — restart clears the store)."""
    _authorize(x_api_key)
    if plan_id not in _PLANS:
        raise HTTPException(status_code=404, detail="plan not found")
    return _PLANS[plan_id]
