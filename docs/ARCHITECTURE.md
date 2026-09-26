# ARCHITECTURE

## Layer contract

Five generations, each a real dependency layer. The build protocol (Lagom)
wrote contract tests before each module; the package layout keeps those
boundaries explicit and lintable:

```
config.py            ← constants only (imports nothing from the engine)
citations.py         ← epistemic kernel (imports config)
gen1_foundation.py   ← types, enums, serde, audit (stdlib only)
gen2_analysis.py     ← SPOF engine, sterilizer, DSUP, Tardigrade (gen1 + citations)
gen3_strategy.py     ← causal, NPV, Verjährung, Nash, opponent model (gen1 + numpy)
gen4_execution.py    ← builders, tripwires, lock, orchestrator (gen1–gen3)
gen5_integration.py  ← serde, CLI, in-binary suite (gen1–gen4)
api.py              ← FastAPI wrapper (gen4 + gen5; optional extra)
```

Rule: a layer imports only downward. Violations are CI-visible (ruff I001 +
the import contract is reviewable in one pass).

## The decide() pipeline (gen4.Ragnar.decide)

1. **Encode** the threat; append INGEST to the hash-chained audit.
2. **SPOF constellation**: `analyze_spofs_universal()` — the deduplicated
   O-series with honest gates (O3 needs dispute volume, O6 needs consumer +
   AGB, O7 needs claimant logistics evidence, O11 needs dated tripwire
   history). Output sorted by severity: firing order = attack order.
3. **DSUP shield**: CONFIRMED-law coverage of the fired constellation →
   score ∈ [0,1] (empty constellation scores an honest 0.5).
4. **Velocity probe** (O11): shrinking dunning intervals → tempo policy.
5. **Nash-Lagom**: 2×2 zero-sum (aggressive/patient vs escalate/fold) with
   the clock value (crypto_viability) as the patience bonus — the ZHUGE
   condition is derived from the payoff matrix, not folklore.
6. **Maneuver selection**: path-dependent NPV (vectorized, seeded) + doctrine
   affinity. Registry-locked ids (maneuver id == causal profile id).
7. **Adjoint self-audit** (I4): overreach without evidence, Art. 82 tariffing,
   own-data hygiene (mod-97) — findings priced into plan confidence.
8. **Documents**: channel-separated builders → trust-gated citations →
   sterilizer (clean text passes verbatim; dirty text loses only rhetoric)
   → sha256 fingerprint.
9. **Tardigrade phase**: threat level + tripwire signal → ACTIVE/TUN/CRYPTO.
10. **Omega Lock**: fail-closed engage under break conditions; absence of
    RAGNAR_OMEGA_KEY denies execution and logs it (drafting continues).
11. **Victory projection**: causal draw + interaction adjustment
    (irrational opponents sue past EV) → five states, Pyrrhic-negative.
12. **Plan** assembled with audit root; every step hash-chained.

## Design decisions worth knowing

- **Why numpy, honestly**: import cost (~150 ms) exceeds the unoptimized
  compute (~20 ms). It is paid for DETERMINISM (seeded, injectable RNG) and
  for making the outcome draw a `searchsorted` over a cumsum — the v30
  unreachable-branch bug class dies as a property of the data layout.
- **Why the registry (R1)**: all domain knowledge lives as data
  (`DomainProfile`); the 11 SPOF tests are generic logic. Adding a domain =
  one registry entry, zero function edits. The maintenance SPOF that the
  first plan silently reintroduced is structurally dead.
- **Why documents render `[offen]`**: the drafting layer never invents
  facts. Ground truth or silence.
- **Why the sterilizer early-exits on clean text**: sentence surgery is only
  ever performed on dirty text; clean legal prose passes byte-identical
  (paragraph breaks, "Abs. 2" numbering survive).
- **Why `verjaehrung_date` means EXPIRY**: one semantic everywhere
  (`statute_expired`, `calculate_verjaehrung`, `crypto_viability`). The clock
  anchor is `rueckgabe_date`; if only the anchor is known, the model derives
  expiry = anchor + 6 months (§ 548 Abs. 1 BGB) and extends it through
  § 204 Hemmung / § 212 Neubeginn events.

## History note

The v33 build protocol assembled a single-file `ragnar.py` via regex welding
(`build_final.py`). Production rejects that artifact — "production wants
boring" — the package layout keeps the five generations as importable,
lintable modules and resolves the two Gen-4 integration flags natively
(documented in `gen5_integration.apply_assembly_patches`, which verifies the
native fix and fails loudly if it is absent).
