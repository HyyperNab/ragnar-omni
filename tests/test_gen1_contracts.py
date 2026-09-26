# GEN 1 contracts — foundation types, serde, audit chain.
"""Contract tests for the foundation layer (Lagom protocol: tests first, then modules)."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from ragnar.gen1_foundation import (
    AuditTrail,
    Doctrine,
    Domain,
    OpponentModel,
    OpponentType,
    Severity,
    Threat,
    TState,
    VerjaehrungEvent,
    VerjaehrungEventType,
    VictoryState,
    threat_from_json,
)


def test_threat_serde_roundtrip() -> None:
    t = Threat(
        domain=Domain.AUTO_ABO,
        opponent="DFD",
        claim=2100.0,
        basis="§ 249 BGB",
        contract_number="VR-1",
        bank_account="DE89370501981234567890",
        threat_date=date(2026, 6, 1),
        verjaehrung_date=date(2026, 12, 1),
        correspondence=("Mahnung 1", "Mahnung 2"),
    )
    restored = threat_from_json(json.dumps(t.to_json()))
    assert restored == t


def test_threat_minimal_json_defaults() -> None:
    t = threat_from_json({"domain": "auto_abo", "opponent": "X", "claim": 100.0, "basis": "b"})
    assert t.domain is Domain.AUTO_ABO
    assert t.is_consumer is True
    assert t.verjaehrung_date is None
    assert t.threat_date == date.today()


def test_threat_unknown_domain_rejected() -> None:
    with pytest.raises(ValueError, match="unknown domain"):
        threat_from_json({"domain": "nonsense", "opponent": "X", "claim": 1.0, "basis": "b"})


def test_seven_tardigrade_states() -> None:
    assert len(TState) == 7
    assert TState.CRYPTO.value == "crypto"


def test_severity_ordering_is_load_bearing() -> None:
    assert Severity.CRITICAL > Severity.HIGH > Severity.MEDIUM > Severity.LOW > Severity.INFO


def test_victory_states_are_five() -> None:
    assert len(VictoryState) == 5
    assert {v.value for v in VictoryState} == {"total", "partial", "pyrrhic", "stalemate", "defeat"}


def test_audit_chain_verifies_and_detects_tampering() -> None:
    trail = AuditTrail()
    trail.append("INGEST", "a")
    trail.append("SPOF", "b")
    assert trail.verify() is True
    trail.events[1] = trail.events[1].__class__(
        type="SPOF",
        detail="TAMPERED",
        ts=trail.events[1].ts,
        prev=trail.events[1].prev,
        hash=trail.events[1].hash,
    )
    assert trail.verify() is False


def test_audit_trail_roundtrip() -> None:
    trail = AuditTrail()
    trail.append("A", "1")
    trail.append("B", "2")
    restored = AuditTrail.from_json(trail.to_json())
    assert restored.verify() is True
    assert restored.root == trail.root


def test_opponent_model_uniform() -> None:
    m = OpponentModel.uniform()
    assert abs(sum(m.belief.values()) - 1.0) < 1e-9
    assert set(m.belief) == set(OpponentType)
    assert m.dark_horse == 0.5


def test_verjaehrung_event_frozen() -> None:
    ev = VerjaehrungEvent(date=date(2026, 1, 1), type=VerjaehrungEventType.KLAGE)
    with pytest.raises(AttributeError):
        ev.date = date(2027, 1, 1)  # type: ignore[misc]


def test_doctrine_members() -> None:
    assert {d.value for d in Doctrine} == {"hannibal", "zhuge", "caesar", "fabian"}


def test_threat_date_string_and_timedelta_paths() -> None:
    t = threat_from_json(
        {
            "domain": "banking",
            "opponent": "B",
            "claim": 10.0,
            "basis": "x",
            "verjaehrung_date": "2026-08-01",
        }
    )
    assert t.verjaehrung_date == date(2026, 8, 1)
    assert t.threat_date == date.today()


def test_genesis_root_before_events() -> None:
    assert AuditTrail().root == "GENESIS:0"


def test_recent_deadline_encoding() -> None:
    t = threat_from_json(
        {
            "domain": "auto_abo",
            "opponent": "X",
            "claim": 1.0,
            "basis": "b",
            "verjaehrung_date": None,
            "threat_date": (date.today() - timedelta(days=10)).isoformat(),
        }
    )
    assert t.threat_date < date.today()
