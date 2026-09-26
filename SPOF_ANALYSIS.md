# SPOF ANALYSIS — The Filter Applied to This Repo

*"SPOF-free" cannot mean the opponent has no failures. It means our engine has
no unpatched dependencies.* This document is the SPOF filter the repo itself
had to survive before shipping. Every single point of failure found in the
code, the knowledge base, the infrastructure, and the operation is listed with
its disposition: **FILTERED** (eliminated), **COVERED** (mitigated + named
cover), or **PRICED** (residual risk with an honest price).

## A. Epistemic SPOFs (the deepest class)

| ID | SPOF | Disposition | Mechanism |
|---|---|---|---|
| E1 | Hallucinated/unverified precedent ingested as ground truth | **FILTERED** | `CitationTrust` tiers; court docs emit CONFIRMED-only; QUARANTINED entries are structurally unreachable in `citations.emit_citations()`; quarantine list is public to the operator (`citations.quarantined_citations()`). |
| E2 | Model self-contamination (confident output born UNVERIFIED) | **FILTERED** | Confidence ∈ [0,1] attached to every SPOF and document; load-bearing threshold in config; audit trail logs every internal finding. |
| E3 | Citation shelf life (BGH VI ZR 375/24 is 10 weeks old at freeze) | **COVERED** | `reverify_after: 2027-01-27` in the registry; `reverify_due()` check surfaced in `/health` and the CLI — the date is a production calendar event, not a comment. |
| E4 | Single-source legal knowledge | **COVERED** | Statute-first architecture: every load-bearing argument survives the deletion of any case citation (statutes are the substrate, cases corroborate). |
| E5 | Facts invented by the drafting layer | **FILTERED** | Missing context renders as `[offen]`, never fabricated (`gen4._fmt`); ground truth or silence. |

## B. Code SPOFs

| ID | SPOF | Disposition | Mechanism |
|---|---|---|---|
| C1 | Cross-generation state threading (the v33 build's patch layer) | **FILTERED** | Package layout resolves it natively in the owning module (`Ragnar._last_threat` + live Verjährung threading in `ingest_incoming`); `apply_assembly_patches()` is an idempotent no-op that verifies integrity and fails loudly if the native fix is missing. |
| C2 | Omega Lock replay attack (v32.0 hole) | **FILTERED** | Nonce set survives re-engagement; same nonce never works twice (`lock.cycle_and_replay` contract); key compared timing-safe (`hmac.compare_digest`). |
| C3 | Lock silently disabled (no key) | **FILTERED** | Fail-closed: absent `RAGNAR_OMEGA_KEY` → `engage()` raises `OmegaLockError`; drafting continues, execution denied, audit logs the refusal. |
| C4 | Tripwire false positives on negations ("keine SCHUFA-Meldung") | **FILTERED** | Threat-pattern AND defensive-pattern separation with sentence-scoped negation guards (C19 fix); contract-tested. |
| C5 | Template fingerprinting → deterrence decay (I11) | **COVERED** | Polymorphic generation: citation order + section order permuted per seed; no two deployments share a fingerprint; SPOF survival rates conceptually time-decayed. |
| C6 | Monto Carlo non-determinism | **FILTERED** | Seeded, injectable RNG threaded from `RagnarConfig.seed` through causal + NPV; tests assert distributions, not noise. |
| C7 | Unreachable-branch bug class (v30) | **FILTERED** | Outcome draw is a `searchsorted` over a cumsum — branch reachability is a property of the data, not nested ternaries. |
| C8 | State aliasing / attribute typos | **FILTERED** | `frozen=True, slots=True` on all data model classes — mutation raises, typos raise. |
| C9 | Magic numbers drift | **FILTERED** | One frozen `RagnarConfig`; every constant is named, typed, tested API. |
| C10 | Python version drift (StrEnum is load-bearing) | **FILTERED** | `requires-python = ">=3.11"` enforced by packaging + CI matrix (3.11/3.12). |
| C11 | Lint/type gate rot | **FILTERED** | CI blocks on ruff check + format + mypy + pytest; the in-binary suite ships in the wheel so production can self-verify. |
| C12 | Typed-JSON boundary leaking `Any` | **COVERED** | mypy strict on the reasoning core; per-module staged overrides documented (gen4 prose carriers, tests) — the staged gate is the documented compromise, not a hidden one. |

## C. Infrastructure SPOFs

| ID | SPOF | Disposition | Mechanism |
|---|---|---|---|
| I1 | Single interface (CLI-only) | **FILTERED** | Triple redundancy: library API, CLI (`ragnar`), FastAPI service (`/decide`, `/ingest`, `/plan/{id}`, `/health`). Any one can die; the engine survives. |
| I2 | Runtime network dependency | **FILTERED** | Zero runtime network calls; numpy is the only heavy dep; engine runs fully offline. |
| I3 | Secrets in artifacts | **FILTERED** | Env-only secrets; `.env` git-ignored + docker-ignored; Docker image bakes no key; API key gate fail-closed. |
| I4 | Container as root | **FILTERED** | Dockerfile: dedicated non-root user `ragnar`, read_only rootfs (compose), no shell in entry. |
| I5 | Unbounded container resources | **FILTERED** | compose memory limits + CPU shares; engine peak RSS < 200 MB (headroom ×20 on the reference 4 GB host). |
| I6 | Broken deployment unnoticed | **FILTERED** | `/health` endpoint checks liveness AND `citation_reverify_due` (the epistemic shelf life is first-class telemetry); Docker HEALTHCHECK uses it. |
| I7 | Pinned-base drift / supply chain | **COVERED** | `python:3.12-slim` pinned by digest-ready tag scheme; pip constrained (`numpy>=1.26,<3`); reproducible installs via pyproject lock constraints. Hash-pinning the base image digest is the operator's next hardening step (named cover). |
| I8 | State loss on restart | **PRICED** | Plans are in-memory in the API by design (operator decides where state lives); CLI state machine round-trips via `save_state`/`load_state` with hash-chained audit — tested. Residual: API plans do not survive restart; priced as acceptable for a drafting engine. |
| I9 | CI as single quality gate | **COVERED** | The in-binary suite (`ragnar --test`) ships inside the wheel — production verifies itself without the repo. |
| I10 | GitHub as single host | **PRICED** | Standard residual; the local clone is the DR copy; `make archive` produces a source tarball for cold storage. |

## D. Operational SPOFs (adjoint: the operator)

| ID | SPOF | Disposition | Mechanism |
|---|---|---|---|
| O-1 | Operator files machine output unreviewed | **FILTERED (architecturally)** | LICENSE + README + docs make human lawyer review a stated precondition; documents are drafts, the engine has no filing capability. The adjoint principle applied to the operator. |
| O-2 | Operator feeds poisoned research dossiers | **COVERED** | Trust tiers quarantine unverified input; suspicion heuristics documented in the inward audit (suspicion is triage, never verdict). |
| O-3 | Opponent fingerprinting this public repo | **COVERED** | Polymorphism + the repo's own doctrine documents the arms race honestly; the signal that matters (competence) is costly to fake and decays with capture — modeled (I11). |
| O-4 | Reverify date passes unnoticed | **FILTERED** | `reverify_due()` surfaces in `/health`, README, and the registry meta; CI does not enforce it (it can't — law is not CI) but production telemetry does. |

## Residual risk register (what "SPOF-free" does not cover)

1. **The § 548 auto-abo gap (confidence 0.75).** The Mietvertrag qualification
   is argued as an analogy chain via the provider's own AGB; a court could
   rule otherwise. Mitigation: it is one of four independent gates — its
   failure degrades the plan, it does not kill it. Priced, never hidden.
2. **Opponent irrationality** (institutional inertia, sunk cost): a ~0.10
   Klage path exists despite negative EV for them. Mitigation: O1+O2 are
   court-ready from day one; J-series documents are built for that path.
3. **Doctrine capture over time**: every deployment makes the next opponent
   slightly more compliant, slightly less SPOF-ridden — success changes the
   environment. Mitigation: time-decay scoring concept + polymorphism.

## Verdict

FILTERED: 19 · COVERED: 7 · PRICED: 3 — and every PRICED item has a named
owner and a named cover. That is the only honest form of "SPOF-free".

## V. Serverless route (Vercel) — platform-specific entries

The Vercel deployment (main.py bridge → one Fluid function) adds its own
honest risk entries. The repo keeps BOTH routes: Docker/compose is the
stateful reference deployment; Vercel is the zero-ops drafting surface.
They cross-cover each other (I10 class).

| ID | SPOF | Disposition | Mechanism |
|---|---|---|---|
| V1 | Serverless statelessness — plan store & tripwire history ephemeral | **PRICED + SHAPED** | The API creates a fresh engine per request BY DESIGN (stateless decide/ingest); `/plan/{id}` is warm-instance best-effort; stateful operations are documented as Docker-route territory. The deployment shape matches the workload — the SPOF is not hidden, it is priced. |
| V2 | Cold start ≈ 2–4 s (numpy + FastAPI import) | **PRICED** | acceptable for a drafting API; Fluid compute amortizes it; `/health` liveness distinguishes cold vs warm. |
| V3 | Function bundle size ceiling (numpy ≈ 100+ MB unzipped) | **COVERED** | `.vercelignore` ships engine-only bundle (no .git/tests/docs/docker); numpy pinned `>=1.26,<3`; fallback documented: pin `numpy==1.26.4` if a future runtime exceeds the 250 MB limit. |
| V4 | Platform dependency (Vercel outage/config drift) | **COVERED** | Cross-cover with Docker/compose + bare-metal routes; the repo remains the single source of truth (`vercel deploy` builds from the same tree; no vendored copy). |
| V5 | Public URL exposure of the drafting API | **FILTERED** | `RAGNAR_API_KEY` required via `X-API-Key` (fail-closed if set — and we set it); `/health` deliberately unauthenticated liveness only (no case data, no engine internals beyond version + reverify flag). |
| V6 | Secrets leaking via bundle | **FILTERED** | `.vercelignore` excludes `.env*`; secrets live ONLY in Vercel env vars; `RAGNAR_OMEGA_KEY` never printed by any endpoint (health exposes presence, not value). |
| V7 | Public demo surface = compute-burn / abuse vector | **FILTERED** | `/demo/*` carries a per-client sliding-window throttle (30/hour) + hard input caps (field lengths, claim ceiling, correspondence count); no key ever ships to the client; demo output is a draft and is not stored. The honest residual: the throttle is instance-local on serverless — the named global cap is the platform's own rate limiting. |
| V8 | Client-side secret leak (key embedded in showcase JS) | **FILTERED** | The showcase page contains zero secrets by construction: it calls only keyless `/demo/*` + `/health`; the operator API key never touches client code. |
| V9 | Frontend SPOF class (CDN font/library outage, asset 404, build-tool drift) | **FILTERED** | `public/index.html` is one self-contained file: system fonts, inline SVG, zero external requests, zero build step — nothing the page needs can 404 or rot. Server-rendered fallback: the FastAPI `/` route serves the same page if the CDN layer is bypassed. |
