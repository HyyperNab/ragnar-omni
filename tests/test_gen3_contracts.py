# GEN 3 contracts — causal, NPV, Verjährung, Nash, opponent model, victory.
"""Contract tests for the strategy layer. Seeded determinism throughout."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from ragnar.config import default_cfg
from ragnar.gen1_foundation import (
    Doctrine,
    Domain,
    Maneuver,
    OpponentModel,
    Threat,
    VerjaehrungEvent,
    VerjaehrungEventType,
    VictoryState,
)
from ragnar.gen3_strategy import (
    CausalGraph,
    calculate_verjaehrung,
    compute_victory_projection,
    compute_victory_value,
    days_to_verjaehrung,
    escalation_velocity,
    lagom_solve_nash,
    npv_path_dependent,
    statute_expired,
    update_opponent_model,
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


class _Ev:
    def __init__(self, d: date) -> None:
        self.date = d


def test_causal_shape_reachability_and_sum() -> None:
    d = CausalGraph("DEMAND_REFUND").propagate(8000)
    assert set(d) == {"fold", "sue", "regulatory", "stall"}
    assert abs(sum(d.values()) - 1.0) < 1e-9
    assert all(v > 0 for v in d.values())


def test_causal_silence_stall_dominant() -> None:
    d = CausalGraph("SILENCE").propagate(5000)
    assert d["stall"] == max(d.values())


def test_causal_seeded_determinism() -> None:
    a = CausalGraph("SILENCE").propagate(1000)
    b = CausalGraph("SILENCE").propagate(1000)
    assert a == b


def test_causal_unknown_profile_fails_loud() -> None:
    with pytest.raises(KeyError, match="registry-locked"):
        CausalGraph("NOT_A_PROFILE")


def test_escalation_velocity_detects_shrinking_cadence() -> None:
    events = [_Ev(date(2026, 1, 1)), _Ev(date(2026, 1, 15)), _Ev(date(2026, 1, 25))]
    assert escalation_velocity(events) > 0  # 14 → 10 days: a human took over
    assert escalation_velocity([]) == 0.0
    assert escalation_velocity([_Ev(date(2026, 1, 1))]) == 0.0


def test_verjaehrung_hemmung_pauses_the_clock() -> None:
    base = _t(verjaehrung_date=None, threat_date=date(2024, 1, 1))
    plain = calculate_verjaehrung(base, ())
    hemmed = calculate_verjaehrung(
        base,
        (
            VerjaehrungEvent(
                date=date(2024, 6, 1), type=VerjaehrungEventType.KLAGE, end_date=date(2024, 12, 1)
            ),
        ),
    )
    assert plain is not None and hemmed is not None
    assert hemmed.expiry_date > plain.expiry_date
    assert hemmung_days_check(hemmed) > 0


def hemmung_days_check(model) -> int:
    return model.hemmung_days


def test_verjaehrung_neubeginn_on_anerkennung() -> None:
    base = _t(verjaehrung_date=None, threat_date=date(2024, 1, 1))
    model = calculate_verjaehrung(
        base, (VerjaehrungEvent(date=date(2024, 5, 1), type=VerjaehrungEventType.ANERKENNTUNG),)
    )
    plain = calculate_verjaehrung(base, ())
    assert model is not None and plain is not None
    assert model.expiry_date > plain.expiry_date  # § 212: full restart


def test_days_to_verjaehrung_signed() -> None:
    model = calculate_verjaehrung(_t(verjaehrung_date=date.today() - timedelta(days=5)), ())
    assert model is not None
    assert days_to_verjaehrung(model) < 0


def test_statute_expired_binary_flag() -> None:
    assert statute_expired(_t(verjaehrung_date=date.today() - timedelta(days=10))) is True
    assert statute_expired(_t()) is False
    assert statute_expired(_t(verjaehrung_date=None)) is False  # unknown: never claim death


def test_npv_rational_opponents_fold_earlier() -> None:
    m = Maneuver("SILENCE", "m", "b", Doctrine.ZHUGE, cost_estimate=100.0)
    high = npv_path_dependent(m, OpponentModel.uniform(rationality_weight=0.95))
    low = npv_path_dependent(m, OpponentModel.uniform(rationality_weight=0.05))
    assert high > low


def test_npv_seed_makes_it_deterministic() -> None:
    m = Maneuver("SILENCE", "m", "b", Doctrine.ZHUGE, cost_estimate=100.0)
    a = npv_path_dependent(m, OpponentModel.uniform(), n_paths=500)
    b = npv_path_dependent(m, OpponentModel.uniform(), n_paths=500)
    assert a == b


def test_victory_value_matrix() -> None:
    assert compute_victory_value(VictoryState.TOTAL, 2000, 500, 400) == 1900
    assert compute_victory_value(VictoryState.PYRRHIC, 500, 2000, 0) < 0
    assert compute_victory_value(VictoryState.DEFEAT, 1000, 200, 0) < 0
    assert compute_victory_value(VictoryState.STALEMATE, 1000, 200, 0) < 0


def test_victory_projection_five_states_sum_one() -> None:
    m = Maneuver("SILENCE", "m", "b", Doctrine.ZHUGE)
    proj = compute_victory_projection(
        m, OpponentModel.uniform(), 0.8, default_cfg(), np.random.default_rng(0)
    )
    assert set(proj) == {"total", "partial", "pyrrhic", "stalemate", "defeat"}
    assert abs(sum(proj.values()) - 1.0) < 1e-6


def test_lagom_nash_clock_makes_patience_dominant() -> None:
    # the ZHUGE condition derived, not felt: a running § 548 clock raises patience
    p_with_clock, _ = lagom_solve_nash(0.5, 2100.0, 800.0, clock_value=0.9)
    p_no_clock, _ = lagom_solve_nash(0.5, 2100.0, 800.0, clock_value=0.0)
    assert 0.0 <= p_with_clock <= 1.0 and 0.0 <= p_no_clock <= 1.0
    assert p_with_clock < p_no_clock


def test_opponent_model_bayesian_update() -> None:
    m0 = OpponentModel.uniform()
    m1 = update_opponent_model(
        m0, "SUE", Maneuver("m", "m", "b", Doctrine.HANNIBAL), Domain.BANKING
    )
    assert abs(sum(m1.belief.values()) - 1.0) < 1e-6
    # BANK + SUE + BANKING domain affinity: BANK posterior must rise
    bank = _bank()
    assert m1.belief[bank] > m0.belief[bank]
    m2 = update_opponent_model(
        m1, "SUE", Maneuver("m", "m", "b", Doctrine.HANNIBAL), Domain.BANKING
    )
    assert m2.dark_horse <= m1.dark_horse + 1e-9  # dark horse only decays


def _bank():
    from ragnar.gen1_foundation import OpponentType

    return OpponentType.BANK


def test_opponent_observations_increment() -> None:
    m0 = OpponentModel.uniform()
    m1 = update_opponent_model(m0, "FOLD", Maneuver("m", "m", "b", Doctrine.ZHUGE), Domain.AUTO_ABO)
    assert m1.observations == m0.observations + 1
