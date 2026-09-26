# THE CORRECTION MATRIX (v32.0 → v33.0)

Every error found across all versions and its disposition. The delta between
the flawed arc and the shipped engine. Three confirmed hallucination-class
errors (one mine, two dossier), four mischaracterizations, two false
fabrication-flags revoked (cases that were REAL), and the architectural
fixes. This matrix is the engine's honesty ledger — it ships with the product.

| # | Error | Found in | Status | Correction |
|---|---|---|---|---|
| C1 | BGH VIII ZR 168/24 (23.11.2024 — a Saturday) cited for Neu-für-Alt | model output | CONFIRMED HALLUCINATION (amalgam) | DELETED; Neu-für-Alt anchored to § 249 Abs. 1 BGB + 6 U 84/24's Abschlag holding |
| C2 | "§ 204 Abs. 1 Nr. 1 ZPO" | dossier | MISCITATION (§ 204 is BGB) | corrected |
| C3 | "§ 309 Nr. 7 i.V.m. § 302 BGB" for Verjährungsverlängerung | dossier | DOGMATICALLY FALSE | corrected to § 307 Abs. 1, 2 BGB + BGH VIII ZR 13/17 |
| C4 | "BGH NJW 2007, 2106" | dossier | UNVERIFIABLE | QUARANTINED; doctrine survives via § 31 Abs. 2 BDSG + VI ZR 375/24 |
| C5 | "BGH, Juli 2026" | dossier | real case, wrong date | corrected to BGH VI ZR 375/24, 12.05.2026 (upgraded holding: Widerruf + Art. 82) |
| C6 | "BGH VIII ZR 178/85" for § 548-analog | dossier/assumption | UNVERIFIED | deleted; § 548-analog argued as analogy chain |
| C7 | LG Gießen 1 S 148/21 as "richtungsweisend unwirksam" | dossier | MISCHARACTERIZED (Regelfall wirksam, B2B) | downgraded to PROBABLE corroboration; § 308 Nr. 9 carries consumers alone |
| C8 | VI ZR 300/24 cited as purely favorable | dossier | DOUBLE-EDGED (strengthens fictive billing) | O7 narrowed: claimant-specific infrastructure only |
| C9 | Kindersitzverformung detail in 6 U 84/24 | dossier | UNVERIFIED detail | dropped from load-bearing use; verified core holdings carry |
| C10 | Gebrauchsspur table cites (LG München I, OLG Düsseldorf, AG Osnabrück) | dossier | UNVERIFIED individually | dropped as unnecessary — 6 U 84/24 defines Gebrauchsspuren internally |
| C11 | FALSE FLAG: "6 U 84/24 likely fabricated" | model audit | MY ERROR — case is real, figures accurate | REVOKED; upgraded to CONFIRMED load-bearing |
| C12 | FALSE FLAG: "XII ZR 96/23 wrong senate" | model audit | MY ERROR — real, on-point | REVOKED; upgraded to CONFIRMED |
| C13 | Lagom = equilibrium | v32.0 | heuristic, not Nash | I12: Nash solver specified (LOW priority) |
| C14 | NPV independence assumption | v32.0 | path dependence ignored | I15: matrix-mask path-dependent NPV (shipped) |
| C15 | Verjährung binary | v32.0 | no interruption modeling | I7: stochastic model with § 204/212 events (shipped) |
| C16 | Victory = fold/dismiss | v32.0 | Pyrrhic wins invisible | I8: five-state model (shipped, Pyrrhic-negative) |
| C17 | Omega Lock replayable | v32.0 | security hole | I5: nonce set survives re-engagement (shipped) |
| C18 | DSUP unsanitized | v32.0 | injection surface | I6: citation format whitelist |
| C19 | Tripwire keyword matching | v32.0 | ~15% false positives | semantic threat/defense pattern separation + negation guards (shipped) |
| C20 | Scalpel Email rhetoric | uploaded email | judge-facing reactance risk | J5 channel separation: density deters, rhetoric deleted (shipped in sterilizer + specs) |
| C21 | Opponent modeled as single node | v32.0 | edge friction missed | O10 formalized (shipped) |
| C22 | No escalation velocity detection | v32.0 | cedes tempo | O11 + pre-emptive Feststellungsklage rule (shipped) |
| C23 | No uncertainty pricing anywhere | ALL versions | META-SPOF | I16: confidence on every proposition; load-bearing thresholds (shipped) |
| C24 | Draft's CLI ingest contract self-contradiction: KLAGE text expected exit 0 while the CLI documents exit 3 for cryptobiosis-breaking ingest | build draft | internal inconsistency | resolved per the CLI's own semantics: break → 3; both paths contract-tested |
| C25 | Draft test-fixture IBAN "DE89370501981234567890" fails ISO 13616 mod-97 | build draft | invalid fixture | replaced with mod-97-valid sample; the adjoint audit (I-C) now correctly passes what it was built to police |

**The meta-lesson (unchanged from the audit):** two of the flagged citations
were fabricated by the model, delivered with full confidence, and absorbed
without resistance. Zero-trust must include the operator, the operator's
sources, and the model generating the engine. Including me.
