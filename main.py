# VERCEL ENTRYPOINT — FastAPI instance named `app` (Vercel detection contract).
"""Vercel entrypoint: expose the FastAPI instance named `app`.

Vercel detects `main.py` at the repository root as a supported FastAPI
entrypoint and mounts `ragnar.api:app` as ONE serverless function (Fluid
compute keeps instances warm between requests).

The sys.path bridge keeps the src/ layout intact — the package is never
copied or vendored. Single source of truth, no drift SPOF. The packaged
data files (CITATIONS_VERIFIED.json) ride along inside src/ragnar/data/
and are read via importlib.resources, exactly as in the wheel.

Serverless honesty (see SPOF_ANALYSIS.md §C/V): this deployment is
STATELESS — decide/ingest create a fresh engine per request by design;
GET /plan/{id} works within a warm instance only. Stateful operations
(ingest history, tripwire state machine) belong on the Docker/compose
route. The Omega Lock arms only if RAGNAR_OMEGA_KEY is set in the Vercel
project env — absent key, execution is denied, drafting works (fail-closed
by design).
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from ragnar.api import app  # noqa: E402,F401 — the name Vercel binds to
