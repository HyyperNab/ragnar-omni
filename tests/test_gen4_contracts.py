# GEN 4 contracts — builders, tripwires, lock, self-audit, orchestrator.
"""Contract tests for the execution layer. The channel-separation invariants
(all docs sterile, court docs rhetoric-free, quarantine never emitted) are the
spirit checks — they must never regress."""

from __future__ import annotations

import re
from datetime import date, timedelta

import pytest

from ragnar.citations import quarantined_citations
from ragnar.config import default_cfg
from ragnar.gen1_foundation import (
    Doctrine,
    Domain,
    Severity,
    Threat,
    TripwireType,
    TState,
)
from ragnar.gen4_execution import (
    MANEUVERS,
    SPECS,
    OmegaLock,
    OmegaLockError,
    Ragnar,
    TripwireMonitor,
    build_document,
    judge_adoptability,
    self_audit,
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


_CTX = {
    "mandant": "M",
    "gegner": "G",
    "vertrag": "V",
    "konto": "K",
    "betrag": "1.000,00",
    "datum": "01.07.2026",
    "rueckgabe": "01.06.2026",
    "gericht": "AG",
    "aktenzeichen": "1 O 1/26",
    "anschrift": "X",
    "rate": "100,00",
    "verjaehrung": "01.01.2027",
    "sachverhalt": "y",
}


def test_all_eight_specs_exist() -> None:
    assert len(SPECS) == 8
    assert set(SPECS) == {
        "bestreiten_sperre",
        "verjaehrungseinrede",
        "methodology_defense",
        "schufa_unterlassung",
        "abtretungsverbot_defense",
        "systemic_exposure",
        "feststellungsklage",
        "klageerwiderung",
    }


def test_all_eight_docs_sterile_under_full_ctx() -> None:
    for sid in SPECS:
        doc = build_document(sid, _CTX)
        assert doc.spof_risk < 0.1, f"{sid} failed sterilization: {doc.spof_risk}"
        assert doc.body, sid
        assert doc.hash, sid
        assert doc.citations, sid


def test_court_docs_carry_no_rhetoric() -> None:
    for sid in SPECS:
        doc = build_document(sid, _CTX)
        assert "Blöße" not in doc.body
        assert "!!" not in doc.body


def test_court_docs_citations_confirmed_only() -> None:
    for sid, spec in SPECS.items():
        if spec.channel.value != "court_facing":
            continue
        doc = build_document(sid, _CTX)
        for c in doc.citations:
            assert not re.search(r"NJW 2007|178/85|168/24|9301/96|513/98", c), (
                f"quarantined citation leaked into {sid}: {c}"
            )


def test_quarantine_never_emitted_anywhere() -> None:
    for sid in SPECS:
        doc = build_document(sid, _CTX)
        joined = " ".join(doc.citations)
        for q in quarantined_citations():
            needle = q["text"].split("(")[0].strip()[:24]
            assert needle not in joined, f"quarantine leak in {sid}"


def test_polymorphism_permutes_citations_not_substance() -> None:
    a = build_document("bestreiten_sperre", _CTX, seed=1)
    b = build_document("bestreiten_sperre", _CTX, seed=2)
    same_set = set(a.citations) == set(b.citations)
    assert same_set  # substance identical
    # a permuted order is possible; hashes differ when order differs
    if list(a.citations) != list(b.citations):
        assert a.hash != b.hash


def test_missing_ctx_renders_offen_not_crash() -> None:
    doc = build_document("feststellungsklage", {"gegner": "G"})
    assert "[offen]" in doc.body


def test_judge_adoptability_bounded_and_positive() -> None:
    for sid in SPECS:
        score = judge_adoptability(build_document(sid, _CTX))
        assert 0.0 < score <= 1.0


def test_self_audit_flags_overreach_without_evidence() -> None:
    aggressive = next(m for m in MANEUVERS if m.id == "WIDERKLAGE")
    findings = self_audit(aggressive, _t())  # no correspondence corpus
    assert any(f.code == "SELF_OVERREACH" for f in findings)


def test_self_audit_clean_on_modest_maneuver() -> None:
    silence = next(m for m in MANEUVERS if m.id == "SILENCE")
    assert self_audit(silence, _t()) == []


def test_self_audit_flags_bad_iban() -> None:
    silence = next(m for m in MANEUVERS if m.id == "SILENCE")
    bad = _t(bank_account="DE00BROKEN123")
    assert any(f.code == "SELF_DATA_QUALITY" for f in self_audit(silence, bad))


def test_tripwire_klage_fires_critical() -> None:
    ev = TripwireMonitor().check("Klage wird erhoben.", TState.CRYPTO)
    assert ev is not None and ev.type is TripwireType.KLAGE
    assert ev.severity == Severity.CRITICAL
    assert TripwireMonitor().should_break_cryptobiosis(ev)


def test_tripwire_negation_guard() -> None:
    ev = TripwireMonitor().check("Wir bestätigen: keine SCHUFA-Meldung erfolgt.", TState.CRYPTO)
    assert ev is None or ev.type is not TripwireType.SCHUFA


def test_tripwire_sb_atomization() -> None:
    text = (
        "Rechnung: Selbstbeteiligung 1.000,00 EUR; "
        "Selbstbeteiligung 750,00 EUR; Selbstbeteiligung 1.000,00 EUR."
    )
    ev = TripwireMonitor().check(text, TState.CRYPTO)
    assert ev is not None and ev.type is TripwireType.SB_ATOMIZATION


def test_tripwire_verjaehrung_tick_needs_days() -> None:
    m = TripwireMonitor()
    assert m.check("Sehr geehrte Damen und Herren.", TState.CRYPTO) is None
    ev = m.check("Sehr geehrte Damen und Herren.", TState.CRYPTO, days_to_verjaehrung=10)
    assert ev is not None and ev.type is TripwireType.VERJAERHRUNG_TICK


def test_tripwire_settlement_offer_breaks() -> None:
    ev = TripwireMonitor().check(
        "Wir unterbreiten Ihnen folgendes Vergleichsangebot.", TState.CRYPTO
    )
    assert ev is not None and ev.type is TripwireType.SETTLEMENT_OFFER
    assert TripwireMonitor().should_break_cryptobiosis(ev)


def test_lock_fail_closed_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAGNAR_OMEGA_KEY", raising=False)
    ol = OmegaLock()
    with pytest.raises(OmegaLockError, match="fail-closed"):
        ol.engage(Doctrine.ZHUGE, TState.CRYPTO, ["KLAGE"])


def test_lock_cycle_and_replay() -> None:
    ol = OmegaLock()
    assert ol.engage(Doctrine.ZHUGE, TState.CRYPTO, ["KLAGE"])
    assert ol.unlock(TripwireType.KLAGE, nonce="n1") is True
    assert ol.engage(Doctrine.ZHUGE, TState.CRYPTO, ["KLAGE"])
    assert ol.unlock(TripwireType.KLAGE, nonce="n1") is False  # replay dead
    assert ol.unlock(TripwireType.KLAGE, nonce="n2") is True


def test_lock_wrong_condition_rejected() -> None:
    ol = OmegaLock()
    assert ol.engage(Doctrine.ZHUGE, TState.CRYPTO, ["KLAGE"])
    assert ol.unlock(TripwireType.SETTLEMENT_OFFER, nonce="x") is False
    assert ol.engaged is True


def test_decide_returns_validated_plan() -> None:
    r = Ragnar(resources=10.0)
    plan = r.decide(_t())
    assert plan.spofs, "SPOF constellation must not be empty for a quant claim"
    assert plan.confidence > 0
    assert abs(sum(plan.victory_projection.values()) - 1.0) < 1e-6
    assert plan.documents
    assert r.audit.verify()


def test_decide_chooses_low_aggression_for_running_clock() -> None:
    plan = Ragnar().decide(_t())  # verjaehrung 90 days out, COLLECTION-style opponent
    assert plan.doctrine in (Doctrine.ZHUGE, Doctrine.FABIAN)


def test_ingest_rehydrates_on_klage() -> None:
    r = Ragnar()
    r.decide(_t())
    ev = r.ingest_incoming("Hiermit wird Klage erhoben.")
    assert ev is not None and ev.type is TripwireType.KLAGE
    assert r.tstate is TState.ACTIVE


def test_ingest_silence_stays_crypto() -> None:
    r = Ragnar()
    r.decide(_t())
    ev = r.ingest_incoming("Wir nehmen Ihr Schreiben zur Kenntnis.")
    assert ev is None
    assert r.tstate is TState.CRYPTO


def test_state_roundtrip(tmp_path) -> None:
    r1 = Ragnar(resources=10.0)
    r1.decide(_t())
    r1.ingest_incoming("Mahnbescheid wurde am 01.08.2026 zugestellt.")
    p = str(tmp_path / "state.json")
    r1.save_state(p)
    r2 = Ragnar(resources=1.0)
    r2.load_state(p)
    assert r2.tstate == r1.tstate
    assert r2.doctrine == r1.doctrine
    assert r2.model.belief == r1.model.belief
    assert r2.audit.verify()


def test_break_conditions_are_the_lock_conditions() -> None:
    cfg = default_cfg()
    assert set(cfg.break_conditions) == {"KLAGE", "SCHUFA", "VERJAERHRUNG_TICK", "SETTLEMENT_OFFER"}
