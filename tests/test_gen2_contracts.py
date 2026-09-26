# GEN 2 contracts — SPOF engine, sterilization, DSUP, Tardigrade.
"""Contract tests for the analysis layer."""

from __future__ import annotations

from datetime import date, timedelta

from ragnar.config import default_cfg
from ragnar.gen1_foundation import Document, Domain, Severity, Threat, TState
from ragnar.gen2_analysis import (
    DOMAINS,
    analyze_spofs_universal,
    crypto_viability,
    detect_violations,
    dsup_shield,
    recursive_sterilize,
    select_tardigrade,
)


def _t(**kw) -> Threat:
    base: dict = {
        "domain": Domain.AUTO_ABO,
        "opponent": "DFD",
        "claim": 2100.0,
        "basis": "§ 249 BGB",
        "contract_number": "VR-12345",
        "bank_account": "DE02120300000000202051",  # mod-97 valid sample
        "threat_date": date(2026, 6, 1),
        "verjaehrung_date": date.today() + timedelta(days=90),
    }
    base.update(kw)
    return Threat(**base)


def test_spof_universe_is_the_deduplicated_eleven() -> None:
    codes = {s.code for s in analyze_spofs_universal(_t(), True, ["x"] * 5, None)}
    expected = {
        "EVIDENTIARY_ROOT",
        "CALCULATION_METHODOLOGY",
        "PROCESSING_BLOCK_ACCRUAL",
        "TEMPORAL_DECAY",
        "TAX_PHANTOM",
        "AGB_ISOLATION_VOID",
        "LOGISTICS_PHANTOM",
        "SYSTEMIC_REGULATORY",
        "BUSINESS_MODEL_DEPENDENCY",
        "NETWORK_EDGE_FRICTION",
        "ESCALATION_VELOCITY_BLINDNESS",
    }
    assert codes & expected == codes  # no invented codes
    assert "EVIDENTIARY_ROOT" in codes
    # GATED weapons must respect their gates
    assert "TAX_PHANTOM" not in codes  # no USt text in incoming
    assert "AGB_ISOLATION_VOID" in codes  # consumer + agb_present


def test_spof_severity_sorted_and_confident() -> None:
    spofs = analyze_spofs_universal(_t(), True, ["x"] * 5, None)
    assert spofs == sorted(spofs, key=lambda s: -s.severity)
    assert all(0.0 < s.confidence <= 1.0 for s in spofs)
    assert all(s.cascade for s in spofs)


def test_spof_o9_is_heuristic_tier() -> None:
    spofs = analyze_spofs_universal(_t(), False, [], None)
    o9 = [s for s in spofs if s.code == "BUSINESS_MODEL_DEPENDENCY"]
    assert o9 and o9[0].severity <= Severity.LOW and o9[0].confidence <= 0.5


def test_spof_jurisdiction_warning_rides_for_exotic_domains() -> None:
    t = _t(domain=Domain.GOVERNMENT)
    assert any(
        s.code == "JURISDICTION_WARNING" for s in analyze_spofs_universal(t, False, [], None)
    )
    t2 = _t(domain=Domain.CROSS_BORDER)
    assert any(
        s.code == "JURISDICTION_WARNING" for s in analyze_spofs_universal(t2, False, [], None)
    )


def test_domain_registry_covers_all_domains() -> None:
    assert set(DOMAINS) == set(Domain)


def test_sterilize_drops_rhetoric_and_keeps_substance() -> None:
    doc = Document(
        body=(
            "Die Forderung wird bestritten. Sie sind KORRUPT!!! Dies ist ein Skandal. "
            "Die Berechnung enthält keinen Neu-für-Alt-Abzug."
        )
    )
    clean = recursive_sterilize(doc)
    assert detect_violations(clean.body) == []
    assert "Neu-für-Alt-Abzug" in clean.body  # substance survives
    assert "bestritten" in clean.body


def test_sterilize_assembles_salutation_and_closing() -> None:
    doc = Document(
        body="Sachlich bleiben.",
        salutation="Sehr geehrte Damen und Herren,",
        closing="Mit freundlichen Grüßen",
    )
    clean = recursive_sterilize(doc)
    assert "Sehr geehrte Damen und Herren" in clean.body
    assert "Mit freundlichen Grüßen" in clean.body


def test_sterilize_converges_within_five_passes() -> None:
    clean = recursive_sterilize(Document(body="Sauber von Anfang an."))
    assert 1 <= clean.sterilization_passes <= 5
    assert clean.spof_risk < 0.1


def test_detect_violations_flags_known_fingerprints() -> None:
    assert detect_violations("empirisch zu erproben") != []
    assert detect_violations("Widerwärtig!") != []
    assert detect_violations("Die DSGVO gilt.") == []  # whitelisted acronym
    assert detect_violations("SCHUFA-Meldung") == []  # whitelisted acronym


def test_dsup_bounded_and_citation_backed() -> None:
    res = dsup_shield(_t(), analyze_spofs_universal(_t(), True, ["x"] * 5, None))
    assert 0.0 <= res.score <= 1.0
    assert res.citations_used  # CONFIRMED bedrock exists
    empty = dsup_shield(_t(), [])
    assert empty.score == 0.5  # honest neutral


def test_tardigrade_thresholds() -> None:
    assert select_tardigrade(0.95, None) is TState.CRYPTO
    assert select_tardigrade(0.95, "SCHUFA") is TState.ACTIVE
    assert select_tardigrade(0.6, None) is TState.TUN
    assert select_tardigrade(0.2, None) is TState.ACTIVE


def test_crypto_viability_clock_and_stakes() -> None:
    expired = crypto_viability(_t(verjaehrung_date=date.today() - timedelta(days=10)))
    running = crypto_viability(_t())
    unknown = crypto_viability(_t(verjaehrung_date=None))
    assert expired > running > 0.0
    assert 0.0 <= unknown <= 1.0


def test_o3_gate_respects_cfg() -> None:
    cfg = default_cfg()
    assert cfg.o3_min_events == 3
    codes = {s.code for s in analyze_spofs_universal(_t(), False, ["a", "b"], None)}
    assert "PROCESSING_BLOCK_ACCRUAL" not in codes
