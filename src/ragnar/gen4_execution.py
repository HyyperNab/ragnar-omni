# GEN 4 — EXECUTION: builders, tripwires, Omega Lock, self-audit, orchestrator.
"""RAGNAR Ω OMNI v33.0 — Gen 4: Execution Layer.

Owns the outside world: channel-separated document builders (J5 — deterrence
through legal density, never rhetoric), the twelve semantic tripwires (C19 —
threat-pattern AND defensive-pattern separation, negations must not fire),
the fail-closed Omega Lock with nonce replay protection (I5/C17), the adjoint
self-audit (I4 — the SPOF engine run against ourselves before every maneuver),
and the Ragnar orchestrator that welds the layers into a Plan.

Layer contract: imports gen1/gen2/gen3 + config + citations. Top of the stack.
"""

from __future__ import annotations

import hmac
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import ClassVar

import numpy as np

from .citations import citation_confidence, emit_citations
from .config import RagnarConfig, default_cfg
from .gen1_foundation import (
    SPOF,
    AuditTrail,
    Channel,
    Doctrine,
    Document,
    Maneuver,
    OpponentModel,
    OpponentType,
    Plan,
    Severity,
    Threat,
    TripwireResponse,
    TripwireType,
    TState,
)
from .gen2_analysis import (
    analyze_spofs_universal,
    crypto_viability,
    detect_violations,
    dsup_shield,
    recursive_sterilize,
    select_tardigrade,
)
from .gen3_strategy import (
    calculate_verjaehrung,
    compute_victory_projection,
    days_to_verjaehrung,
    escalation_velocity,
    lagom_solve_nash,
    npv_path_dependent,
    update_opponent_model,
)

__all__ = [
    "MANEUVERS",
    "SPECS",
    "OmegaLock",
    "OmegaLockError",
    "Ragnar",
    "TripwireEvent",
    "TripwireMonitor",
    "build_document",
    "judge_adoptability",
    "self_audit",
]


# --------------------------------------------------------------------------- #
# Document specs — the eight builders. German legal substance is the product;
# the voice is the weapon; rhetoric is the defect (C20: the last two paragraphs
# of the old Scalpel Email were the 10% that failed — deleted here by design).
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    id: str
    title: str
    channel: Channel
    topics: tuple[str, ...]
    salutation: str
    body: str
    closing: str = ""
    permutable: bool = True  # polymorphism may permute sections (I11/C-spirit)
    confidence_base: float = 0.9


SPECS: dict[str, DocumentSpec] = {
    "bestreiten_sperre": DocumentSpec(
        id="bestreiten_sperre",
        title="Vollumfängliches Bestreiten mit Verarbeitungssperre",
        channel=Channel.OPPONENT_FACING,
        topics=("schufa", "minderwert_methodology"),
        salutation="Sehr geehrte Damen und Herren,",
        body=(
            "Betreff: Forderung {vertrag} — vollumfängliches Bestreiten; "
            "Verarbeitungssperre; Hinweis auf § 31 Abs. 2 BDSG\n\n"
            "1. Die mit Schreiben vom {datum} geltend gemachte Forderung über "
            "{betrag} EUR wird vollumfänglich und ohne Anerkennung einer "
            "Rechtspflicht bestritten.\n\n"
            "2. Gemäß Art. 18 DSGVO wird die Einschränkung der Verarbeitung "
            "verlangt. Jede Übermittlung an Auskunfteien ist ab Zugang dieses "
            "Schreibens unzulässig (§ 31 Abs. 2 BDSG; BGH, Urt. v. 12.05.2026 "
            "— VI ZR 375/24).\n\n"
            "3. Zur Begründetheit: Ein Minderwert ergibt sich nicht aus der "
            "Aufsummierung fiktiver Reparaturkosten (OLG Stuttgart, Urt. v. "
            "28.10.2025 — 6 U 84/24; § 249 Abs. 1 BGB). Eine auf diese Weise "
            "berechnete Forderung ist nicht plausibel dargelegt, mit der Folge, "
            "dass ihre Übermittlung unabhängig vom Bestreiten unzulässig ist "
            "(BGH, Urt. v. 12.05.2026 — VI ZR 375/24).\n\n"
            "4. Ein den Anforderungen des § 31 Abs. 2 BDSG genügender "
            "Warnhinweis ist nicht rechtzeitig erfolgt.\n\n"
            "5. Dieses Schreiben richtet sich gegen Sie als Inhaber der "
            "Forderung und gegen jeden eingeschalteten Dritten in gleicher "
            "Weise (§ 840 BGB).\n\n"
            "6. Sachverhalt: {sachverhalt}."
        ),
        closing="Einer weiteren außergerichtlichen Korrespondenz in dieser "
        "Sache wird nicht entgegengesehen.",
    ),
    "verjaehrungseinrede": DocumentSpec(
        id="verjaehrungseinrede",
        title="Einrede der Verjährung (§ 548 Abs. 1 BGB)",
        channel=Channel.COURT_FACING,
        topics=("verjaehrung_548",),
        salutation="",
        body=(
            "An das {gericht} — Az. {aktenzeichen}\n\n"
            "1. Die Einrede der Verjährung wird gemäß § 548 Abs. 1 BGB erhoben.\n\n"
            "2. Das Fahrzeug wurde am {rueckgabe} zurückgegeben. Die Frist von "
            "sechs Monaten begann mit diesem Tag. Bis heute ist weder "
            "Rechtshängigkeit noch ein Hemmungsereignis nach § 204 Abs. 1 BGB "
            "eingetreten. Die Frist lief am {verjaehrung} ab.\n\n"
            "3. Formularvertragliche Verlängerungen dieser Frist wären nach "
            "§ 307 Abs. 1 BGB unwirksam (BGH, Urt. v. 08.11.2017 — VIII ZR "
            "13/17). Eine Verlängerung ist nicht wirksam vereinbart.\n\n"
            "4. Der Anspruch ist somit verjährt und nach § 214 Abs. 1 BGB zu "
            "abweisen, soweit die Einrede erhoben wird.\n\n"
            "5. Ergänzend wird auf die Besitzrückgabe iSd § 548 Abs. 1 S. 2 "
            "BGB abgestellt (BGH, Urt. v. 29.01.2025 — XII ZR 96/23)."
        ),
    ),
    "methodology_defense": DocumentSpec(
        id="methodology_defense",
        title="Methodische Einwände gegen die Schadensberechnung",
        channel=Channel.COURT_FACING,
        topics=("minderwert_methodology", "gebrauchsspuren"),
        salutation="",
        body=(
            "An das {gericht} — Az. {aktenzeichen}\n\n"
            "1. Die Berechnungsmethodik des Klägers ist ungeeignet, einen "
            "ersatzfähigen Schaden zu belegen. Der Minderwert entspricht "
            "regelmäßig nicht der Summe aller Reparaturkosten (OLG Stuttgart, "
            "Urt. v. 28.10.2025 — 6 U 84/24).\n\n"
            "2. Ein Abzug Neu für Alt ist zwingend (§ 249 Abs. 1 BGB: "
            "Bereicherungsverbot). Neue Preise für einen gebrauchten "
            "Gegenstand bereichern den Anspruchsteller und sind nicht "
            "ersatzfähig.\n\n"
            "3. Ersetzbar sind nur Schäden, die über die üblichen "
            "Gebrauchsspuren hinausgehen (§ 538 BGB; OLG Stuttgart a.a.O.). "
            "Die monatliche Rate hat die gewöhnliche Abnutzung vollständig "
            "abgegolten.\n\n"
            "4. Die Darlegungs- und Beweislast für jede Position liegt beim "
            "Kläger (§ 286 ZPO). Eine Aufstellung, die lediglich fiktive "
            "Einzelkosten addiert, genügt den Anforderungen an die "
            "Darlegung eines marktüblichen Minderwerts nicht.\n\n"
            "5. Die Schätzung nach § 287 ZPO setzt eine tragfähige "
            "Berechnungsgrundlage voraus; die Summe fiktiver Positionen "
            "ist keine solche Grundlage."
        ),
    ),
    "schufa_unterlassung": DocumentSpec(
        id="schufa_unterlassung",
        title="Verarbeitungssperre und Unterlassung (SCHUFA)",
        channel=Channel.OPPONENT_FACING,
        topics=("schufa",),
        salutation="Sehr geehrte Damen und Herren,",
        body=(
            "Betreff: {vertrag} — Verarbeitungssperre gemäß Art. 18 DSGVO; "
            "Aufforderung zum Widerruf etwaiger Meldungen\n\n"
            "1. Die Forderung wird bestritten. Gemäß § 31 Abs. 2 BDSG ist die "
            "Übermittlung bestrittener Forderungen an Auskunfteien gesetzlich "
            "unzulässig.\n\n"
            "2. Nach BGH, Urt. v. 12.05.2026 — VI ZR 375/24 stellt die "
            "bestrittene Forderung keine belastbare Bonitätsinformation dar. "
            "Etwaige Meldungen sind unverzüglich zu widerrufen.\n\n"
            "3. Gemäß Art. 18 DSGVO wird die Einschränkung der Verarbeitung "
            "verlangt; gemäß Art. 21 DSGVO wird der Verarbeitung ausdrücklich "
            "widersprochen.\n\n"
            "4. Sollte gleichwohl eine Meldung erfolgen, bleibt die Geltend"
            "machung von Ansprüchen nach Art. 82 DSGVO ausdrücklich vorbehalten; "
            "die Höhe etwaiger Ansprüche richtet sich nach den Umständen des "
            "Einzelfalls."
        ),
        closing="Ich bitte um schriftliche Bestätigung der Sperrung und des "
        "Widerrufs innerhalb von zehn Tagen.",
    ),
    "abtretungsverbot_defense": DocumentSpec(
        id="abtretungsverbot_defense",
        title="Unwirksamkeit des Abtretungsverbots (§ 308 Nr. 9 BGB)",
        channel=Channel.OPPONENT_FACING,
        topics=("abtretungsverbot",),
        salutation="Sehr geehrte Damen und Herren,",
        body=(
            "Betreff: {vertrag} — Abtretungsbeschränkung in Ihren AGB\n\n"
            "1. Die in Ihren Allgemeinen Geschäftsbedingungen enthaltene "
            "Beschränkung der Abtretbarkeit von Geldansprüchen ist gemäß "
            "§ 308 Nr. 9 lit. a) BGB nichtig.\n\n"
            "2. Unabhängig davon bleibt das Grundrecht des Verbrauchers auf "
            "unbeschränkte Wahrnehmung seiner Rechte durch Rechtsdienst"
            "leister unberührt (BGH, Urt. v. 27.11.2019 — VIII ZR 285/18; "
            "§ 10 Abs. 1 S. 1 Nr. 1 RDG).\n\n"
            "3. Soweit Sie sich auf das Verbot berufen, wird dessen Unwirksam"
            "keit hiermit ausdrücklich gerügt."
        ),
    ),
    "systemic_exposure": DocumentSpec(
        id="systemic_exposure",
        title="Systematische Einordnung des Geschäftsmodells",
        channel=Channel.COURT_FACING,
        topics=("market_evidence", "minderwert_methodology"),
        salutation="",
        body=(
            "An das {gericht} — Az. {aktenzeichen}\n\n"
            "1. Zur Einordnung wird auf veröffentlichte Marktdaten Bezug "
            "genommen: Der durchschnittliche Abo-Monatstarif betrug nach dem "
            "Auto-Abo-Report der Faaren Group 563 EUR (2024) bei einem Abo-"
            "Faktor von 1,07 Prozent des Fahrzeuglistenpreises (2025).\n\n"
            "2. Die Kostenbasis eines Neuwagens der gebuchten Klasse liegt "
            "nach den Daten der ADAC Autokostendatenbank (2024) erheblich "
            "über diesem Tarifniveau.\n\n"
            "3. Hieraus folgt als statistischer Befund: Der économique"
            "ische Hauptumsatz solcher Modelle wird regelmäßig am Vertrags"
            "ende generiert. Dies begründet keine Vermutung gegen den Kläger "
            "im Einzelfall, erklärt aber, warum die gewählte Abrechnungs"
            "methodik systematisch zu Nachforderungen führt.\n\n"
            "4. Die rechtliche Bewertung jeder Einzelforderung bleibt an den "
            "Maßstab des § 249 Abs. 1 BGB gebunden; die Marktdaten dienen "
            "allein dem Verständnis des Verfahrensgegenstands."
        ),
        confidence_base=0.6,  # heuristic tier: honest ceiling for market-based argumentation
    ),
    "feststellungsklage": DocumentSpec(
        id="feststellungsklage",
        title="Negative Feststellungsklage (§ 256 ZPO)",
        channel=Channel.COURT_FACING,
        topics=("systemic", "minderwert_methodology"),
        salutation="",
        body=(
            "An das {gericht}\n\n"
            "1. Es wird festgestellt werden, dass der Beklagten aus dem "
            "Vertragsverhältnis {vertrag} kein Anspruch auf Zahlung von "
            "{betrag} EUR zusteht (§ 256 ZPO).\n\n"
            "2. Das Feststellungsinteresse folgt aus der angekündigten "
            "Klageerhebung und der drohenden Meldung an Auskunfteien.\n\n"
            "3. Begründetheit: Die geltend gemachte Forderung beruht auf der "
            "Addition fiktiver Reparaturkosten ohne Minderwertberechnung und "
            "ohne Abzug Neu für Alt (§ 249 Abs. 1 BGB; OLG Stuttgart, Urt. "
            "v. 28.10.2025 — 6 U 84/24). Diese Methode trägt eine Darlegung "
            "nach § 286 ZPO nicht.\n\n"
            "4. Das Fahrzeug wurde am {rueckgabe} zurückgegeben; Ansprüche "
            "wegen Veränderungen der Mietsache verjähren in sechs Monaten "
            "(§ 548 Abs. 1 BGB). Der Klagevortrag nennt kein Hemmungs"
            "ereignis (§ 204 Abs. 1 BGB).\n\n"
            "5. Beweis: Rückgabeprotokoll vom {rueckgabe}; Schreiben vom "
            "{datum}; Vertragsunterlagen {vertrag}."
        ),
    ),
    "klageerwiderung": DocumentSpec(
        id="klageerwiderung",
        title="Klageerwiderung (Struktur)",
        channel=Channel.COURT_FACING,
        topics=("minderwert_methodology", "verjaehrung_548", "umsatzsteuer", "schufa"),
        salutation="",
        body=(
            "An das {gericht} — Az. {aktenzeichen}\n\n"
            "1. Die Klage wird in vollem Umfang bestritten.\n\n"
            "2. Einrede der Verjährung: Die Rückgabe erfolgte am {rueckgabe}; "
            "die Frist des § 548 Abs. 1 BGB ist abgelaufen (§ 214 Abs. 1 "
            "BGB). Ein Hemmungsereignis nach § 204 Abs. 1 BGB ist nicht "
            "vorgetragen.\n\n"
            "3. Methodik: Die Klageberechnung addiert fiktive Reparatur"
            "kosten. Der Minderwert entspricht regelmäßig nicht der Summe "
            "aller Reparaturkosten (OLG Stuttgart, Urt. v. 28.10.2025 — "
            "6 U 84/24). Der zwingende Abzug Neu für Alt fehlt (§ 249 "
            "Abs. 1 BGB).\n\n"
            "4. Umsatzsteuer: Soweit auf fiktive Positionen Umsatzsteuer "
            "berechnet wird, ist diese nicht erstattungsfähig (§ 249 Abs. 2 "
            "S. 2 BGB; BGH, Urt. v. 18.05.2011 — VIII ZR 260/10).\n\n"
            "5. Gebrauchsspuren: Positionen, die übliche Gebrauchsspuren "
            "betreffen, sind nach § 538 BGB nicht ersatzfähig.\n\n"
            "6. Verarbeitung: Die bestrittene Forderung darf an keine "
            "Auskunftei übermittelt werden (§ 31 Abs. 2 BDSG; BGH, Urt. v. "
            "12.05.2026 — VI ZR 375/24).\n\n"
            "7. Beweislast: Der Kläger trägt Darlegung und Beweis für jede "
            "Position (§ 286 ZPO).\n\n"
            "8. Es wird Klageabweisung beantragt."
        ),
    ),
}

_FMT_RE = re.compile(r"\{(\w+)\}")


def _fmt(template: str, ctx: dict[str, str]) -> str:
    """Placeholder substitution. Missing keys render as [offen] — honest gaps,
    never invented facts (ground truth or silence)."""
    return _FMT_RE.sub(lambda m: str(ctx.get(m.group(1), "[offen]")), template)


def _german_amount(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_document(
    spec_id: str,
    ctx: dict[str, str],
    cfg: RagnarConfig | None = None,
    seed: int | None = None,
) -> Document:
    """Render one document: template → citations (trust-gated) → sterilize → hash.

    Citation gating: COURT_FACING emits CONFIRMED tier only; letters at least
    PROBABLE. Quarantined entries are structurally unreachable (I1/I2).
    Polymorphism (I11): with a seed, citation order is permuted — no two
    deployments share a fingerprint; substance never varies, only surface.
    """
    cfg = cfg or default_cfg()
    spec = SPECS[spec_id]
    court = spec.channel is Channel.COURT_FACING

    citations: list[str] = []
    for topic in spec.topics:
        for c in emit_citations(topic, court=court):
            if c not in citations:
                citations.append(c)
    if seed is not None and citations:
        rng = np.random.default_rng(seed)
        order = np.argsort(rng.random(len(citations)))
        citations = [citations[i] for i in order]

    conf = (
        min([spec.confidence_base] + [citation_confidence(t, court=court) for t in spec.topics])
        if spec.topics
        else spec.confidence_base
    )

    draft = Document(
        body=_fmt(spec.body, ctx),
        salutation=_fmt(spec.salutation, ctx),
        closing=_fmt(spec.closing, ctx),
        citations=tuple(citations),
        channel=spec.channel,
        confidence=round(max(0.0, conf), 4),
    )
    clean = recursive_sterilize(draft)
    fingerprint = sha256((clean.body + "|" + "|".join(clean.citations)).encode("utf-8")).hexdigest()
    return Document(
        body=clean.body,
        salutation=clean.salutation,
        closing=clean.closing,
        citations=clean.citations,
        hash=fingerprint,
        tone_score=clean.tone_score,
        spof_risk=clean.spof_risk,
        sterilization_passes=clean.sterilization_passes,
        channel=clean.channel,
        confidence=clean.confidence,
    )


def judge_adoptability(doc: Document) -> float:
    """The decisive fitness metric for court documents in [0,1]:

    adoptability = (structure × citation_density × brevity) / (1 + rhetoric)

    The best legal document is the one the judge can plagiarize — write
    urteilsfähig and the court adopts your text into the Entscheidungsgründe.
    """
    structure_markers = len(re.findall(r"(?m)^\s*(?:\d+\.|I+\.|[IVX]+\.)\s", doc.body))
    structure = min(1.0, 0.3 + 0.12 * structure_markers)
    density = min(1.0, len(doc.citations) / 6.0)
    brevity = min(1.0, max(0.1, 1.0 - len(doc.body) / 12_000))
    rhetoric = len(detect_violations(doc.body))
    return round(structure * density * brevity / (1.0 + rhetoric), 4)


# --------------------------------------------------------------------------- #
# Self-audit — the adjoint check (I4): run the SPOF engine against ourselves
# --------------------------------------------------------------------------- #


def _iban_valid(iban: str) -> bool:
    """ISO 13616 mod-97 check — our own data hygiene before we demand theirs."""
    v = re.sub(r"\s", "", iban).upper()
    if len(v) < 15 or not v.isalnum():
        return False
    rearranged = v[4:] + v[:4]
    numeric = "".join(str(int(c, 36)) for c in rearranged)
    return int(numeric) % 97 == 1


def self_audit(maneuver: Maneuver, threat: Threat) -> list[SPOF]:
    """Adjoint audit: every SPOF we deploy exists symmetrically on us.

    A weapon you cannot survive is not a weapon. If this returns HIGH-severity
    internal SPOFs, the maneuver is not Lagom.
    """
    findings: list[SPOF] = []

    if maneuver.aggression >= 0.8 and not threat.correspondence:
        findings.append(
            SPOF(
                id="I-A",
                code="SELF_OVERREACH",
                desc="Aggressiver Manöver ohne Korrespondenzkorpus: keine Grundlage "
                "für Kosten-Nutzen-Annahmen des Gegnerverhaltens.",
                exploit="Downgrade auf beweislastverschiebende Manöver (O2), die "
                "kein Gegengutachten verlangen.",
                severity=Severity.HIGH,
                confidence=0.70,
                cascade=("aggression_damped",),
            )
        )

    if maneuver.id == "WIDERKLAGE":
        findings.append(
            SPOF(
                id="I-B",
                code="SELF_ART82_RANGE",
                desc="Art.-82-Schaden ist diskretionär, nicht tarifiert.",
                exploit="Schadensersatz ausnahmslos als Spanne mit Belegzitaten "
                "darstellen — nie als Arithmetik.",
                severity=Severity.LOW,
                confidence=0.90,
                cascade=("methodology_clean",),
            )
        )

    if threat.bank_account and not _iban_valid(threat.bank_account):
        findings.append(
            SPOF(
                id="I-C",
                code="SELF_DATA_QUALITY",
                desc="Eigene Kontodaten bestehen die Mod-97-Prüfung nicht.",
                exploit="Datenhygiene korrigieren, bevor Verarbeitungssperren "
                "verlangt werden (adjoint: sie prüfen uns genauso).",
                severity=Severity.LOW,
                confidence=0.95,
                cascade=("credibility_risk",),
            )
        )

    if threat.is_consumer and threat.agb_excerpt and "abtretung" not in threat.agb_excerpt.lower():
        pass  # no O6 exploitation without evidence — silence over speculation

    return findings


# --------------------------------------------------------------------------- #
# Tripwires — twelve semantic patterns, negation-guarded (C19)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class TripwireEvent:
    type: TripwireType
    severity: Severity
    response: TripwireResponse
    date: date
    detail: str = ""

    @property
    def name(self) -> str:
        return self.type.name

    def to_json(self) -> dict[str, str | int]:
        return {
            "type": self.type.value,
            "severity": int(self.severity),
            "response": self.response.value,
            "date": self.date.isoformat(),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class _TripPattern:
    type: TripwireType
    severity: Severity
    response: TripwireResponse
    pattern: re.Pattern[str]


_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_NEGATION_RE = re.compile(
    r"\b(?:keine[rnms]?|nicht|bestätigen|widerrufen|zurückgenommen|erledigt)\b",
    re.IGNORECASE,
)

_PATTERNS: tuple[_TripPattern, ...] = (
    _TripPattern(
        TripwireType.KLAGE,
        Severity.CRITICAL,
        TripwireResponse.REHYDRATE,
        re.compile(
            r"Klage(?:\s+wird|\s+ist|\s+wurde)?[^.]{0,60}erhoben"
            r"|Rechtshängigkeit|Klageeingang|Mahnantrag"
        ),
    ),
    _TripPattern(
        TripwireType.SCHUFA,
        Severity.HIGH,
        TripwireResponse.COUNTER_ESCALATE,
        re.compile(r"\bSCHUFA\b|Auskunftei|Bonitätsinformation"),
    ),
    _TripPattern(
        TripwireType.MAHNBESCHEID,
        Severity.HIGH,
        TripwireResponse.REHYDRATE,
        re.compile(r"\bMahnbescheid\b"),
    ),
    _TripPattern(
        TripwireType.EINREICHUNGSVERBOT,
        Severity.HIGH,
        TripwireResponse.COUNTER_ESCALATE,
        re.compile(r"Einreichungsverbot|Frist[^.]{0,60}verstreichen[^.]{0,40}Klage"),
    ),
    _TripPattern(
        TripwireType.KLAGEDROHUNG,
        Severity.MEDIUM,
        TripwireResponse.LOG_ONLY,
        re.compile(r"Klage[^.]{0,80}(?:erheben|androhen|in Aussicht)"),
    ),
    _TripPattern(
        TripwireType.INKASSO,
        Severity.MEDIUM,
        TripwireResponse.SILENCE,
        re.compile(r"\bInkasso\b|Claimfuchs|Forderungsmanagement|Inkassobüro"),
    ),
    _TripPattern(
        TripwireType.SB_ATOMIZATION,
        Severity.HIGH,
        TripwireResponse.COUNTER_ESCALATE,
        re.compile(r"Selbstbeteiligung"),
    ),  # count-checked separately
    _TripPattern(
        TripwireType.SETTLEMENT_OFFER,
        Severity.MEDIUM,
        TripwireResponse.ACCEPT,
        re.compile(r"Vergleichs(?:angebot|vorschlag)|außergerichtliche[rsn]?\s+Vergleich"),
    ),
    _TripPattern(
        TripwireType.GEGENDARSTELLUNG,
        Severity.MEDIUM,
        TripwireResponse.LOG_ONLY,
        re.compile(r"\bGegendarstellung\b"),
    ),
    _TripPattern(
        TripwireType.ANERKENNTUNG,
        Severity.MEDIUM,
        TripwireResponse.LOG_ONLY,
        re.compile(r"Forderung[^.]{0,80}(?:anerkannt|anerkennt|Teilzahlung)"),
    ),
    _TripPattern(
        TripwireType.GUTACHTEN_FORDERUNG,
        Severity.MEDIUM,
        TripwireResponse.LOG_ONLY,
        re.compile(r"Gutachten[^.]{0,120}(?:Rechnung|fordern|forderung|bezahlen|begleichen)"),
    ),
)


class TripwireMonitor:
    """Semantic incoming-mail monitor. A pattern fires only when its sentence
    is not negated — 'keine SCHUFA-Meldung erfolgt' must never trigger."""

    def __init__(self, cfg: RagnarConfig | None = None) -> None:
        self.cfg = cfg or default_cfg()

    def check(
        self,
        text: str,
        tstate: TState,
        days_to_verjaehrung: int | None = None,
    ) -> TripwireEvent | None:
        """Scan one incoming text. Returns the highest-severity true positive."""
        _ = tstate  # state informs rehydration policy, not detection — kept in API
        today = date.today()

        # D-term tick: the § 548 clock crossing the 30-day line
        if (
            days_to_verjaehrung is not None
            and 0 <= days_to_verjaehrung <= self.cfg.verjaehrung_tick_days
        ):
            return TripwireEvent(
                type=TripwireType.VERJAERHRUNG_TICK,
                severity=Severity.HIGH,
                response=TripwireResponse.REHYDRATE,
                date=today,
                detail=f"Verjährung in {days_to_verjaehrung} Tagen — Einrede vorbereiten",
            )

        sentences = _SENT_SPLIT_RE.split(text)

        # SB atomization: one invoice, N identical Selbstbeteiligung positions
        sb_count = len(re.findall(r"Selbstbeteiligung", text))
        sb_event: TripwireEvent | None = None
        if sb_count >= 3:
            sb_event = TripwireEvent(
                type=TripwireType.SB_ATOMIZATION,
                severity=Severity.HIGH,
                response=TripwireResponse.COUNTER_ESCALATE,
                date=today,
                detail=f"{sb_count} Selbstbeteiligung-Positionen — Atomisierung eines einheitlichen Lebenssachverhalts",
            )

        best: TripwireEvent | None = sb_event
        for pat in _PATTERNS:
            if pat.type is TripwireType.SB_ATOMIZATION:
                continue  # handled by count above
            m = pat.pattern.search(text)
            if not m:
                continue
            sent = next((s for s in sentences if m.group(0) in s), "")
            if sent and _NEGATION_RE.search(sent):
                continue  # negated → defensive pattern, not a threat
            ev = TripwireEvent(
                type=pat.type,
                severity=pat.severity,
                response=pat.response,
                date=today,
                detail=m.group(0)[:120],
            )
            if best is None or ev.severity > best.severity:
                best = ev
        return best

    def should_break_cryptobiosis(self, event: TripwireEvent) -> bool:
        """Break CRYPTO on lock conditions or HIGH+ severity (J-series tested)."""
        return event.name in self.cfg.break_conditions or event.severity >= Severity.HIGH


# --------------------------------------------------------------------------- #
# Omega Lock — fail-closed, nonce-protected, timing-safe (I5/C17)
# --------------------------------------------------------------------------- #


class OmegaLockError(RuntimeError):
    """Raised when the lock refuses to engage — absent key is a hard stop."""


class OmegaLock:
    """The commitment device: once engaged, no action until a break condition
    with a FRESH nonce unlocks. Replay of an old nonce is rejected — C17 dead.

    Fail-closed by design: no RAGNAR_OMEGA_KEY in the environment → engage()
    raises. That is correct behavior; do not 'fix' it by hardcoding.
    """

    def __init__(self) -> None:
        self._used_nonces: set[str] = set()  # survives re-engagement (replay horizon)
        self._unlock_key_hash: str | None = None
        self._token: str = ""
        self._conditions: set[str] = set()
        self._engaged = False

    @property
    def engaged(self) -> bool:
        return self._engaged

    def engage(self, doctrine: Doctrine, tstate: TState, conditions: Sequence[str]) -> bool:
        """Arm the lock. Requires RAGNAR_OMEGA_KEY — only its hash is stored."""
        try:
            key = os.environ["RAGNAR_OMEGA_KEY"]  # KeyError > silent default (S105)
        except KeyError as exc:
            msg = "fail-closed: RAGNAR_OMEGA_KEY not set — the lock refuses to engage"
            raise OmegaLockError(msg) from exc
        self._token = f"{doctrine.value}|{tstate.value}|{'|'.join(sorted(conditions))}"
        self._unlock_key_hash = sha256((key + self._token).encode("utf-8")).hexdigest()
        self._conditions = set(conditions)
        self._engaged = True
        return True

    def unlock(self, tripwire: TripwireType, nonce: str) -> bool:
        """Unlock only for a break condition with a fresh nonce, under the
        key the lock was armed with (rotation invalidates — fail closed)."""
        if not self._engaged or self._unlock_key_hash is None:
            return False
        if tripwire.name not in self._conditions:
            return False
        if not nonce or nonce in self._used_nonces:
            return False  # replay (C17) — the same nonce never works twice
        try:
            key = os.environ["RAGNAR_OMEGA_KEY"]
        except KeyError:
            return False
        expected = sha256((key + self._token).encode("utf-8")).hexdigest()
        if not hmac.compare_digest(expected, self._unlock_key_hash):
            return False  # key rotated since engage — fail closed, timing-safe
        self._used_nonces.add(nonce)
        self._engaged = False
        return True


# --------------------------------------------------------------------------- #
# Maneuver registry — ids double as causal profile ids (registry-locked)
# --------------------------------------------------------------------------- #

MANEUVERS: tuple[Maneuver, ...] = (
    Maneuver(
        "SILENCE",
        "Cryptobiosis-Halten",
        "§ 548 Abs. 1 BGB — die Uhr arbeitet",
        Doctrine.ZHUGE,
        0.10,
        0.0,
    ),
    Maneuver("DEMAND_REFUND", "Rückforderung", "§ 812 BGB", Doctrine.FABIAN, 0.40, 120.0),
    Maneuver(
        "GEGENERKLAERUNG",
        "Beweislastverschiebung",
        "§ 286 ZPO; OLG Stuttgart 6 U 84/24",
        Doctrine.HANNIBAL,
        0.60,
        100.0,
    ),
    Maneuver(
        "VERJAERHRUNGSEINREDE",
        "Verjährungseinrede",
        "§ 548 Abs. 1 BGB",
        Doctrine.FABIAN,
        0.30,
        50.0,
    ),
    Maneuver(
        "SCALPEL_LETTER",
        "Präzisionsantwort",
        "§ 249 BGB — Darlegungslast zurückverschieben",
        Doctrine.HANNIBAL,
        0.85,
        150.0,
    ),
    Maneuver(
        "REGULATORY_DOSSIER", "Verbandsdossier", "§§ 1, 2 UKlaG", Doctrine.CAESAR, 0.70, 200.0
    ),
    Maneuver(
        "FESTSTELLUNGSKLAGE",
        "Negative Feststellungsklage",
        "§ 256 ZPO — Tempo erobern",
        Doctrine.CAESAR,
        0.80,
        400.0,
    ),
    Maneuver(
        "WIDERKLAGE", "DSGVO-Widerklage", "Art. 82 DSGVO; § 840 BGB", Doctrine.HANNIBAL, 0.95, 300.0
    ),
)

_DOCS_FOR_MANEUVER: dict[str, tuple[str, ...]] = {
    "SILENCE": ("bestreiten_sperre", "verjaehrungseinrede", "methodology_defense"),
    "DEMAND_REFUND": ("bestreiten_sperre", "methodology_defense"),
    "GEGENERKLAERUNG": ("bestreiten_sperre", "methodology_defense"),
    "VERJAERHRUNGSEINREDE": ("verjaehrungseinrede", "bestreiten_sperre"),
    "SCALPEL_LETTER": ("bestreiten_sperre", "methodology_defense", "schufa_unterlassung"),
    "REGULATORY_DOSSIER": ("systemic_exposure", "bestreiten_sperre"),
    "FESTSTELLUNGSKLAGE": ("feststellungsklage", "methodology_defense"),
    "WIDERKLAGE": ("schufa_unterlassung", "bestreiten_sperre"),
    "KLAGE_ERWIDERUNG": ("klageerwiderung", "verjaehrungseinrede"),
}


def _doctrine_for_aggression(p_aggressive: float) -> Doctrine:
    if p_aggressive >= 0.75:
        return Doctrine.HANNIBAL
    if p_aggressive >= 0.55:
        return Doctrine.CAESAR
    if p_aggressive >= 0.40:
        return Doctrine.FABIAN
    return Doctrine.ZHUGE


# --------------------------------------------------------------------------- #
# Orchestrator — welds the layers into a Plan
# --------------------------------------------------------------------------- #


class Ragnar:
    """The engine. decide() ingests a threat and returns a fully-priced Plan;
    ingest_incoming() processes opponent mail through the tripwire monitor.

    Execution is fail-closed (Omega Lock); drafting is not — the engine
    produces documents, it never files them. The human checkpoint is a
    feature, not a disclaimer.
    """

    _assembly_patched: ClassVar[bool] = False  # integration-layer marker (Gen 5)

    def __init__(self, resources: float = 10.0, cfg: RagnarConfig | None = None) -> None:
        self.cfg = cfg or default_cfg()
        self.resources = resources
        self.monitor = TripwireMonitor(self.cfg)
        self.audit = AuditTrail()
        self.model = OpponentModel.uniform()
        self.tstate = TState.ACTIVE
        self.doctrine = Doctrine.ZHUGE
        self.lock = OmegaLock()
        self.rng = np.random.default_rng(self.cfg.seed)
        self._history: list[TripwireEvent] = []
        self._last_threat: Threat | None = None

    # ---------------------------------------------------------------- decide
    def decide(self, threat: Threat, resources: float | None = None) -> Plan:
        """Full pipeline: encode → SPOFs → shield → Nash-Lagom → maneuver →
        self-audit → documents → Tardigrade → lock → priced Plan."""
        if resources is not None:
            self.resources = resources
        self._last_threat = threat
        cfg = self.cfg
        self.audit.append("INGEST", f"{threat.domain.value}|{threat.opponent}|{threat.claim}")

        # SPOF constellation (O-series) — attack order = severity order
        agb_present = bool(threat.agb_excerpt.strip())
        spofs = analyze_spofs_universal(
            threat,
            agb_present,
            threat.correspondence,
            cfg,
            self._history,
        )
        self.audit.append("SPOF", ",".join(s.code for s in spofs) or "none")

        # Defensive superiority
        dsup = dsup_shield(threat, spofs)
        self.audit.append("DSUP", f"score={dsup.score}|coverage={dsup.coverage}")

        # Escalation velocity → tempo policy (O11)
        velocity = escalation_velocity(self._history)
        if velocity > cfg.velocity_threshold:
            self.audit.append("VELOCITY", f"{velocity:+.0f}d — human takeover detected")

        # Nash-Lagom doctrine selection — the ZHUGE condition derived, not felt
        clock = crypto_viability(threat, cfg)
        p_aggressive, ev = lagom_solve_nash(
            self.model.rationality_weight,
            threat.claim,
            cfg.defense_cost_ceiling,
            clock,
            cfg,
        )
        doctrine = _doctrine_for_aggression(p_aggressive)
        self.audit.append(
            "LAGOM", f"p_agg={p_aggressive}|clock={clock}|EV={ev}|doctrine={doctrine.value}"
        )

        # Maneuver selection: path-dependent NPV + doctrine affinity
        best_m, best_score = None, None
        for m in MANEUVERS:
            score = npv_path_dependent(m, self.model, claim=threat.claim, cfg=cfg, rng=self.rng)
            if m.doctrine is doctrine:
                score += 75.0  # affinity: the doctrine is the equilibrium — aligned maneuvers get priority
            if best_score is None or score > best_score:
                best_m, best_score = m, score
        if best_m is None:  # MANEUVERS is non-empty by construction — fail loud anyway
            raise RuntimeError("maneuver registry empty")
        maneuver = best_m
        self.audit.append("MANEUVER", f"{maneuver.id}|score={best_score:.2f}")

        # Adjoint self-audit (I4) — before the maneuver is committed
        internal = self_audit(maneuver, threat)
        if internal:
            self.audit.append("SELF_AUDIT", ";".join(s.code for s in internal))
        penalty = 0.03 * sum(1 for s in internal if s.severity >= Severity.HIGH)

        # Documents — channel-separated, trust-gated, polymorphic-seeded
        ctx = self._ctx_from(threat)
        docs = tuple(
            build_document(spec_id, ctx, cfg=cfg, seed=cfg.seed)
            for spec_id in _DOCS_FOR_MANEUVER.get(maneuver.id, ("bestreiten_sperre",))
        )

        # Tardigrade phase
        threat_level = self._threat_level(threat, spofs)
        signal = self._history[-1].name if self._history else None
        tstate = select_tardigrade(threat_level, signal)
        self.tstate = tstate
        self.doctrine = doctrine

        # Omega Lock — fail-closed execution gate
        try:
            self.lock.engage(doctrine, tstate, list(cfg.break_conditions))
            self.audit.append("LOCK", f"engaged|{tstate.value}")
        except OmegaLockError:
            self.audit.append(
                "LOCK",
                "fail-closed: RAGNAR_OMEGA_KEY absent — execution denied, drafting continues",
            )

        # Victory projection with interaction adjustment
        victory = compute_victory_projection(maneuver, self.model, dsup.score, cfg, self.rng)

        confidence = round(
            max(0.10, 0.95 * (0.85 + 0.15 * dsup.score) - penalty),
            4,
        )
        self.audit.append("PLAN", f"maneuver={maneuver.id}|confidence={confidence}")
        return Plan(
            threat=threat,
            spofs=tuple(spofs),
            maneuver=maneuver,
            doctrine=doctrine,
            tstate=tstate,
            documents=docs,
            dsup_score=dsup.score,
            confidence=confidence,
            victory_projection=victory,
            audit_root=self.audit.root,
        )

    # --------------------------------------------------------------- ingest
    def ingest_incoming(self, text: str) -> TripwireEvent | None:
        """Process opponent mail through the tripwire monitor (native Gen-5
        integration: the live threat feeds the Verjährung tick)."""
        days: int | None = None
        if self._last_threat is not None:
            model = calculate_verjaehrung(self._last_threat, (), self.cfg)
            if model is not None:
                days = days_to_verjaehrung(model)
        ev = self.monitor.check(text, self.tstate, days_to_verjaehrung=days)
        if ev is not None:
            self._history.append(ev)
            self.audit.append("TRIPWIRE", f"{ev.name}|{ev.severity.name}")
            if self.monitor.should_break_cryptobiosis(ev):
                self._tstate_backup = self.tstate
                self.tstate = TState.ACTIVE
                self.audit.append("REHYDRATE", ev.type.value)
        return ev

    # ------------------------------------------------------------ internals
    def _threat_level(self, threat: Threat, spofs: Sequence[SPOF]) -> float:
        level = 0.35 + 0.07 * max((s.severity for s in spofs), default=0)
        if threat.verjaehrung_date is not None:
            days = (threat.verjaehrung_date - date.today()).days
            if days < 0:
                level += 0.35  # phase transition complete
            elif days <= 90:
                level += 0.25
            else:
                level += 0.10
        else:
            level += 0.15  # unknown clock — priced honestly
        return min(1.0, level)

    @staticmethod
    def _ctx_from(threat: Threat) -> dict[str, str]:
        return {
            "mandant": "[offen]",
            "gegner": threat.opponent,
            "vertrag": threat.contract_number or "[offen]",
            "konto": threat.bank_account or "[offen]",
            "betrag": _german_amount(threat.claim),
            "datum": threat.threat_date.isoformat(),
            "rueckgabe": threat.rueckgabe_date.isoformat() if threat.rueckgabe_date else "[offen]",
            "gericht": "[offen]",
            "aktenzeichen": "[offen]",
            "anschrift": "[offen]",
            "rate": "[offen]",
            "verjaehrung": threat.verjaehrung_date.isoformat()
            if threat.verjaehrung_date
            else "[offen]",
            "sachverhalt": threat.basis or "[offen]",
        }

    # ------------------------------------------------------------ state I/O
    def save_state(self, path: str) -> None:
        """Persist orchestrator state (JSON). The audit trail rides along —
        the chain is the evidence."""
        import json

        payload = {
            "version": "33.0.0",
            "resources": self.resources,
            "tstate": self.tstate.value,
            "doctrine": self.doctrine.value,
            "model": {
                "belief": {t.value: v for t, v in self.model.belief.items()},
                "dark_horse": self.model.dark_horse,
                "rationality_weight": self.model.rationality_weight,
                "observations": self.model.observations,
            },
            "audit": self.audit.to_json(),
            "history": [e.to_json() for e in self._history],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)

    def load_state(self, path: str) -> None:
        """Restore orchestrator state. Round-trip fidelity is contract-tested."""
        import json

        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        from .gen1_foundation import AuditTrail as _AT

        self.resources = float(payload.get("resources", self.resources))
        self.tstate = TState(str(payload.get("tstate", self.tstate.value)))
        self.doctrine = Doctrine(str(payload.get("doctrine", self.doctrine.value)))
        model = payload.get("model", {})
        belief_raw: dict[str, float] = {
            str(k): float(v) for k, v in model.get("belief", {}).items()
        }
        self.model = OpponentModel(
            belief={t: belief_raw.get(t.value, 0.0) for t in OpponentType},
            dark_horse=float(model.get("dark_horse", 0.5)),
            rationality_weight=float(model.get("rationality_weight", 0.5)),
            observations=int(model.get("observations", 0)),
        )
        self.audit = _AT.from_json(payload.get("audit", []))
        self._history = [
            TripwireEvent(
                type=TripwireType(e["type"]),
                severity=Severity(int(e["severity"])),
                response=TripwireResponse(e["response"]),
                date=date.fromisoformat(e["date"]),
                detail=e.get("detail", ""),
            )
            for e in payload.get("history", [])
        ]

    # Observe outcomes → update the opponent model (Bayesian, dark horse decays)
    def observe_outcome(self, outcome: str, maneuver: Maneuver | None = None) -> None:
        m = maneuver or MANEUVERS[0]
        if self._last_threat is not None:
            self.model = update_opponent_model(
                self.model, outcome, m, self._last_threat.domain, self.cfg
            )
            self.audit.append("OBSERVE", f"{outcome}|rw={self.model.rationality_weight:.3f}")
