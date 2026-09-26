# GEN 2 — ANALYSIS: SPOF engine, DSUP shield, sterilization, Tardigrade selection.
"""RAGNAR Ω OMNI v33.0 — Gen 2: Analysis.

The deduplicated SPOF universe O1–O11 (v33.0 Part 1) as generic, domain-agnostic
logic reading a DomainProfile registry — all domain data lives as data (R1 fix:
adding a domain is one registry entry, zero function edits; the maintenance SPOF
my first plan silently reintroduced is dead).

Also owns: rhetoric sterilization (channel separation enforcement, J5/C20),
the DSUP defensive-superiority shield, and Tardigrade state selection.

Layer contract: imports gen1 + config + citations. Never gen3/gen4.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import pairwise

from .citations import citation_confidence, emit_citations
from .config import RagnarConfig, default_cfg
from .gen1_foundation import (
    SPOF,
    Channel,
    Document,
    Domain,
    Severity,
    Threat,
    TState,
)

__all__ = [
    "DOMAINS",
    "DSUPResult",
    "DomainProfile",
    "analyze_spofs_universal",
    "crypto_viability",
    "detect_violations",
    "dsup_shield",
    "recursive_sterilize",
    "select_tardigrade",
]


# --------------------------------------------------------------------------- #
# Domain registry — one entry per functor target (v32.2 Dimension 8)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DomainProfile:
    """All domain knowledge as data. The 11 SPOF tests are generic logic."""

    domain: Domain
    method_flaw: str
    method_correct: str
    method_citation: str
    regulatory_body: str
    regulatory_law: str
    verjaehrung_basis: str
    confidence_floor: float
    has_own_logistics: bool = False
    deficit_heuristic: bool = False
    jurisdiction_warning: str = ""


_GENERIC_METHOD_FLAW = "Aufsummierung fiktiver Einzelposten ohne belastbare Gesamtberechnung"

DOMAINS: dict[Domain, DomainProfile] = {
    Domain.AUTO_ABO: DomainProfile(
        domain=Domain.AUTO_ABO,
        method_flaw="Aufsummierung fiktiver Reparaturkosten ohne Minderwertberechnung, "
        "ohne Neu-für-Alt-Abzug, mit Phantompositionen",
        method_correct="Marktüblicher Minderwert mit zwingendem Neu-für-Alt-Abzug; "
        "nur Schäden über übliche Gebrauchsspuren hinaus (§ 538 BGB)",
        method_citation="OLG Stuttgart, Urt. v. 28.10.2025 – 6 U 84/24; § 249 Abs. 1 BGB",
        regulatory_body="Verbraucherzentrale Bundesverband / qualifizierte Einrichtung",
        regulatory_law="§§ 1, 2 UKlaG; § 307 BGB; § 3 UWG",
        verjaehrung_basis="§ 548 Abs. 1 BGB — 6 Monate ab Rückgabe "
        "(Mietvertrags-Qualifikation über die AGB des Anbieters selbst)",
        confidence_floor=0.75,  # the honest auto-abo gap: § 548-analog argued as chain, O4 gate
        has_own_logistics=True,
        deficit_heuristic=True,
    ),
    Domain.BANKING: DomainProfile(
        domain=Domain.BANKING,
        method_flaw=_GENERIC_METHOD_FLAW,
        method_citation="§ 249 Abs. 1 BGB; § 286 ZPO",
        method_correct="Nachvollziehbare Berechnung nach § 249 Abs. 1 BGB, § 254 BGB",
        regulatory_body="BaFin / Verbraucherzentrale",
        regulatory_law="§§ 1, 2 UKlaG; § 307 BGB",
        verjaehrung_basis="§ 195 BGB — 3 Jahre",
        confidence_floor=0.85,
    ),
    Domain.INSURANCE: DomainProfile(
        domain=Domain.INSURANCE,
        method_flaw=_GENERIC_METHOD_FLAW,
        method_citation="§ 249 Abs. 1 BGB; § 286 ZPO",
        method_correct="Regulierung nach § 249 BGB mit Wirtschaftlichkeitsgebot (§ 254 BGB)",
        regulatory_body="BaFin",
        regulatory_law="§§ 1, 2 UKlaG; VVG",
        verjaehrung_basis="§ 195 BGB — 3 Jahre",
        confidence_floor=0.85,
    ),
    Domain.TELECOM: DomainProfile(
        domain=Domain.TELECOM,
        method_flaw=_GENERIC_METHOD_FLAW,
        method_citation="§ 249 Abs. 1 BGB; § 286 ZPO",
        method_correct="Berechnung nur nachvertraglich gedeckter, "
        "tatsächlich angefallener Positionen",
        regulatory_body="BNetzA / Verbraucherzentrale",
        regulatory_law="§§ 1, 2 UKlaG; TKG",
        verjaehrung_basis="§ 195 BGB — 3 Jahre",
        confidence_floor=0.85,
    ),
    Domain.ENERGY: DomainProfile(
        domain=Domain.ENERGY,
        method_flaw=_GENERIC_METHOD_FLAW,
        method_citation="§ 249 Abs. 1 BGB; § 286 ZPO",
        method_correct="Nachbilanzierung nur auf Basis belastbarer Messdaten",
        regulatory_body="BNetzA",
        regulatory_law="§§ 1, 2 UKlaG; EnWG",
        verjaehrung_basis="§ 195 BGB — 3 Jahre",
        confidence_floor=0.85,
    ),
    Domain.GOVERNMENT: DomainProfile(
        domain=Domain.GOVERNMENT,
        method_flaw=_GENERIC_METHOD_FLAW,
        method_citation="§ 249 Abs. 1 BGB; § 286 ZPO",
        method_correct="Berechnung nach Maßstab der beantragten Rechtsgrundlage",
        regulatory_body="Funktionskontrolle / Kommunalaufsicht",
        regulatory_law="Verwaltungsverfahrensrecht",
        verjaehrung_basis="Sachnah: jeweilige Spezialvorschrift",
        confidence_floor=0.60,
        jurisdiction_warning="EC-6: kein UKlaG-Morphismus — das Regulierungsobjekt existiert "
        "mit anderen Pfeilen; Functor neu spezifizieren, nicht aufgeben.",
    ),
    Domain.CROSS_BORDER: DomainProfile(
        domain=Domain.CROSS_BORDER,
        method_flaw=_GENERIC_METHOD_FLAW,
        method_citation="§ 249 Abs. 1 BGB; § 286 ZPO",
        method_correct="Berechnung nach anwendbarem Sachrecht",
        regulatory_body="zuständige Stelle nach Kollisionsrecht",
        regulatory_law="Anwendbares Sachrecht klären",
        verjaehrung_basis="Anwendbare Verjährungsordnung klären",
        confidence_floor=0.50,
        jurisdiction_warning="EC-8: partieller Functor — grenzüberschreitend ist dies "
        "eine andere Kategorie. Lokale Beratung zwingend.",
    ),
}


# --------------------------------------------------------------------------- #
# SPOF engine — the deduplicated O-series (v33.0 Part 1)
# --------------------------------------------------------------------------- #

_UST_RE = re.compile(r"(?:USt|Umsatzsteuer|MwSt|Mehrwertsteuer)[^\n]{0,40}?19\s?%", re.IGNORECASE)
_LOGISTICS_RE = re.compile(
    r"(?:UPE[^a-z]?\w*|Verbringungskosten|Überführungskosten)", re.IGNORECASE
)
_INKASSO_RE = re.compile(r"(?:Inkasso|Claimfuchs|Forderungsmanagement|Inkassobüro)", re.IGNORECASE)

# SPOF code → citation topic (DSUP coverage + document emission)
_SPOF_TOPICS: dict[str, str] = {
    "EVIDENTIARY_ROOT": "minderwert_methodology",
    "CALCULATION_METHODOLOGY": "minderwert_methodology",
    "PROCESSING_BLOCK_ACCRUAL": "schufa",
    "TEMPORAL_DECAY": "verjaehrung_548",
    "TAX_PHANTOM": "umsatzsteuer",
    "AGB_ISOLATION_VOID": "abtretungsverbot",
    "LOGISTICS_PHANTOM": "upe_verbringung",
    "SYSTEMIC_REGULATORY": "systemic",
    "BUSINESS_MODEL_DEPENDENCY": "market_evidence",
    "NETWORK_EDGE_FRICTION": "systemic",
    "ESCALATION_VELOCITY_BLINDNESS": "systemic",
}


def spof_topic(code: str) -> str:
    """Public: which citation topic backs a SPOF code (empty = none)."""
    return _SPOF_TOPICS.get(code, "")


def _incoming_text(incoming: Sequence[str]) -> str:
    return "\n".join(incoming)


def _velocity_probe(tripwire_events: Sequence[object]) -> float:
    """Raw D-term probe (full model lives in gen3 — kept minimal here by layering).

    Returns intervals[0] - intervals[-1] over ≥3 dated events; positive means
    shrinking cadence (a human has taken over the file).
    """
    dates: list[date] = []
    for e in tripwire_events:
        d = getattr(e, "date", None)
        if isinstance(d, date):
            dates.append(d)
    if len(dates) < 3:
        return 0.0
    dates = sorted(dates)
    intervals = [(b - a).days for a, b in pairwise(dates)]
    return float(intervals[0] - intervals[-1])


def analyze_spofs_universal(
    threat: Threat,
    agb_present: bool,
    incoming: Sequence[str],
    cfg: RagnarConfig | None = None,
    tripwire_events: Sequence[object] | None = None,
) -> list[SPOF]:
    """Run the deduplicated O-series constellation against a threat.

    Params
    ------
    agb_present: does the opponent operate on its own AGB (O6 gate)?
    incoming:    texts received from the opponent (O3/O5/O7/O10 evidence).
    cfg:         engine config; None → default_cfg().
    tripwire_events: dated events for the O11 velocity probe.

    Output is sorted by severity (stable) — the firing order is the attack order.
    """
    cfg = cfg or default_cfg()
    profile = DOMAINS.get(threat.domain, DOMAINS[Domain.BANKING])
    text = _incoming_text(incoming)
    found: list[SPOF] = []

    def add(s: SPOF) -> None:
        found.append(s)

    quant = threat.claim > 0

    # O1 — EVIDENTIARY_ROOT: measurement/methodology chain unproven (universal)
    if quant:
        add(
            SPOF(
                id="O1",
                code="EVIDENTIARY_ROOT",
                desc="Die Mess- und Berechnungskette der Forderung ist nicht dargelegt.",
                exploit="§ 286 ZPO: Beweislast beim Anspruchsteller. Die Darlegungslast wird "
                "zurückverschoben — ohne eigenes Gegengutachten (adjoint-geprüft: unser "
                "Evidenzdefizit wird nicht offen).",
                severity=Severity.CRITICAL,
                confidence=0.95,
                cascade=("claim_unschluessig",),
            )
        )

    # O2 — CALCULATION_METHODOLOGY: the method itself is unsound (universal)
    if quant:
        add(
            SPOF(
                id="O2",
                code="CALCULATION_METHODOLOGY",
                desc=f"Methodenfehler: {profile.method_flaw}.",
                exploit=f"Richtig ist: {profile.method_correct} ({profile.method_citation}). "
                "Die Methodik als Ganzes angreifen, nicht Einzelposten.",
                severity=Severity.CRITICAL,
                confidence=0.90,
                cascade=("claim_reduced_or_dead",),
            )
        )

    # O3 — PROCESSING_BLOCK_ACCRUAL: processing/reporting continues during dispute
    if len(incoming) >= cfg.o3_min_events:
        add(
            SPOF(
                id="O3",
                code="PROCESSING_BLOCK_ACCRUAL",
                desc="Der Gegner verarbeitet/meldet die bestrittene Forderung weiter.",
                exploit="§ 31 Abs. 2 BDSG; Art. 18, 82 DSGVO; BGH VI ZR 375/24: "
                "Verarbeitungssperre verlangen; jeder Kontakt danach ist "
                "Art.-82-Ereignis (als Spanne dargestellt).",
                severity=Severity.CRITICAL,
                confidence=0.90,
                cascade=("sperre", "accrual_events"),
            )
        )

    # O4 — TEMPORAL_DECAY: the claim is dying on a short clock (GATED, analogy chain)
    if threat.verjaehrung_date is not None or threat.rueckgabe_date is not None:
        expired = threat.verjaehrung_date is not None and threat.verjaehrung_date < date.today()
        add(
            SPOF(
                id="O4",
                code="TEMPORAL_DECAY",
                desc=f"Verjährungslauf: {profile.verjaehrung_basis}.",
                exploit="Einrede der Verjährung gemäß § 548 Abs. 1 BGB bzw. der "
                "einschlägigen Norm; AGB-Verlängerungen sind nach § 307 Abs. 1 BGB "
                "und BGH VIII ZR 13/17 unwirksam. "
                + (
                    "Die Frist ist abgelaufen — Anspruch verjährt."
                    if expired
                    else "Kein Hemmungsereignis bekannt — die Uhr läuft zu unseren Gunsten."
                ),
                severity=Severity.HIGH,
                confidence=profile.confidence_floor,  # honestly priced: 0.75 for the auto-abo gap
                cascade=("claim_dead",) if expired else ("claim_dying",),
            )
        )

    # O5 — TAX_PHANTOM: USt on fictive amounts
    if _UST_RE.search(text):
        add(
            SPOF(
                id="O5",
                code="TAX_PHANTOM",
                desc="Umsatzsteuer auf fiktive Schadenspositionen berechnet.",
                exploit="§ 249 Abs. 2 S. 2 BGB; BGH VIII ZR 260/10: USt nur bei tatsächlichem "
                "Aufwand — Position sofort absetzen.",
                severity=Severity.HIGH,
                confidence=0.85,
                cascade=("position_eliminated",),
            )
        )

    # O6 — AGB_ISOLATION_VOID: assignment/review bans (CONSUMER-GATED)
    if threat.is_consumer and agb_present:
        add(
            SPOF(
                id="O6",
                code="AGB_ISOLATION_VOID",
                desc="AGB enthält Abtretungs-/Überprüfungungsverbot gegenüber Verbrauchern.",
                exploit="§ 308 Nr. 9 lit. a) BGB (seit 01.10.2021) macht solche Klauseln nichtig; "
                "§ 307 BGB davor; BGH VIII ZR 285/18 (Lexfox) bestätigt Legal-Tech-Inkasso.",
                severity=Severity.MEDIUM,
                confidence=0.90,
                cascade=("agb_void",),
            )
        )

    # O7 — LOGISTICS_PHANTOM: UPE/Verbringung the claimant never incurs (NARROWED)
    if profile.has_own_logistics and _LOGISTICS_RE.search(text):
        add(
            SPOF(
                id="O7",
                code="LOGISTICS_PHANTOM",
                desc="UPE-Aufschläge/Verbringungskosten trotz eigener "
                "Logistik des Anspruchstellers.",
                exploit="BGH VI ZR 300/24 (eingeengt): fiktive UPE nur bei regional "
                "zwingendem Markenwerkstatt-Aufwand — Eigenlogistik belegt das "
                "Gegenteil (§ 242 BGB).",
                severity=Severity.MEDIUM,
                confidence=0.70,
                cascade=("position_eliminated",),
            )
        )

    # O8 — SYSTEMIC_REGULATORY: dossier to collective enforcement (PROBABILISTIC)
    if threat.claim >= cfg.o8_claim_threshold:
        add(
            SPOF(
                id="O8",
                code="SYSTEMIC_REGULATORY",
                desc="Mustererkennung: AGB-Methodik kollektiv angreifbar "
                f"({profile.regulatory_body}).",
                exploit=f"{profile.regulatory_law}: Verbandsbeschwerde/Dossier als Option — "
                "Hub-Angriff: ein Präzedenz propagiert netzweit. Wert liegt im Erwartungswert, "
                "nicht in der Einzelwahrscheinlichkeit.",
                severity=Severity.HIGH,
                confidence=cfg.p_regulatory_action,
                cascade=("expected_cost_pressure",),
            )
        )

    # O9 — BUSINESS_MODEL_DEPENDENCY: structural deficit forces overreach (HEURISTIC)
    if profile.deficit_heuristic and quant:
        add(
            SPOF(
                id="O9",
                code="BUSINESS_MODEL_DEPENDENCY",
                desc="Defizitstruktur: Marktrate unter dokumentierter Kostenbasis "
                "(Faaren-Report €563 Ø; ADAC-Kostenbasis ≈ €1.563+/Monat).",
                exploit="Nur als Prior-Setzung für das Opponentenmodell — heuristic, nie "
                "load-bearing vor Gericht (I16-Preis: confidence 0.5).",
                severity=Severity.LOW,
                confidence=0.50,
                cascade=("opponent_priors",),
            )
        )

    # O10 — NETWORK_EDGE_FRICTION: principal/agent interest divergence
    if (
        "&" in threat.opponent
        or " und " in threat.opponent.lower()
        or _INKASSO_RE.search(threat.opponent)
        or _INKASSO_RE.search(text)
    ):
        add(
            SPOF(
                id="O10",
                code="NETWORK_EDGE_FRICTION",
                desc="Multi-Akteurs-Gegner (Principal/Inkasso-Agent) mit "
                "divergierenden Interessen.",
                exploit="§ 840 BGB Gesamtschuld: beide Adressaten in einem Satz "
                "benennen — der Agent trägt Compliance-Risiko weit über seiner "
                "Marge und wirft ab.",
                severity=Severity.MEDIUM,
                confidence=0.80,
                cascade=("agent_drops_mandate",),
            )
        )

    # O11 — ESCALATION_VELOCITY_BLINDNESS: cadence reveals intent (D-term)
    if tripwire_events and _velocity_probe(tripwire_events) > cfg.velocity_threshold:
        add(
            SPOF(
                id="O11",
                code="ESCALATION_VELOCITY_BLINDNESS",
                desc="Schrumpfende Mahnintervalle: ein Mensch hat die Akte übernommen.",
                exploit="§ 256 ZPO: präemptive negative Feststellungsklage — Tempo erobern, "
                "Anker setzen, Verfahrensrahmen bestimmen (J2).",
                severity=Severity.MEDIUM,
                confidence=0.80,
                cascade=("seize_tempo",),
            )
        )

    # Jurisdiction warnings ride along, honestly priced, never weapons
    if profile.jurisdiction_warning:
        add(
            SPOF(
                id="W1",
                code="JURISDICTION_WARNING",
                desc=profile.jurisdiction_warning,
                exploit="Domain-Eingangsprüfung: Functor-Grenzen dokumentieren, lokal absichern.",
                severity=Severity.LOW,
                confidence=0.70,
                cascade=("scope_guard",),
            )
        )

    found.sort(key=lambda s: (-s.severity, s.id))  # stable: O1 before O2 on ties
    return found


# --------------------------------------------------------------------------- #
# Sterilization — channel separation enforced (J5/C20)
# --------------------------------------------------------------------------- #

# Rhetoric markers: the Scalpel Email's last two paragraphs were the 10% that failed.
# These are the fingerprints of that failure. German legal prose is the product;
# rhetoric is the defect.
_CAPS_RUN_RE = re.compile(r"\b[A-ZÄÖÜ]{5,}\b")
_CAPS_WHITELIST = frozenset(
    {"SCHUFA", "DSGVO", "BDSG", "RAGNAR", "OMNI", "VERJAHRUNG", "BEKLAGTENPROZESS"}
)
_EXCL_RUN_RE = re.compile(r"!{2,}")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_RHETORIC_MARKERS: tuple[str, ...] = (
    "korrupt",
    "lächerlich",
    "abgrundtief",
    "unerhört",
    "skandal",
    "frechheit",
    "inakzeptabel",
    "blöße",
    "empirisch zu erproben",
    "final kalibriert",
    "selbst zu geben",
    "sie werden bereuen",
    "lüge",
    "unverschämt",
    "widerwärtig",
    "betrügermasche",
    "abzocke",
    "ganoven",
)


def _caps_violations(text: str) -> list[str]:
    return [m.group(0) for m in _CAPS_RUN_RE.finditer(text) if m.group(0) not in _CAPS_WHITELIST]


def detect_violations(text: str) -> list[str]:
    """All channel-separation violations in a text. Empty list = emission-ready."""
    violations: list[str] = []
    if _EXCL_RUN_RE.search(text):
        violations.append("exclamation_run")
    violations.extend(f"caps:{w}" for w in _caps_violations(text))
    low = text.lower()
    violations.extend(f"rhetoric:{m}" for m in _RHETORIC_MARKERS if m in low)
    return violations


def _clean_pass(text: str) -> tuple[str, int]:
    """One sterilization pass over DIRTY text only: fix punctuation runs, drop
    rhetoric sentences with their separators (span-based — clean prose is never
    re-assembled, so 'Abs. 2' and paragraph breaks survive untouched)."""
    changes = 0
    if _EXCL_RUN_RE.search(text):
        text = _EXCL_RUN_RE.sub(".", text)
        changes += 1
    out: list[str] = []
    idx = 0
    for m in _SENT_SPLIT_RE.finditer(text):
        fragment = text[idx : m.end()]  # sentence incl. trailing separator
        if detect_violations(fragment):
            changes += 1  # dropped, separator with it
        else:
            out.append(fragment)
        idx = m.end()
    tail = text[idx:]
    if tail:
        if detect_violations(tail):  # final sentence has no trailing separator — filter it too
            changes += 1
        else:
            out.append(tail)
    text = "".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, changes


def recursive_sterilize(doc: Document, max_passes: int = 5) -> Document:
    """Iterative rhetoric sterilization with early exit on convergence.

    Assembles salutation + body + closing into Document.body (a plan without
    its weapons is not a plan; a document without its Anrede is not a letter).
    German legal substance is untouchable — only rhetoric dies. CLEAN text is
    passed through VERBATIM (zero surgery on zero violations: sentence surgery
    is only ever performed on dirty text).
    """
    text = doc.body
    passes = 0
    violations_total = 0
    for _ in range(max_passes):
        passes += 1
        found = detect_violations(text)
        if not found:
            break  # convergence measured — clean text exits untouched after pass 1
        violations_total += len(found)
        text, changes = _clean_pass(text)
        if changes == 0:
            break

    parts = [p for p in (doc.salutation.strip(), text.strip(), doc.closing.strip()) if p]
    assembled = "\n\n".join(parts)

    excl = len(_EXCL_RUN_RE.findall(assembled))
    caps = len(_caps_violations(assembled))
    tone = max(0.0, 1.0 - 0.15 * (excl + caps))

    return Document(
        body=assembled,
        title=doc.title,
        salutation=doc.salutation,
        closing=doc.closing,
        citations=doc.citations,
        hash=doc.hash,
        tone_score=tone,
        spof_risk=round(0.06 * violations_total + 0.03 * max(0, passes - 1), 4),
        sterilization_passes=passes,
        channel=doc.channel,
        confidence=doc.confidence,
    )


# --------------------------------------------------------------------------- #
# DSUP — Defensive Superior shield
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DSUPResult:
    """How well our citation bedrock covers the fired SPOFs. Bounded [0,1]."""

    score: float
    coverage: float
    citations_used: tuple[str, ...]


def dsup_shield(threat: Threat, spofs: Sequence[SPOF]) -> DSUPResult:
    """Defensive superiority: CONFIRMED-law coverage of the SPOF constellation.

    An empty constellation is scored 0.5 — honest neutral: no weapons needed,
    none claimed (I16: the engine never invents confidence).
    """
    if not spofs:
        return DSUPResult(score=0.5, coverage=0.0, citations_used=())
    weighted_conf = 0.0
    weight = 0.0
    used: set[str] = set()
    covered = 0
    for s in spofs:
        topic = _SPOF_TOPICS.get(s.code, "")
        if not topic:
            continue
        conf = citation_confidence(topic, court=False)
        w = float(s.severity)
        weighted_conf += conf * w
        weight += w
        if conf >= 0.5:
            covered += 1
        used.update(emit_citations(topic, court=False))
    if weight == 0:
        return DSUPResult(score=0.5, coverage=0.0, citations_used=())
    score = 0.3 + 0.7 * (weighted_conf / weight)
    return DSUPResult(
        score=round(min(1.0, max(0.0, score)), 4),
        coverage=round(covered / len(spofs), 4),
        citations_used=tuple(sorted(used)),
    )


# --------------------------------------------------------------------------- #
# Tardigrade — phase-state selection (v32.2 Dimension 2, literally thermodynamics)
# --------------------------------------------------------------------------- #

_BREAK_SIGNALS = frozenset(
    {"KLAGE", "SCHUFA", "VERJAERHRUNG_TICK", "SETTLEMENT_OFFER", "SB_ATOMIZATION", "MAHNBESCHEID"}
)


def select_tardigrade(threat_level: float, tripwire_signal: str | None) -> TState:
    """Select the Tardigrade phase.

    High threat + no tripwire + running clock → CRYPTO (glass phase: minimum
    energy, maximum patience — mathematically unbeatable when the asymmetry
    holds). Any break signal rehydrates instantly.
    """
    if tripwire_signal is not None and tripwire_signal.upper() in _BREAK_SIGNALS:
        return TState.ACTIVE
    if threat_level >= 0.8:
        return TState.CRYPTO
    if threat_level >= 0.5:
        return TState.TUN
    return TState.ACTIVE


def crypto_viability(
    threat: Threat, cfg: RagnarConfig | None = None, days: int | None = None
) -> float:
    """Viability of the CRYPTO state in [0,1].

    Physics: a dispute at zero input energy decays toward the defendant's ground
    state because the opponent must continuously expend energy to maintain the
    threat. Viability is therefore a function of the clock and the stakes.
    """
    _ = cfg  # reserved for tunables; formula is statute-shaped, not cfg-shaped
    if days is None:
        if threat.verjaehrung_date is None:
            return 0.40  # unknown clock — silence is a gamble, price it honestly
        days = (threat.verjaehrung_date - date.today()).days
    if days < 0:
        base = 1.0  # phase transition complete: enforceability dropped to 0
    elif days <= 180:
        base = 0.85
    elif days <= 365:
        base = 0.65
    else:
        base = 0.45
    attention_risk = min(threat.claim / 20_000.0, 0.25)  # large claims attract court gravity
    return round(min(1.0, max(0.0, base * (1.0 - attention_risk))), 4)


_ = (timedelta, Channel)  # reserved: kept explicit so layer imports stay auditable
