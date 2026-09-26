# EPISTEMOLOGY — The Citation Trust Protocol

## The rule

**The STATUTE carries the weight. Cases corroborate. Never invert this.**

Structure of every load-bearing argument:

```
statute (CONFIRMED, safe)
  → doctrine (derivable from statute, safe)
  → case citation (optional, trust-tagged, quarantined if < PROBABLE)
```

## The tiers

| Tier | Value | Meaning | Emittable? |
|---|---|---|---|
| CONFIRMED | 4 | statutes; multi-source/primary-source verified landmarks | everywhere (court floor) |
| PROBABLE | 3 | format/doctrine consistent, single-source | letters (außergerichtlich) |
| UNVERIFIED | 2 | generated in-session, not cross-checked | never |
| SUSPECT | 1 | fabrication markers: weekend dates, wrong senate, hyper-specific narratives, future dates | never |
| QUARANTINED | 0 | superseded, deleted, or kept as audit evidence | **never** — structurally unreachable |

## Why this exists (the discovery)

RAGNAR's legal knowledge base was enriched from a research dossier. An audit
against fabrication markers found: one citation dated to a **Saturday**
(BGH does not verkünden on Saturdays), one with the **wrong senate**
(XII. Zivilsenat is Familiensachen; § 548 BGB is VIII. Zivilsenat territory),
one **future-dated**, and one hyper-specific narrative bearing all the
generation signatures of LLM confabulation — plus **two citations the model
had fabricated itself** in an earlier session and delivered with full
confidence. The engine had applied zero-trust to the opponent for 32 versions
and none to its own supply chain.

Consequences of the unfiltered state (why this is the deepest SPOF):
- instant credibility collapse ("Die Beklagtenseite beruft sich auf eine
  nicht existierende Entscheidung"), contaminating even the sound arguments;
- § 138 ZPO Wahrheitspflicht exposure for whoever files it (the German
  Mata v. Avianca);
- deterrence logic inverts: a discovered fake citation signals incompetence,
  and the signal cannot be un-sent.

## The three concrete repairs

1. **SCHUFA defense re-anchored to § 31 Abs. 2 BDSG** — the statute itself
   bars reporting bestrittene Forderungen; the case law becomes optional
   corroboration. Unfalsifiable by citation attack.
2. **Minderwert ≠ Reparaturkostensumme rebuilt from statute alone** where
   needed: § 249 Abs. 1 BGB (Bereicherungsverbot) + § 254 (Wirtschaftlichkeit)
   + § 286 ZPO (Darlegungslast) — weaker than verified precedent but
   unattackable. The verified OLG Stuttgart 6 U 84/24 carries the primary
   channel anyway (false fabrication-flag revoked).
3. **Quarantine protocol**: NJW 2007, 2106; VIII ZR 178/85; VIII ZR 168/24
   (the Saturday hallucination — kept in the registry as model-error
   evidence); the Kindersitz detail; the old Gebrauchsspur table cites.
   All listed in `CITATIONS_VERIFIED.json → quarantine`, visible to the
   operator via `citations.quarantined_citations()`, reachable by NO
   document builder.

## Heterogeneous redundancy (error-correcting codes, formalized)

Statute + doctrine + case is triple-modular redundancy across heterogeneous
channels. Heterogeneity matters: if all three derive from the same poisoned
dossier, failures correlate and the redundancy is fake. **Every load-bearing
proposition needs at least one CONFIRMED channel source-independent of the
others.**

## Governance

- Registry: `src/ragnar/data/CITATIONS_VERIFIED.json` — packaged with the
  wheel, single source of truth.
- Shelf life: `reverify_after: 2027-01-27` — surfaced by `/health` and the
  citations API. Production treats it as a calendar obligation.
- The audit trail: every confidence score, every quarantined citation, every
  gate condition is logged hash-chained. The trail is the evidence that the
  engine distrusts itself — which is the final SPOF patch.
