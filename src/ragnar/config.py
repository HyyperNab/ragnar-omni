# GEN 0 — CONFIG: every magic number becomes a named, tunable API.
"""RagnarConfig — the single frozen source of all engine constants.

The Lagom constants stop being folklore and become API (v33.0 engineering pass).
All values are scalars only: config must never import engine types
(that would be a circular-dependency SPOF).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RagnarConfig:
    """Frozen engine configuration. Immutability kills the state-aliasing bug class."""

    # Determinism — seeded RNG threaded through causal + NPV (tests assert on it)
    seed: int = 0
    mc_iterations: int = 5_000
    npv_horizon: int = 12
    npv_paths: int = 2_000

    # Strategy layer
    lagom_center: float = 0.5
    p_regulatory_action: float = 0.3
    discount_rate: float = 0.02  # monthly
    defense_cost_ceiling: float = 800.0  # Pyrrhic check: paths above this re-score sub-Lagom
    velocity_threshold: float = 0.0  # O11 fires when escalation velocity > threshold

    # Epistemic layer — citation floors (4 = CitationTrust.CONFIRMED, 3 = PROBABLE)
    citation_floor_court: int = 4
    citation_floor_letter: int = 3
    confidence_load_bearing: float = 0.8

    # SPOF engine
    o3_min_events: int = 3  # PROCESSING_BLOCK_ACCRUAL gate: dispute must be underway
    o8_claim_threshold: float = 1_000.0  # SYSTEMIC_REGULATORY economic relevance gate

    # Verjährung model (§ 548 Abs. 1 BGB — six months from return)
    verjaehrung_months: int = 6
    verjaehrung_tick_days: int = 30  # tripwire: claim clock near expiry

    # Opponent model
    dark_horse_decay: float = 0.5  # P(unknown type) decays with every observation

    # Tardigrade thresholds
    crypto_threshold: float = 0.8
    tun_threshold: float = 0.5

    # Tripwire — cryptobiosis break conditions (TripwireType names)
    break_conditions: tuple[str, ...] = (
        "KLAGE",
        "SCHUFA",
        "VERJAERHRUNG_TICK",
        "SETTLEMENT_OFFER",
    )


def default_cfg() -> RagnarConfig:
    """Factory kept as a function (API stability across frozen-dataclass evolution)."""
    return RagnarConfig()
