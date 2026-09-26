# CHANGELOG

## 33.1.0 (2026-09-26) — Showcase: public one-page demo

The deployment became the demo: a self-contained showcase page plus two
throttled public endpoints running the real engine.

### Added
- `public/index.html` — one-page showcase (zero external assets, zero build):
  intro, four-step pipeline, live `POST /demo/decide` runner with SPOF/victory/
  document rendering, tripwire playground, doctrine, and the honest limits
  section (L1–L6). Served by the Vercel CDN; the FastAPI `/` route is the
  local-dev/wheel fallback.
- `/demo/decide` and `/demo/ingest` — public showcase surface: same engine,
  no key, per-client sliding-window throttle (30/hour), hard input caps
  (field lengths, claim ≤ 1,000,000, correspondence ≤ 12 × 1,500 chars).
- Demo contracts in the test suite: throttle, caps, negation guard, no-key
  access, no plan storage for demo runs.

### Changed
- Version 33.0.0 → 33.1.0 (API, pyproject, health).
- SPOF_ANALYSIS.md §V extended: V7–V9 (public demo surface, client-secret
  leak class, frontend SPOF class — all FILTERED).

## 33.0.0 (2026-09-26) — Ω OMNI: the self-consistent engine

Master synthesis of the v32.0 → v32.3 arc, rebuilt as a production package.

### Added
- Deduplicated SPOF universe O1–O11 with honest gates (consumer-gated,
  dispute-gated, claimant-specific, probabilistic) over a DomainProfile
  registry — one entry per domain, zero function edits to extend.
- Epistemic kernel: CitationTrust tiers, CONFIRMED-only court emission,
  structurally unreachable quarantine, reverify calendar (2027-01-27).
- Judge layer J1–J5: the third player modeled; judge_adoptability metric;
  channel separation enforced by the sterilizer.
- Adjoint self-audit (I4): the engine runs its own weapon checks against the
  operator before every maneuver (overreach, Art. 82 tariffing, mod-97 IBAN).
- Vectorized, seeded Monte Carlo; path-dependent NPV; five-state victory
  model (Pyrrhic-negative); Nash-solved Lagom doctrine; Bayesian opponent
  model with decaying dark horse; escalation velocity (D-term).
- Fail-closed Omega Lock with nonce replay protection.
- Twelve semantic tripwires with negation guards and the § 548 30-day tick.
- Eight German document builders, channel-separated, polymorphic-seeded.
- FastAPI wrapper, Docker/compose stack, CI gates, contract test suites.
- The in-binary test suite ships inside the wheel (runtime self-verification).

### Fixed (corrections C1–C25 — see docs/CORRECTION_MATRIX.md)
- One confirmed model-fabricated citation deleted (Saturday date, C1);
  two false fabrication-flags revoked (real cases restored to CONFIRMED, C11/C12);
  quarantine protocol for unverifiable entries (C4/C6/C9/C10);
  CLI ingest exit-code contract resolved (C24); test fixture IBAN made
  mod-97-valid (C25 — the adjoint audit working as designed).

### Removed
- The single-file weld artifact (build_final.py concatenation) — production
  wants boring: the package layout keeps generation boundaries importable.

### Gates at release
ruff check/format: clean · mypy strict core: clean · pytest: 87/87 ·
in-binary: 42/42.
