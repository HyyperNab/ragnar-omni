# RAGNAR Ω OMNI v33.0 — package foundation.
"""RAGNAR Ω OMNI v33.0 — asymmetric, zero-trust, game-theoretic legal defense engine.

Public API is re-exported lazily from the five generation modules, which are
real dependency layers (not build artifacts):

    gen1_foundation  — types, enums, threat serde, hash-chained audit trail
    gen2_analysis    — SPOF engine (O1–O11), DSUP shield, sterilization, Tardigrade
    gen3_strategy    — causal graphs, NPV, Verjährung model, Nash-Lagom, opponent model
    gen4_execution   — document builders, tripwires, Omega Lock, orchestrator
    gen5_integration — typed serde, CLI, in-binary test suite
"""

from __future__ import annotations

from typing import Any

__version__ = "33.1.0"

__all__ = [
    "AuditTrail",
    "Doctrine",
    "Domain",
    "Maneuver",
    "OpponentModel",
    "Plan",
    "Ragnar",
    "Severity",
    "TState",
    "Threat",
    "TripwireMonitor",
    "VictoryState",
    "__version__",
    "default_cfg",
    "run_cli",
    "threat_from_json",
]


def __getattr__(name: str) -> Any:  # PEP 562 — lazy re-export, cheap imports
    if name in ("Ragnar", "TripwireMonitor", "OmegaLock"):
        from . import gen4_execution

        return getattr(gen4_execution, name)
    if name == "run_cli":
        from . import gen5_integration

        return getattr(gen5_integration, name)
    _map = {
        "AuditTrail": "gen1_foundation",
        "Doctrine": "gen1_foundation",
        "Domain": "gen1_foundation",
        "Maneuver": "gen1_foundation",
        "OpponentModel": "gen1_foundation",
        "Plan": "gen1_foundation",
        "Severity": "gen1_foundation",
        "Threat": "gen1_foundation",
        "TState": "gen1_foundation",
        "VictoryState": "gen1_foundation",
        "default_cfg": "config",
        "threat_from_json": "gen1_foundation",
    }
    if name in _map:
        import importlib

        mod = importlib.import_module(f".{_map[name]}", __package__)
        return getattr(mod, name)
    raise AttributeError(f"module 'ragnar' has no attribute {name!r}")
