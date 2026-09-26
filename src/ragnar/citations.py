# EPISTEMIC LAYER — Citation supply chain with zero trust, including zero trust in itself.
"""CitationTrust tiers and the verified-citation registry (v33.0 internal SPOFs I1/I2).

The load-bearing rule: the STATUTE carries the weight, cases corroborate, never the
inverse. Every citation ships with a trust tier; anything below PROBABLE is
quarantined and can never be emitted by any document builder. Court-facing
documents require CONFIRMED tier only.

Registry source of truth: ``ragnar/data/CITATIONS_VERIFIED.json`` (packaged),
reverify date 2027-01-27 — a production calendar obligation, not a comment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import IntEnum
from functools import lru_cache
from importlib import resources
from typing import Any

__all__ = [
    "COURT_DOCUMENT_MINIMUM",
    "LETTER_MINIMUM",
    "CitationRecord",
    "CitationTrust",
    "citation_confidence",
    "emit_citations",
    "quarantined_citations",
    "registry",
    "reverify_due",
]


class CitationTrust(IntEnum):
    """Trust tiers. The engine's deepest SPOF was trusting confident output."""

    QUARANTINED = 0  # never emitted — fabrication-adjacent, superseded, or unverified details
    SUSPECT = 1  # fabrication markers: weekend dates, wrong senate, hyper-specific narratives
    UNVERIFIED = 2  # generated in-session, not cross-checked
    PROBABLE = 3  # format/doctrine consistent, single-source
    CONFIRMED = 4  # statutes + landmark cases, multi-source / primary-source verified


COURT_DOCUMENT_MINIMUM = CitationTrust.CONFIRMED
LETTER_MINIMUM = CitationTrust.PROBABLE  # außergerichtlich


@dataclass(frozen=True, slots=True)
class CitationRecord:
    """One citation with its epistemic price tag attached (I16: uncertainty is priced)."""

    text: str
    tier: CitationTrust
    kind: str  # statute | case | market
    source: str = ""
    note: str = ""

    @property
    def confidence(self) -> float:
        """Honest confidence per kind: statutes are bedrock, cases corroborate,
        market evidence is heuristic — never load-bearing in court."""
        base = {
            "statute": 0.95,
            "case": 0.90,
            "market": 0.60,
        }.get(self.kind, 0.50)
        # Tier discount: below CONFIRMED the price rises on every channel
        if self.tier < CitationTrust.CONFIRMED:
            return base * (0.55 + 0.1125 * int(self.tier))
        return base


@dataclass(frozen=True, slots=True)
class CitationRegistry:
    """Immutable view over the packaged registry JSON."""

    meta: dict[str, Any]
    topics: dict[str, tuple[CitationRecord, ...]]
    quarantine: tuple[dict[str, str], ...]

    def emit(self, topic: str, minimum: CitationTrust) -> tuple[CitationRecord, ...]:
        """Trust-gated emission. Quarantined entries are structurally unreachable."""
        records = self.topics.get(topic, ())
        return tuple(r for r in records if r.tier >= minimum)

    def reverify_after(self) -> date:
        raw = str(self.meta.get("reverify_after", "2027-01-27"))
        return datetime.strptime(raw, "%Y-%m-%d").date()  # noqa: DTZ007 — date, not datetime


@lru_cache(maxsize=1)
def _load() -> CitationRegistry:
    ref = resources.files("ragnar").joinpath("data/CITATIONS_VERIFIED.json")
    raw: dict[str, Any] = json.loads(ref.read_text(encoding="utf-8"))
    topics: dict[str, tuple[CitationRecord, ...]] = {}
    for topic, entries in raw.get("citations", {}).items():
        topics[topic] = tuple(
            CitationRecord(
                text=str(e["text"]),
                tier=CitationTrust(int(e["tier"])),
                kind=str(e.get("kind", "case")),
                source=str(e.get("source", "")),
                note=str(e.get("note", "")),
            )
            for e in entries
        )
    return CitationRegistry(
        meta=dict(raw.get("meta", {})),
        topics=topics,
        quarantine=tuple(raw.get("quarantine", [])),
    )


def registry() -> CitationRegistry:
    """The frozen registry (cached). Single source of truth, packaged with the wheel."""
    return _load()


def reverify_due(today: date | None = None) -> bool:
    """True once the legal bedrock's shelf life has expired — production must act."""
    today = today or datetime.now(UTC).date()
    return today >= registry().reverify_after()


def emit_citations(topic: str, court: bool = False) -> tuple[str, ...]:
    """Emit citation TEXTS for a topic, gated by channel floor.

    Court-facing: CONFIRMED only. Letters: at least PROBABLE.
    QUARANTINED/SUSPECT/UNVERIFIED are structurally unreachable — the fix for I1/I2.
    """
    floor = COURT_DOCUMENT_MINIMUM if court else LETTER_MINIMUM
    return tuple(r.text for r in registry().emit(topic, floor))


def citation_confidence(topic: str, court: bool = False) -> float:
    """Weakest-link confidence across emitted citations (never overclaim)."""
    floor = COURT_DOCUMENT_MINIMUM if court else LETTER_MINIMUM
    emitted = registry().emit(topic, floor)
    if not emitted:
        return 0.0
    return min(r.confidence for r in emitted)


def quarantined_citations() -> tuple[dict[str, str], ...]:
    """Transparency API: the quarantine list is public to the operator (never to courts)."""
    return registry().quarantine
