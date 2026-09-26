# GEN 3 — STRATEGY: causal graphs, NPV, Verjährung, Nash-Lagom, opponent model.
"""RAGNAR Ω OMNI v33.0 — Gen 3: Strategy Layer.

Engineering honesty: RAGNAR is a decision engine, not a simulation engine.
There are exactly two hot loops in the architecture — both Monte Carlo — and
both vectorize completely (searchsorted / matrix masks). The branch-reachability
bug class from v30 dies as a property of the cumsum. numpy is paid for
DETERMINISM (seeded, injectable RNG), not milliseconds — stated plainly.

Layer contract: imports gen1 + config + numpy. Never gen2/gen4.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import pairwise
from typing import assert_never

import numpy as np

from .config import RagnarConfig, default_cfg
from .gen1_foundation import (
    Doctrine,
    Domain,
    Maneuver,
    OpponentModel,
    OpponentType,
    Threat,
    VerjaehrungEvent,
    VerjaehrungEventType,
    VictoryState,
)

__all__ = [
    "CausalGraph",
    "CausalProfile",
    "VerjaehrungModel",
    "calculate_verjaehrung",
    "compute_victory_projection",
    "compute_victory_value",
    "days_to_verjaehrung",
    "escalation_velocity",
    "lagom_solve_nash",
    "npv_path_dependent",
    "statute_expired",
    "update_opponent_model",
]

OUTCOMES = ("fold", "sue", "regulatory", "stall")


# --------------------------------------------------------------------------- #
# Causal profiles — 8 maneuver outcome distributions (data, not code)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CausalProfile:
    """Outcome distribution for a maneuver.

    p_bot_success:  P(the file stays pure-bot — no human ever touches it)
    p_human_if_bot:  P(a human eventually takes over | bot path)
    p_human_else:    P(human handling | immediately human) — structurally ~1.0
    Outcome draw applies only when a human is in the loop; the bot path stalls.
    """

    p_fold: float
    p_sue: float
    p_regulatory: float
    p_stall: float
    p_bot_success: float
    p_human_if_bot: float
    p_human_else: float = 1.0

    def __post_init__(self) -> None:
        total = self.p_fold + self.p_sue + self.p_regulatory + self.p_stall
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            msg = f"profile probabilities sum to {total}, expected 1.0"
            raise ValueError(msg)


PROFILES: dict[str, CausalProfile] = {
    # ZHUGE default: the clock works, the bot stalls, silence compounds
    "SILENCE": CausalProfile(0.30, 0.10, 0.05, 0.55, 0.60, 0.10),
    # A pointed letter forces a human decision
    "DEMAND_REFUND": CausalProfile(0.45, 0.20, 0.15, 0.20, 0.30, 0.40),
    # The Scalpel: costly signal, model-update imposed on the opponent
    "SCALPEL_LETTER": CausalProfile(0.55, 0.20, 0.10, 0.15, 0.25, 0.55),
    # Hub attack: network-wide blast radius, single-case probability is not the value
    "REGULATORY_DOSSIER": CausalProfile(0.25, 0.10, 0.35, 0.30, 0.50, 0.30),
    # Pre-emption: seize tempo, set the anchor (J2)
    "FESTSTELLUNGSKLAGE": CausalProfile(0.35, 0.30, 0.15, 0.20, 0.05, 0.20),
    # Burden-shift letter: O2 deployed, no counter-evidence needed
    "GEGENERKLAERUNG": CausalProfile(0.50, 0.15, 0.10, 0.25, 0.30, 0.35),
    # The clock IS the weapon: claim dies by § 548
    "VERJAERHRUNGSEINREDE": CausalProfile(0.85, 0.05, 0.02, 0.08, 0.55, 0.15),
    # GDPR counter-attack: § 840 edge friction, Art. 82 accrual
    "WIDERKLAGE": CausalProfile(0.40, 0.25, 0.15, 0.20, 0.20, 0.40),
}


class CausalGraph:
    """Monte Carlo outcome model, fully vectorized (searchsorted — one pass)."""

    def __init__(self, profile_id: str, cfg: RagnarConfig | None = None) -> None:
        try:
            self.profile = PROFILES[profile_id]
        except KeyError as e:
            msg = f"unknown causal profile {profile_id!r} — registry-locked (fail loud)"
            raise KeyError(msg) from e
        self.cfg = cfg or default_cfg()

    def propagate(
        self, iterations: int | None = None, rng: np.random.Generator | None = None
    ) -> dict[str, float]:
        """Vectorized outcome draw. Seeded by default — tests assert on distributions."""
        n = iterations if iterations is not None else self.cfg.mc_iterations
        rng = rng if rng is not None else np.random.default_rng(self.cfg.seed)
        p = self.profile
        # Stage 1+2 as vector masks — no Python loop, no unreachable branches
        bot = rng.random(n) < p.p_bot_success
        human = rng.random(n) < np.where(bot, p.p_human_if_bot, p.p_human_else)
        draws = rng.random(n)
        cum = np.cumsum([p.p_fold, p.p_sue, p.p_regulatory, p.p_stall])
        idx = np.searchsorted(cum, draws)  # 0..3, one pass
        idx = np.minimum(idx, 3)  # float-edge guard: rounding can probe past cum[-1]
        idx = np.where(human, idx, 3)  # bot-only path → stall
        counts = np.bincount(idx, minlength=4)
        values = (counts / n).tolist()
        return dict(zip(OUTCOMES, values, strict=True))


# --------------------------------------------------------------------------- #
# Escalation velocity — the D-term (control theory, v32.2 Dimension 7)
# --------------------------------------------------------------------------- #


def escalation_velocity(events: Sequence[object]) -> float:
    """Rate of change of opponent aggression from dated tripwire events.

    Positive velocity (shrinking intervals) = a human has taken over the file
    and is pushing toward Klage. Rule: velocity > 0 AND claim not time-barred →
    pre-empt with Feststellungsklage instead of ceding tempo.
    """
    dates: list[date] = []
    for e in events:
        d = getattr(e, "date", None)
        if isinstance(d, date):
            dates.append(d)
    if len(dates) < 3:
        return 0.0
    dates = sorted(dates)
    intervals = [(b - a).days for a, b in pairwise(dates)]
    return float(intervals[0] - intervals[-1])


# --------------------------------------------------------------------------- #
# Verjährung — stochastic model (I7: no binaries, § 204/212 interruptions modeled)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class VerjaehrungModel:
    start: date
    expiry_date: date
    events_used: int
    hemmung_days: int
    confidence: float
    note: str


def _add_months(d: date, months: int) -> date:
    """Calendar arithmetic without external deps (dateutil is a SPOF we refuse)."""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    # clamp day to target month length
    next_first = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    last_day = (next_first - date(year, month, 1)).days
    return date(year, month, min(d.day, last_day))


def calculate_verjaehrung(
    threat: Threat,
    events: Sequence[VerjaehrungEvent],
    cfg: RagnarConfig | None = None,
) -> VerjaehrungModel | None:
    """Limitation model with § 204 Hemmung and § 212 Neubeginn events.

    Semantics: threat.verjaehrung_date is the EXPIRY (Verjährungseintritt)
    when known; otherwise the expiry is derived from the anchor date plus the
    statutory months. None if no anchor exists (unknown clock — priced
    honestly elsewhere).
    """
    cfg = cfg or default_cfg()
    if threat.verjaehrung_date is not None:
        expiry = threat.verjaehrung_date
    else:
        expiry = _add_months(threat.rueckgabe_date or threat.threat_date, cfg.verjaehrung_months)
    start = threat.rueckgabe_date or threat.threat_date
    hemmung_days = 0
    used = 0
    for ev in sorted(events, key=lambda e: e.date):
        if ev.date < start or ev.date > expiry:
            continue  # outside the running period — no effect, but counted honestly
        if ev.type is VerjaehrungEventType.ANERKENNTUNG:
            # § 212 Abs. 1 Nr. 2 BGB: Neubeginn — full period restarts
            new_expiry = _add_months(ev.date, cfg.verjaehrung_months)
            if new_expiry > expiry:
                expiry = new_expiry
            used += 1
            continue
        end = ev.end_date or _add_months(ev.date, 6)  # § 204 Abs. 2 BGB default
        if end > ev.date:
            hemmung_days += (end - ev.date).days
            expiry = expiry + timedelta(days=(end - ev.date).days)
            used += 1
    confidence = 0.95 if used else 0.90
    return VerjaehrungModel(
        start=start,
        expiry_date=expiry,
        events_used=used,
        hemmung_days=hemmung_days,
        confidence=confidence,
        note="§ 548 Abs. 1 BGB chain incl. § 204/212 events; "
        "auto-abo application priced at profile confidence_floor (analogy chain)",
    )


def days_to_verjaehrung(model: VerjaehrungModel) -> int:
    """Signed days until expiry (negative = past — the phase transition is done)."""
    return (model.expiry_date - date.today()).days


def statute_expired(threat: Threat, cfg: RagnarConfig | None = None) -> bool:
    """Binary expiry check — for tripwires only. Strategy uses the full model."""
    cfg = cfg or default_cfg()
    if threat.verjaehrung_date is not None:
        return threat.verjaehrung_date < date.today()
    if threat.rueckgabe_date is not None:
        return _add_months(threat.rueckgabe_date, cfg.verjaehrung_months) < date.today()
    return False  # unknown clock: never claim death without proof (ground truth or silence)


# --------------------------------------------------------------------------- #
# NPV — path-dependent, matrix-expressed (I15/C14)
# --------------------------------------------------------------------------- #


def npv_path_dependent(
    maneuver: Maneuver,
    opp: OpponentModel,
    horizon: int | None = None,
    n_paths: int | None = None,
    rng: np.random.Generator | None = None,
    claim: float | None = None,
    cfg: RagnarConfig | None = None,
) -> float:
    """Path-dependent NPV of running the maneuver against this opponent.

    The temporal correlation that broke the old NPV (win in month 1 → costs
    stop; win in month 6 → costs compound) is expressed in the data layout:
    the active mask IS the path dependency.

    claim defaults to maneuver.cost_estimate — the Lagom convention that a
    maneuver is priced at the value it protects. Callers with a real claim
    pass it explicitly.
    """
    cfg = cfg or default_cfg()
    h = horizon if horizon is not None else cfg.npv_horizon
    n = n_paths if n_paths is not None else cfg.npv_paths
    rng = rng if rng is not None else np.random.default_rng(cfg.seed)

    at_stake = claim if claim is not None else maneuver.cost_estimate
    # monthly fold probability: rational opponents fold fast on unschlüssig claims
    p_fold_month = min(0.55, max(0.02, 0.05 + 0.40 * opp.rationality_weight))
    # our monthly defense burn while the dispute stays active (3-month amortization)
    monthly_cost = maneuver.cost_estimate / 3.0

    wins = rng.random((n, h)) < p_fold_month  # (n, H) fold events
    win_month = np.where(wins.any(axis=1), wins.argmax(axis=1), h - 1)
    months = np.arange(h)[None, :]  # (1, H)
    active = months <= win_month[:, None]  # (n, H) — the path mask
    costs = (monthly_cost * active).sum(axis=1)  # path-dependent burn
    discount = (1.0 + cfg.discount_rate) ** -(win_month + 1)
    return float(((at_stake - costs) * discount).mean())


# --------------------------------------------------------------------------- #
# Victory — five states, Pyrrhic blindness cured (I8/C16)
# --------------------------------------------------------------------------- #


def compute_victory_value(state: VictoryState, claim: float, cost: float, bonus: float) -> float:
    """Monetary value of an outcome state. A 'win' costing more than it
    protects scores negative — the engine recommends no Pyrrhic victories."""
    match state:
        case VictoryState.TOTAL:
            return claim - cost + bonus
        case VictoryState.PARTIAL:
            return 0.6 * claim - cost + 0.6 * bonus
        case VictoryState.PYRRHIC:
            return claim - 1.25 * cost
        case VictoryState.STALEMATE:
            return -0.5 * cost
        case VictoryState.DEFEAT:
            return -claim - cost + 0.1 * bonus
        case _:
            assert_never(state)


def compute_victory_projection(
    maneuver: Maneuver,
    opp: OpponentModel,
    dsup_score: float,
    cfg: RagnarConfig | None = None,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """Five-state victory projection with interaction adjustment (I10/I13).

    SPOF correlation: opponents of low rationality sue more regardless of merits
    (institutional inertia) — the projection blends that in instead of pretending
    independence.
    """
    cfg = cfg or default_cfg()
    dist = CausalGraph(maneuver.id, cfg).propagate(cfg.mc_iterations, rng)

    # I13 interaction adjust: irrational opponents escalate past their EV
    rw = opp.rationality_weight
    p_sue = dist["sue"] * (1.3 - 0.6 * rw)
    p_fold = dist["fold"] * (0.8 + 0.2 * rw)
    p_reg = dist["regulatory"]
    p_stall = dist["stall"]
    total = p_sue + p_fold + p_reg + p_stall
    p_sue, p_fold, p_reg, p_stall = (x / total for x in (p_sue, p_fold, p_reg, p_stall))

    p_win_court = 0.5 + 0.45 * dsup_score  # defensive superiority → court win prob
    projection = {
        VictoryState.TOTAL: p_fold + p_sue * p_win_court,
        VictoryState.PARTIAL: p_reg,
        VictoryState.PYRRHIC: p_sue * (1.0 - p_win_court) * 0.35,
        VictoryState.DEFEAT: p_sue * (1.0 - p_win_court) * 0.65,
        VictoryState.STALEMATE: p_stall,
    }
    # no rounding: the contract is sum == 1.0 within 1e-6 (float-exact by construction)
    return {str(k.value): v for k, v in projection.items()}


# --------------------------------------------------------------------------- #
# Nash-Lagom — the equilibrium the heuristic was claiming to be (I12)
# --------------------------------------------------------------------------- #


def lagom_solve_nash(
    rationality_weight: float,
    claim: float,
    cost_ceiling: float,
    clock_value: float = 0.0,
    cfg: RagnarConfig | None = None,
) -> tuple[float, float]:
    """Two-player zero-sum solution for the aggression/patience choice.

    clock_value ∈ [0,1] (crypto_viability): when silence lets the claim die on
    a short clock, patience gains a bonus that aggression cannot match — this is
    the ZHUGE condition derived from the payoff matrix instead of folklore.
    Returns (p_aggressive, expected_value), both bounded.

    Game matrix (our EV):
        vs ESCALATE:  AGG = 0.2·claim·rw − 0.6·C      PAT = −0.05·C + clock·claim·0.25
        vs FOLD:      AGG = claim − 0.1·C              PAT = claim·rw − 0.05·C
    Opponent mix: p(ESCALATE) = 1 − 0.7·rw (rational opponents fold more).
    """
    _ = cfg  # payoff matrix is statute-shaped; tunables enter via clock_value
    rw = min(1.0, max(0.0, rationality_weight))
    clock = min(1.0, max(0.0, clock_value))
    c = max(1.0, cost_ceiling)

    p_escalate = 1.0 - 0.7 * rw
    agg_esc = 0.2 * claim * rw - 0.6 * c
    agg_fold = claim - 0.1 * c
    pat_esc = -0.05 * c + clock * claim * 0.25
    pat_fold = claim * rw - 0.05 * c

    ev_agg = p_escalate * agg_esc + (1.0 - p_escalate) * agg_fold
    ev_pat = p_escalate * pat_esc + (1.0 - p_escalate) * pat_fold

    # smoothed best response: pure-strategy dominance rendered as a bounded mixed weight
    tau = max(50.0, 0.05 * max(1.0, claim))
    p_aggressive = 1.0 / (1.0 + math.exp(-(ev_agg - ev_pat) / tau))
    return round(p_aggressive, 6), round(max(ev_agg, ev_pat), 4)


# --------------------------------------------------------------------------- #
# Opponent model — Bayesian update, 5 known types + decaying dark horse (I13)
# --------------------------------------------------------------------------- #

_BASE_LIKELIHOOD: dict[OpponentType, dict[str, float]] = {
    OpponentType.FLEET_PROVIDER: {"SUE": 0.25, "FOLD": 0.30, "STALL": 0.35, "REGULATORY": 0.10},
    OpponentType.INKASSO_AGENT: {"SUE": 0.10, "FOLD": 0.40, "STALL": 0.45, "REGULATORY": 0.05},
    OpponentType.BANK: {"SUE": 0.35, "FOLD": 0.35, "STALL": 0.25, "REGULATORY": 0.05},
    OpponentType.INSURER: {"SUE": 0.30, "FOLD": 0.30, "STALL": 0.35, "REGULATORY": 0.05},
    OpponentType.GOVERNMENT: {"SUE": 0.15, "FOLD": 0.15, "STALL": 0.60, "REGULATORY": 0.10},
}

_DOMAIN_AFFINITY: dict[Domain, OpponentType] = {
    Domain.AUTO_ABO: OpponentType.FLEET_PROVIDER,
    Domain.BANKING: OpponentType.BANK,
    Domain.INSURANCE: OpponentType.INSURER,
    Domain.GOVERNMENT: OpponentType.GOVERNMENT,
}

_TYPE_RATIONALITY: dict[OpponentType, float] = {
    OpponentType.FLEET_PROVIDER: 0.40,
    OpponentType.INKASSO_AGENT: 0.35,
    OpponentType.BANK: 0.60,
    OpponentType.INSURER: 0.50,
    OpponentType.GOVERNMENT: 0.30,
}

_DOCTRINE_LIKELIHOOD: dict[Doctrine, tuple[str, float]] = {
    Doctrine.HANNIBAL: ("SUE", 1.3),
    Doctrine.ZHUGE: ("STALL", 1.2),
    Doctrine.FABIAN: ("FOLD", 1.1),
    Doctrine.CAESAR: ("REGULATORY", 1.15),
}


def update_opponent_model(
    model: OpponentModel,
    outcome: str,
    maneuver: Maneuver,
    domain: Domain,
    cfg: RagnarConfig | None = None,
) -> OpponentModel:
    """Bayesian update over opponent types after an observed outcome.

    The dark-horse mass only ever decays — with every observation the unknown
    becomes known, never the reverse (tested invariant).
    """
    cfg = cfg or default_cfg()
    outcome = outcome.upper()
    belief = dict(model.belief)
    for t in OpponentType:
        likelihood = _BASE_LIKELIHOOD[t].get(outcome, 0.05)
        if _DOMAIN_AFFINITY.get(domain) is t:
            likelihood *= 1.8  # the domain makes this type a priori likelier
        bumped, factor = _DOCTRINE_LIKELIHOOD.get(maneuver.doctrine, ("", 1.0))
        if bumped == outcome:
            likelihood *= factor  # our maneuver influenced this outcome
        belief[t] = belief[t] * likelihood
    total = sum(belief.values()) or 1.0
    belief = {t: v / total for t, v in belief.items()}

    most_likely = max(belief, key=lambda t: belief[t])
    rw = 0.7 * model.rationality_weight + 0.3 * _TYPE_RATIONALITY[most_likely]
    return model.with_update(
        belief=belief,
        dark_horse=model.dark_horse * cfg.dark_horse_decay,
        rationality_weight=rw,
    )
