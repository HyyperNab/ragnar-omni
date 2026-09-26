# CONTRIBUTING

The build protocol is **Lagom**: contract tests first, frozen interfaces,
gates between layers. Nothing lands on a broken foundation.

## Rules of the house

1. **Contract first.** Every module change ships with its contract test
   written before the implementation (tests/test_genN_contracts.py). The
   in-binary suite (gen5 `_CASES`) grows one row per new invariant.
2. **The statute carries the weight.** No new citation enters the registry
   without a tier and a source. Nothing below PROBABLE is ever emittable —
   if you need it in court, verify it first.
3. **Price your confidence.** Every new SPOF, document, or maneuver ships
   with a confidence in [0,1]. The engine must be able to say "arguable,
   not settled" and act accordingly.
4. **Fail loud.** Unknown domain → ValueError. Unknown causal profile →
   KeyError. Missing lock key → OmegaLockError. Silence hides failure;
   failure must not be silent.
5. **German prose is the product.** Code style is enforced (ruff, 100 cols);
   prose is exempt per-file but must survive the sterilizer with
   spof_risk < 0.1 and zero rhetoric.
6. **Run the gate before you commit:**

   ```bash
   make ci    # ruff check + format + mypy + pytest + in-binary suite
   ```

7. **Human checkpoint is not optional.** Anything that drafts court-facing
   documents keeps the "lawyer reviews before filing" invariant — PRs that
   automate filing will be rejected on architectural principle.

## SPOF discipline

Before proposing a feature, check it against docs/SPOF_ANALYSIS.md: does it
introduce a single point of failure, or patch one? New SPOFs need a named
cover in the analysis before they ship.
