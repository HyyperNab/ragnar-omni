# GEN 1 — FOUNDATION: types, enums, threat serde, hash-chained audit trail.
"""RAGNAR Ω OMNI v33.0 — Gen 1: Foundation.

The frozen data model of the engine. Everything downstream reads these types;
nothing downstream may mutate them (frozen + slots kills the state-aliasing
bug class and makes attribute typos raise instead of silently passing).

Layer contract: imports stdlib only. Gen 1 is the bedrock — if it has a
dependency, the dependency is the SPOF.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
from dataclasses import dataclass, field, fields, replace
from datetime import UTC, date, datetime
from enum import IntEnum, StrEnum
from hashlib import sha256

__all__ = [
    "SPOF",
    "AuditEvent",
    "AuditTrail",
    "Channel",
    "Doctrine",
    "Domain",
    "Maneuver",
    "OpponentModel",
    "OpponentType",
    "Plan",
    "Severity",
    "TState",
    "Threat",
    "TripwireResponse",
    "TripwireType",
    "VerjaehrungEvent",
    "VerjaehrungEventType",
    "VictoryState",
    "get_logger",
    "threat_from_json",
]

_GENESIS = "GENESIS:0"


def get_logger(name: str) -> logging.Logger:
    """Namespaced logger with a null-safe default (library etiquette)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


# --------------------------------------------------------------------------- #
# Domains — the functor targets (v32.2 Dimension 8). JURISDICTION warnings for
# government (EC-6: no UKlaG morphism) and cross-border (EC-8: partial functor)
# are encoded as explicit flags consumed by the SPOF engine.
# --------------------------------------------------------------------------- #


class Domain(StrEnum):
    AUTO_ABO = "auto_abo"
    BANKING = "banking"
    INSURANCE = "insurance"
    TELECOM = "telecom"
    ENERGY = "energy"
    GOVERNMENT = "government"  # EC-6: regulatory object re-specified, not abandoned
    CROSS_BORDER = "cross_border"  # EC-8: partial functor — JURISDICTION_WARNING


class Severity(IntEnum):
    """Ordering is load-bearing: sorted(spofs, key=-severity) and gate checks."""

    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class TState(StrEnum):
    """Seven Tardigrade states. CRYPTO is the glass phase: minimum energy,
    structural integrity maintained, zero metabolic cost."""

    ACTIVE = "active"
    ALERT = "alert"
    TUN = "tun"
    CRYPTO = "crypto"
    ANHYDRO = "anhydro"
    LATENT = "latent"
    REVIVED = "revived"


class Doctrine(StrEnum):
    """The four riders. ZHUGE: let the opponent's own overhang destroy them."""

    HANNIBAL = "hannibal"  # decisive maneuver, high aggression
    ZHUGE = "zhuge"  # low-aggression, high-patience — the auto-abo default
    CAESAR = "caesar"  # tempo seizure
    FABIAN = "fabian"  # delay, attrition, let the clock work


class VictoryState(StrEnum):
    """Five-state victory model (I8): a win that costs more than it protects
    is scored as a loss. 'Won the case, lost the money' is a DEFEAT-class outcome."""

    TOTAL = "total"
    PARTIAL = "partial"
    PYRRHIC = "pyrrhic"
    STALEMATE = "stalemate"
    DEFEAT = "defeat"


class TripwireType(StrEnum):
    """Twelve semantic tripwires. Negations must not fire (C19 fix: threat-pattern
    AND defensive-pattern separation)."""

    KLAGE = "klage"
    KLAGEDROHUNG = "klagedrohung"
    MAHNBESCHEID = "mahnbescheid"
    SCHUFA = "schufa"
    INKASSO = "inkasso"
    SB_ATOMIZATION = "sb_atomization"
    VERJAERHRUNG_TICK = "verjaehrung_tick"
    SETTLEMENT_OFFER = "settlement_offer"
    GEGENDARSTELLUNG = "gegendarstellung"
    EINREICHUNGSVERBOT = "einreichungsverbot"
    ANERKENNTUNG = "anerkennung"
    GUTACHTEN_FORDERUNG = "gutachten_forderung"


class TripwireResponse(StrEnum):
    SILENCE = "silence"
    LOG_ONLY = "log_only"
    REHYDRATE = "rehydrate"
    COUNTER_ESCALATE = "counter_escalate"
    ACCEPT = "accept"


class Channel(StrEnum):
    """Channel Separation Doctrine (J5): deterrence through legal density,
    never through rhetoric. Court documents are written as if the judge WILL
    read them — because anything can become an exhibit."""

    OPPONENT_FACING = "opponent_facing"
    COURT_FACING = "court_facing"


class VerjaehrungEventType(StrEnum):
    """§ 204 Abs. 1 BGB Hemmung events (selected) + § 212 Neubeginn (ANERKENNTUNG)."""

    KLAGE = "klage"
    MAHNBESCHEID = "mahnbescheid"
    VERHANDLUNG = "verhandlung"
    ANERKENNTUNG = "anerkennung"  # Neubeginn (§ 212 Abs. 1 Nr. 2 BGB)
    VOLLSTRECKUNG = "vollstreckung"


class OpponentType(StrEnum):
    """Five known opponent archetypes. The sixth — the dark horse, the unknown
    type — is carried as a decaying scalar in OpponentModel, never as false certainty."""

    FLEET_PROVIDER = "fleet_provider"
    INKASSO_AGENT = "inkasso_agent"
    BANK = "bank"
    INSURER = "insurer"
    GOVERNMENT = "government"


# --------------------------------------------------------------------------- #
# Core data model — frozen, slotted, honest.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class SPOF:
    """A single point of failure found in the opponent's position.

    severity: legal leverage (5 = claim-killing).
    confidence: honest applicability price in [0,1] (I16 — never claim 1.0 on
    anything but statute-anchored logic).
    cascade: named downstream effects if exploited.
    """

    id: str
    code: str
    desc: str
    exploit: str
    severity: Severity
    confidence: float
    cascade: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerjaehrungEvent:
    """A limitation-clock event. end_date None → statutory default applies."""

    date: _dt.date  # module-qualified: the field name shadows the bare type
    type: VerjaehrungEventType
    end_date: _dt.date | None = None


@dataclass(frozen=True, slots=True)
class Threat:
    """The encoded threat vector (36-dim family, represented honestly)."""

    domain: Domain
    opponent: str
    claim: float
    basis: str
    contract_number: str = ""
    bank_account: str = ""
    threat_date: date = field(default_factory=date.today)
    verjaehrung_date: date | None = None
    rueckgabe_date: date | None = None
    is_consumer: bool = True
    agb_excerpt: str = ""
    correspondence: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        """JSON-primitive view (ISO dates, enum values). Round-trips via from_json."""
        return {
            "domain": self.domain.value,
            "opponent": self.opponent,
            "claim": self.claim,
            "basis": self.basis,
            "contract_number": self.contract_number,
            "bank_account": self.bank_account,
            "threat_date": self.threat_date.isoformat(),
            "verjaehrung_date": (
                self.verjaehrung_date.isoformat() if self.verjaehrung_date else None
            ),
            "rueckgabe_date": self.rueckgabe_date.isoformat() if self.rueckgabe_date else None,
            "is_consumer": self.is_consumer,
            "agb_excerpt": self.agb_excerpt,
            "correspondence": list(self.correspondence),
        }

    @classmethod
    def from_json(cls, data: dict[str, object] | str) -> Threat:
        """Strict serde: unknown domains raise ValueError (fail closed, exit code 2)."""
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, dict):
            raise TypeError("threat JSON must be an object")
        known = {f.name for f in fields(cls)}
        payload = {k: v for k, v in data.items() if k in known}

        dom_raw = str(payload.get("domain", "")).strip().lower()
        try:
            payload["domain"] = Domain(dom_raw)
        except ValueError as e:
            msg = f"unknown domain {dom_raw!r} — expected one of {[d.value for d in Domain]}"
            raise ValueError(msg) from e

        def _date(key: str) -> date | None:
            raw = payload.get(key)
            if raw in (None, ""):
                return None
            if isinstance(raw, date):
                return raw
            return date.fromisoformat(str(raw))

        payload["threat_date"] = _date("threat_date") or date.today()
        payload["verjaehrung_date"] = _date("verjaehrung_date")
        payload["rueckgabe_date"] = _date("rueckgabe_date")
        payload["is_consumer"] = bool(payload.get("is_consumer", True))
        raw_claim = payload.get("claim", 0.0)
        payload["claim"] = float(raw_claim) if isinstance(raw_claim, (int, float)) else 0.0
        corr = payload.get("correspondence", ())
        payload["correspondence"] = tuple(corr) if isinstance(corr, (list, tuple)) else ()
        return cls(**payload)  # type: ignore[arg-type]


def threat_from_json(data: dict[str, object] | str) -> Threat:
    """Function form of Threat.from_json (stable public API since v32.x)."""
    return Threat.from_json(data)


@dataclass(frozen=True, slots=True)
class Maneuver:
    """A deployable maneuver. cost_estimate is priced at the value it protects."""

    id: str
    name: str
    basis: str
    doctrine: Doctrine
    aggression: float = 0.5
    cost_estimate: float = 0.0


@dataclass(slots=True)
class OpponentModel:
    """Bayesian opponent model: 5 known types + decaying dark-horse mass (I13:
    institutional irrationality is blended in via rationality_weight, never ignored)."""

    belief: dict[OpponentType, float]
    dark_horse: float
    rationality_weight: float
    observations: int = 0

    @classmethod
    def uniform(cls, rationality_weight: float = 0.5) -> OpponentModel:
        n = len(OpponentType)
        return cls(
            belief=dict.fromkeys(OpponentType, 1.0 / n),
            dark_horse=0.5,
            rationality_weight=rationality_weight,
        )

    def most_likely(self) -> OpponentType:
        return max(self.belief, key=lambda t: self.belief[t])

    def with_update(
        self,
        belief: dict[OpponentType, float] | None = None,
        dark_horse: float | None = None,
        rationality_weight: float | None = None,
    ) -> OpponentModel:
        """Functional update — replace() with the fields we own."""
        return OpponentModel(
            belief=belief if belief is not None else dict(self.belief),
            dark_horse=self.dark_horse if dark_horse is None else dark_horse,
            rationality_weight=(
                self.rationality_weight if rationality_weight is None else rationality_weight
            ),
            observations=self.observations + 1,
        )


@dataclass(slots=True)
class Document:
    """A drafted legal document. spof_risk must be < 0.1 before emission
    (post-sterilization invariant, asserted by the test suite for all specs)."""

    body: str
    title: str = ""
    salutation: str = ""
    closing: str = ""
    citations: tuple[str, ...] = ()
    hash: str = ""
    tone_score: float = 1.0
    spof_risk: float = 0.0
    sterilization_passes: int = 0
    channel: Channel = Channel.OPPONENT_FACING
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class Plan:
    """The complete output of decide(): threat, weapons, move, state, price."""

    threat: Threat
    spofs: tuple[SPOF, ...]
    maneuver: Maneuver
    doctrine: Doctrine
    tstate: TState
    documents: tuple[Document, ...]
    dsup_score: float
    confidence: float
    victory_projection: dict[str, float]
    audit_root: str


# --------------------------------------------------------------------------- #
# Audit trail — hash-chained, timezone-aware. The trail is the evidence that
# the engine distrusts itself (the final SPOF patch, I16).
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class AuditEvent:
    type: str
    detail: str
    ts: str  # ISO-8601 UTC — DTZ-clean by construction
    prev: str
    hash: str


def _hash_event(prev: str, type_: str, detail: str, ts: str) -> str:
    return sha256(f"{prev}|{type_}|{detail}|{ts}".encode()).hexdigest()


class AuditTrail:
    """Append-only, hash-chained audit log. verify() detects any tampering."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, type_: str, detail: str) -> AuditEvent:
        ts = datetime.now(UTC).isoformat(timespec="seconds")
        prev = self.events[-1].hash if self.events else _GENESIS
        ev = AuditEvent(
            type=type_, detail=detail, ts=ts, prev=prev, hash=_hash_event(prev, type_, detail, ts)
        )
        self.events.append(ev)
        return ev

    @property
    def root(self) -> str:
        """Merkle-style root: last hash, or the genesis marker."""
        return self.events[-1].hash if self.events else _GENESIS

    def verify(self) -> bool:
        prev = _GENESIS
        for ev in self.events:
            if ev.prev != prev or ev.hash != _hash_event(prev, ev.type, ev.detail, ev.ts):
                return False
            prev = ev.hash
        return True

    def to_json(self) -> list[dict[str, str]]:
        return [
            {"type": e.type, "detail": e.detail, "ts": e.ts, "prev": e.prev, "hash": e.hash}
            for e in self.events
        ]

    @classmethod
    def from_json(cls, data: list[dict[str, str]]) -> AuditTrail:
        trail = cls()
        trail.events = [AuditEvent(**e) for e in data]
        return trail


# Convenience re-export used by orchestrator state serde.
_ = replace
