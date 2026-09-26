# RAGNAR Ω OMNI v33.1

**Asymmetric · zero-trust · game-theoretic legal-defense engine.**

> The business model IS the SPOF. The monthly rates cannot cover costs — that is
> arithmetically provable — therefore the opponent *must* extract at contract end
> to survive. This structural necessity forces them to commit the exact same
> legal errors every single time, with deterministic predictability.
> **You don't need to find the SPOF — the SPOF finds you.**

RAGNAR ingests a legal threat (e.g. an auto-abo damage claim), runs a
deduplicated constellation of 11 opponent-facing SPOF weapons (O1–O11) over a
verified citation bedrock, models the opponent as a Bayesian graph (principal +
agent + data edge), prices every proposition with honest confidence, and emits
channel-separated, judge-adoptable German legal documents — then goes silent
and lets the § 548 BGB clock do the killing.

```
threat JSON ──► SPOF engine ──► DSUP shield ──► Nash-Lagom doctrine
                                   │
                                   ▼
        Plan ◄── documents (trust-gated, sterilized, polymorphic)
          │
          ├─► Tardigrade state machine (7 phases, CRYPTO = glass)
          ├─► Omega Lock (fail-closed, nonce-protected)
          └─► hash-chained audit trail (the engine distrusts itself)
```

---

## Why this exists

Consumer-facing extraction industries (auto-abo, leasing returns, debt
collection) win through **asymmetry**: templated claims vs. unadvised
consumers. RAGNAR collapses the gradient — it industrializes the defense side
with the same templating economics the offense uses, on top of law that is
**verified** (statutes carry the weight; cases corroborate; everything else is
quarantined).

The core insight from the v32.2 inward audit: *the deepest SPOF was never in
the opponent's case — it was in the epistemic supply chain.* A legal engine
that zero-trusts the opponent but trusts its own training data will cite
nonexistent precedent in front of a judge and lose everything in one sentence.
v33.0 is the version where zero-trust points inward: every citation ships with
a trust tier, quarantined entries are structurally unemittable, and the engine
prices its own uncertainty on every output.

## Feature matrix

| Layer | What it does |
|---|---|
| **SPOF engine (O1–O11)** | Deduplicated, domain-agnostic weapon set: evidentiary root, calculation methodology, processing-block accrual, temporal decay (§ 548 clock), tax phantoms, void AGB isolation, logistics phantoms, systemic regulatory, business-model dependency, network edge friction, escalation velocity. Gated honestly (consumer-gated, dispute-gated, claimant-specific). |
| **Epistemic kernel** | `CitationTrust` tiers (CONFIRMED/PROBABLE/UNVERIFIED/SUSPECT/QUARANTINED). Court documents emit CONFIRMED-only; quarantined citations are unreachable by construction. Registry reverify date is a production calendar event. |
| **Judge layer (J1–J5)** | The third player modeled: case-load pressure, anchoring, Gütewang, pattern-matching, reactance. `judge_adoptability` scores every document on the only fitness metric that matters: *can the judge plagiarize it?* |
| **Adjoint self-audit (I4)** | The SPOF engine runs against ourselves before every maneuver. A weapon you cannot survive is not a weapon. |
| **Strategy core** | Vectorized Monte Carlo (deterministic, seeded), path-dependent NPV, five-state victory model (Pyrrhic wins score negative), Nash-solved Lagom doctrine selection, Bayesian opponent model with decaying dark-horse mass. |
| **Tardigrade states** | Seven phases. CRYPTO is the glass phase: minimum energy, structural integrity, zero metabolic cost — thermodynamically optimal when a short clock runs in your favor. |
| **Omega Lock** | Fail-closed commitment device: absent `RAGNAR_OMEGA_KEY`, it refuses to engage. Nonce replay protection, timing-safe key comparison. |
| **Documents (8 builders)** | Channel-separated German legal drafts: statute-first, rhetoric-free (sterilizer enforces it), trust-gated citations, polymorphic-seeded so no two deployments share a fingerprint. |
| **Tripwires (12)** | Semantic incoming-mail monitor with negation guards ("keine SCHUFA-Meldung" never fires) and the § 548 30-day tick. |

## Quickstart

```bash
# Python ≥ 3.11 required (StrEnum is load-bearing)
pip install -e ".[dev,api]"

# The gate — all four must pass before anything ships
ruff check src tests && mypy src && pytest -q && ragnar --test
```

Run a case (stdin in, priced plan out):

```bash
echo '{
  "domain": "auto_abo",
  "opponent": "Muster-Abo GmbH",
  "claim": 3160.0,
  "basis": "Minderwert aus Reparaturkostensumme",
  "verjaehrung_date": "2026-12-25",
  "rueckgabe_date": "2026-06-25",
  "agb_excerpt": "Forderungen duerfen nur nach vorheriger Zustimmung abgetreten werden",
  "correspondence": ["Mahnung 1", "Mahnung 2", "Mahnung 3 mit USt 19%"]
}' | ragnar --stdin --pretty
```

Sample output (truncated):

```json
{
  "maneuver": {"id": "SILENCE", "doctrine": "zhuge"},
  "tstate": "crypto",
  "spofs": [
    {"code": "EVIDENTIARY_ROOT",        "severity": 5, "confidence": 0.95},
    {"code": "CALCULATION_METHODOLOGY", "severity": 5, "confidence": 0.90},
    {"code": "PROCESSING_BLOCK_ACCRUAL","severity": 5, "confidence": 0.90},
    {"code": "TEMPORAL_DECAY",          "severity": 4, "confidence": 0.75},
    ...
  ],
  "dsup_score": 0.9146,
  "confidence": 0.9378,
  "victory_projection": {"total": 0.168, "stalemate": 0.806, ...}
}
```

Ingest opponent mail through the tripwire monitor (exit code 3 = a
cryptobiosis-breaking event fired — script-friendly):

```bash
ragnar --input case.json --ingest "Hiermit wird Klage erhoben."   # → exit 3
```

### API (the leverage layer)

```bash
pip install -e ".[api]"
export RAGNAR_OMEGA_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
uvicorn ragnar.api:app --host 127.0.0.1 --port 8000

curl -s localhost:8000/health
# {"status": "ok", "citation_reverify_due": false, ...}
```

`POST /decide`, `POST /ingest`, `GET /plan/{id}` — see `src/ragnar/api.py`.
Set `RAGNAR_API_KEY` to require `X-API-Key` on every route (fail-closed).

### Showcase demo (public, self-contained)

The deployment serves a one-page showcase at `/` — no frameworks, no external
assets, zero build step (`public/index.html`, CDN-served): what the engine
does, how it works, its hard limits, and a **live demo** running the real
pipeline through two throttled public endpoints:

- `POST /demo/decide` — the full pipeline, no key, 30 runs/hour/client, input-capped
- `POST /demo/ingest` — the tripwire monitor with its negation guards

No secret ever reaches the client (SPOF_ANALYSIS.md §V/V8); demo runs are
stateless and nothing is stored.

### Docker / compose

```bash
cp .env.example .env          # set a real 32+ byte RAGNAR_OMEGA_KEY
docker compose up --build -d
docker compose logs -f api
```

Non-root container, pinned base image, healthcheck, memory limits, read-only
root filesystem — see `docs/DEPLOYMENT.md`.

## Configuration

Everything tunable lives in one frozen dataclass — `src/ragnar/config.py`
(`RagnarConfig`). The Lagom constants are API, not folklore:

| Key | Default | Meaning |
|---|---|---|
| `seed` | 0 | Deterministic engine: seeded RNG threads through causal + NPV |
| `mc_iterations` | 5000 | Monte Carlo depth |
| `o3_min_events` | 3 | Processing-block SPOF gate: dispute must be underway |
| `verjaehrung_months` | 6 | § 548 Abs. 1 BGB |
| `verjaehrung_tick_days` | 30 | Tripwire: clock nearing expiry |
| `defense_cost_ceiling` | 800 | Pyrrhic check: paths above this re-score sub-Lagom |
| `citation_floor_court` | 4 (CONFIRMED) | Court documents emit verified law only |
| `break_conditions` | KLAGE, SCHUFA, VERJAERHRUNG_TICK, SETTLEMENT_OFFER | What wakes the Tardigrade |

Secrets (environment only, never files, never flags):

| Env | Purpose |
|---|---|
| `RAGNAR_OMEGA_KEY` | Arms the Omega Lock. Absent → execution denied (fail-closed). Drafting continues. |
| `RAGNAR_API_KEY` | If set, API requires `X-API-Key` on every route. |

## Repository layout

```
RAGNAR/
├── src/ragnar/
│   ├── config.py            # frozen RagnarConfig — every constant is API
│   ├── citations.py         # trust tiers, emission gates, reverify calendar
│   ├── data/CITATIONS_VERIFIED.json   # THE legal bedrock (reverify 2027-01-27)
│   ├── gen1_foundation.py   # types, enums, threat serde, hash-chained audit
│   ├── gen2_analysis.py     # O1–O11 SPOF engine, sterilizer, DSUP, Tardigrade
│   ├── gen3_strategy.py     # causal graphs, NPV, Verjährung, Nash, opponent model
│   ├── gen4_execution.py    # 8 builders, tripwires, Omega Lock, orchestrator
│   ├── gen5_integration.py # serde, CLI, in-binary test suite
│   └── api.py               # FastAPI wrapper (optional extra)
├── tests/                   # contract tests per generation (Lagom protocol)
├── docs/                    # architecture, SPOF universe, corrections, deployment
│   └── source/Ragnar_draft.txt   # the raw build conversation, preserved verbatim
├── data/examples/           # ready-to-run threat JSON
├── Dockerfile / docker-compose.yml / Makefile / .github/workflows/ci.yml
└── SPOF_ANALYSIS.md         # the SPOF filter applied to this repo itself
```

## Testing & gates

```bash
make ci        # ruff check + format check + mypy + pytest + in-binary suite
```

The test suite is contract-first (the Lagom build protocol): every generation
has a contract file that pinned its API before the module existed. The
in-binary suite (`ragnar --test`) ships *inside the wheel* — production can
verify itself at runtime, no repo required.

## The SPOF filter

"SPOF-free" cannot mean the opponent has no failures — the world is not like
that. It means **our engine has no unpatched dependencies**: every weapon rests
on CONFIRMED law, every claim carries an uncertainty price, every blind spot
has a named cover. The repo's own single points of failure are catalogued and
filtered in **[SPOF_ANALYSIS.md](SPOF_ANALYSIS.md)**.

## Legal notice

Not legal advice. Not a lawyer. Every COURT_FACING document requires human
lawyer review before it touches a court (this is an architectural feature —
the adjoint principle applied to the operator). The citation registry has a
shelf life; reverify after **2027-01-27**. Full terms in `LICENSE`.

## Lineage

Built from the v32.0 → v33.0 arc: outward SPOF doctrine → the inward audit
(8 dimensions, epistemology to category theory) → the master synthesis
(23 corrections, 16 internal patches, 9 verified load-bearing citations) →
the engineering pass (vectorized, registry-driven, lint-gated) → this
production package. The full conversation is preserved at
`docs/source/Ragnar_draft.txt`.

*The Tardigrade still hibernates. Lagom still balances. The Omega Lock still holds.*
