# API — FastAPI wrapper: the leverage layer, plus the public demo surface.
"""RAGNAR Ω OMNI v33.1.0 — FastAPI wrapper.

Key-gated API (operator surface):
    POST /decide       → threat JSON in, priced Plan JSON out (stored under a plan id)
    POST /ingest       → opponent text through the tripwire monitor (with live threat context)
    GET  /plan/{id}    → retrieve a stored plan
    GET  /health       → liveness + epistemic shelf-life check (reverify date!)

Public demo surface (showcase, zero secrets in the client):
    GET  /             → static demo page (Vercel CDN serves public/index.html first;
                         this route is the local-dev fallback)
    POST /demo/decide  → the full pipeline, no key, per-client throttled + capped
    POST /demo/ingest  → the tripwire monitor, no key, same throttle

Security model:
- The engine is fail-closed: RAGNAR_OMEGA_KEY gates execution, not drafting.
- Set RAGNAR_API_KEY to require X-API-Key on every operator route.
- The demo surface never carries a key: rate limit + input caps are the cover
  (SPOF_ANALYSIS.md §V/V7–V9). Demo runs are stateless and are not persisted.
- The service never persists plans to disk — in-memory only, your audit trail
  stays where you decide it lives.

Run: uvicorn ragnar.api:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import os
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .citations import reverify_due
from .gen1_foundation import TState, threat_from_json
from .gen4_execution import Ragnar, TripwireMonitor
from .gen5_integration import plan_to_json

app = FastAPI(
    title="RAGNAR Ω OMNI",
    version=__version__,
    description="Asymmetric, zero-trust, game-theoretic legal defense engine",
)

_PLANS: dict[str, dict[str, Any]] = {}

_PUBLIC_INDEX = Path(__file__).resolve().parents[2] / "public" / "index.html"

_DEMO_RATE_LIMIT = 30
_DEMO_RATE_WINDOW = 3600.0
_DEMO_BUCKETS: defaultdict[str, deque[float]] = defaultdict(deque)
_DEMO_TEXT_CAP = 1500
_DEMO_CLAIM_MAX = 1_000_000.0
_DEMO_FIELD_CAPS: dict[str, int] = {
    "opponent": 120,
    "basis": 300,
    "contract_number": 60,
    "bank_account": 42,
    "agb_excerpt": 2000,
}
_DEMO_CORR_MAX_ITEMS = 12
_DEMO_CORR_MAX_CHARS = 1500


def _authorize(x_api_key: str | None) -> None:
    """Fail-closed API-key gate: if RAGNAR_API_KEY is set, every call must carry it."""
    expected = os.environ.get("RAGNAR_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _demo_throttle(request: Request) -> None:
    """Per-client sliding window. Instance-local by design (serverless):
    the honest global cap is the platform's own — priced in SPOF_ANALYSIS §V."""
    bucket = _DEMO_BUCKETS[_client_ip(request)]
    now = time.monotonic()
    while bucket and now - bucket[0] > _DEMO_RATE_WINDOW:
        bucket.popleft()
    if len(bucket) >= _DEMO_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"demo rate limit reached ({_DEMO_RATE_LIMIT}/hour per client) — "
            "the Tardigrade hibernates; come back shortly",
        )
    bucket.append(now)


def _demo_validate(threat: Any) -> None:
    """Input caps for the public surface: bounded compute per request."""
    for name, cap in _DEMO_FIELD_CAPS.items():
        if len(getattr(threat, name)) > cap:
            msg = f"demo cap exceeded: {name} longer than {cap} characters"
            raise HTTPException(status_code=422, detail=msg)
    if threat.claim > _DEMO_CLAIM_MAX:
        msg = f"demo cap exceeded: claim above {_DEMO_CLAIM_MAX:,.0f}"
        raise HTTPException(status_code=422, detail=msg)
    if len(threat.correspondence) > _DEMO_CORR_MAX_ITEMS:
        msg = f"demo cap exceeded: more than {_DEMO_CORR_MAX_ITEMS} correspondence items"
        raise HTTPException(status_code=422, detail=msg)
    for item in threat.correspondence:
        if len(item) > _DEMO_CORR_MAX_CHARS:
            msg = (
                f"demo cap exceeded: correspondence item longer "
                f"than {_DEMO_CORR_MAX_CHARS} characters"
            )
            raise HTTPException(status_code=422, detail=msg)


@app.get("/", include_in_schema=False)
def root() -> Response:
    """Serve the showcase page. On Vercel the CDN serves public/index.html
    before the function runs; this is the local-dev and wheel fallback."""
    if _PUBLIC_INDEX.exists():
        return FileResponse(_PUBLIC_INDEX, media_type="text/html")
    return JSONResponse(
        {
            "engine": "RAGNAR Ω OMNI",
            "version": __version__,
            "docs": "/docs",
            "endpoints": ["/health", "/decide", "/ingest", "/plan/{plan_id}"],
            "auth": "set X-API-Key (required when RAGNAR_API_KEY is configured)",
        }
    )


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


@app.post("/demo/decide")
def demo_decide(threat: dict[str, Any], request: Request) -> JSONResponse:
    """Public showcase run of the full pipeline — same engine, no key,
    throttled and capped. Output is a draft, not legal advice."""
    _demo_throttle(request)
    try:
        t = threat_from_json(threat)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"invalid threat: {e}") from e
    _demo_validate(t)
    plan = Ragnar().decide(t)
    return JSONResponse(plan_to_json(plan))


@app.post("/demo/ingest")
def demo_ingest(body: dict[str, Any], request: Request) -> dict[str, Any]:
    """Public showcase of the tripwire monitor — no key, throttled.

    Body: {"text": "..."} — negations must not fire ("keine SCHUFA-Meldung").
    """
    _demo_throttle(request)
    text = str(body.get("text", ""))
    if not text.strip() or len(text) > _DEMO_TEXT_CAP:
        msg = f"text required (max {_DEMO_TEXT_CAP} characters)"
        raise HTTPException(status_code=422, detail=msg)
    monitor = TripwireMonitor()
    ev = monitor.check(text, TState.CRYPTO)
    if ev is None:
        return {"event": None}
    return {
        "event": ev.to_json(),
        "break_cryptobiosis": monitor.should_break_cryptobiosis(ev),
    }
