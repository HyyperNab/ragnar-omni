# THE AUTO-ABO MATRIX — Forensic Deconstruction (domain module AUTO_ABO)

*Condensed from the reverse-engineering pass; the SPOF engine encodes these
findings as the O-series with the AUTO_ABO `DomainProfile`.*

## Layer 0 — The economic proof (objective, arithmetical, undisputable)

| Cost component | Monthly equivalent (3-year horizon) |
|---|---|
| Purchase price (€25,000–35,000, amortized 36 months) | €694–972 |
| Financing (5–7% p.a.) | €104–146 |
| Depreciation (28–35% year 1, 15% year 2) | €550–700 |
| Vollkasko (SF 0–2) | €120–180 |
| KfZ-Steuern | €20–40 |
| Wartung (2× Inspektion + Verschleiß) | €60–100 |
| Zulassung/Überführung | €15–25 |
| **Cost floor** | **€1,563–2,163** |

Market rate (Faaren Group Auto-Abo Report 2024/2025): **€563 average**,
Abo-Faktor 1.07% — in the exact segments advertised below €300.

**Structural deficit: ≥ €1,000/month/vehicle.** For a 12-month contract the
operator loses ~€12,000 per vehicle on the subscription itself. The only
recovery mechanism is the return invoice: inflated Minderwert, fictive
repair costs at manufacturer UVP, missing Neu-für-Alt, phantom UPE/Verbringung,
atomized Selbstbeteiligung, illegal USt on fictive amounts.

**This is not a choice — it is arithmetic.** Without the six mechanisms the
operator goes bankrupt; with them they extract €2,000–8,000 per return.
The illegality is structurally deterministic (O9, heuristic tier: sets
opponent priors, never load-bearing in court).

## Layer 1 — The legal qualification SPOF

The provider's own AGB calls it a **Mietvertrag** (Ziffer 1.1) — a
self-inflicted wound. Mietvertrag → §§ 535 ff. BGB → **§ 548 Abs. 1 BGB**:
six months from return, no AGB extension survives § 307 BGB
(BGH VIII ZR 13/17). Operational consequence: no Mahnbescheid/Klage within
six months → the claim is dead. *(Auto-abo application argued as analogy
chain — honestly priced at 0.75, the O4 gate.)*

## Layer 2 — The calculation methodology SPOF

OLG Stuttgart 6 U 84/24 (28.10.2025, verified): claim €9,445 → LG €8,000 →
OLG **€4,160**. Holdings: Minderwert ≠ Summe der Reparaturkosten; Abschlag
per Alter/Laufleistung mandatory; only damage beyond usual Gebrauchsspuren.
**The methodology itself is the SPOF — you don't fight line items, you fight
the framework.** Plus: Neu-für-Alt zwingend (§ 249 Abs. 1 BGB), no USt on
fictive amounts (§ 249 Abs. 2 S. 2 BGB; BGH VIII ZR 260/10), no phantom
logistics when the operator runs own workshops (BGH VI ZR 300/24, narrowed).

## Layer 3 — The Selbstbeteiligung atomization SPOF

N minor damages → N "Schadensereignisse" → N × €1,000 SB, functionally
emptying the paid-for Vollkasko. § 242 (treuwidrig), § 307 Abs. 1 (the
all-inclusive promise emptied in fine print), § 305c (surprise conditions).
Detection tripwire: ≥ 3 "Selbstbeteiligung" positions on one return invoice
→ one argument, all N positions eliminated (subsumed into O2).

## Layer 4 — The consumer isolation SPOF

AGB Abtretungsverbote are **nichtig** (§ 308 Nr. 9 lit. a BGB, since
01.10.2021); pre-2021 via § 307. BGH VIII ZR 285/18 (Lexfox): Legal-Tech
Inkasso on Erfolgshonorar is a valid Rechtsdienstleistung. SCHUFA threats
on bestrittene Forderungen: unlawful (§ 31 Abs. 2 BDSG; BGH VI ZR 375/24 —
bestrittene Forderung ist keine belastbare Bonitätsinformation; Widerruf +
Art. 82 exposure).

## Layer 5 — Gebrauchsspur vs. Schaden

§ 538 BGB: ordinary wear is fully amortized by the monthly rate; the burden
of proof for "übermäßige Abnutzung" lies with the Vermieter, position by
position. (The specific older AG/LG cites were dropped as unverified —
6 U 84/24 defines the boundary internally. Correction C10.)

## The interlock

A claim computed the way 6 U 84/24 forbids is **nicht plausibel dargelegt** —
and a nicht plausibel dargelegte Forderung may not be transmitted to SCHUFA
regardless of dispute (VI ZR 375/24). The methodology defect kills the
lawsuit AND the data-edge threat with one verified flaw.

## The courtroom sequence (J-series optimized)

1. Economic context (2 min, market data as context, not Vorwurf)
2. Legal qualification (1 min, their own AGB)
3. Verjährungseinrede (30 s, if applicable)
4. Methodology destruction (3 min, 6 U 84/24 + the SPOF checklist)
5. Systemic pattern (2 min, sachlich — never rhetoric; the judge adopts
   structure, not adjectives)

Every step maps to a shipped document builder; every sentence in those
builders rides CONFIRMED-tier law.
