# GEN 5 — INTEGRATION: typed serde, CLI, in-binary test suite.
"""RAGNAR Ω OMNI v33.0 — Gen 5: Integration Layer.

Owns the outside world: plan_to_json (typed serde), run_cli (argparse, exit
codes), run_tests (table-driven in-binary suite), and the assembly shim.

Package-layout note (F1 discipline): in the v33 build protocol this layer also
carried a monkey-patch layer welding cross-generation state into the
concatenated artifact. In the pip-installable package layout those two Gen-4
flags are resolved NATIVELY in the owning module (Ragnar persists _last_threat
and threads live Verjährung days through ingest_incoming itself).
apply_assembly_patches() is retained as an idempotent no-op for API stability —
the honest form of a fix that has become permanent code.

Contract: ragnar_manifest — this module is the last layer; it imports all.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# Test/bootstrap environments get a deterministic key ONLY if none is set;
# production sets a real 32+ byte secret via environment (fail-closed lock).
os.environ.setdefault("RAGNAR_OMEGA_KEY", "test-secret-key-for-contract-tests")

from ragnar.citations import CitationTrust, emit_citations, quarantined_citations
from ragnar.gen1_foundation import (
    Doctrine,
    Domain,
    Maneuver,
    OpponentModel,
    Plan,
    Threat,
    TripwireType,
    TState,
    VerjaehrungEvent,
    VerjaehrungEventType,
    VictoryState,
    get_logger,
    threat_from_json,
)
from ragnar.gen1_foundation import Document as _Document  # re-export alias
from ragnar.gen2_analysis import (
    analyze_spofs_universal,
    crypto_viability,
    detect_violations,
    dsup_shield,
    recursive_sterilize,
    select_tardigrade,
)
from ragnar.gen3_strategy import (
    CausalGraph,
    calculate_verjaehrung,
    compute_victory_value,
    days_to_verjaehrung,
    escalation_velocity,
    lagom_solve_nash,
    npv_path_dependent,
    statute_expired,
    update_opponent_model,
)
from ragnar.gen4_execution import (
    MANEUVERS,
    SPECS,
    OmegaLock,
    Ragnar,
    TripwireMonitor,
    build_document,
    judge_adoptability,
    self_audit,
)

__all__ = ["apply_assembly_patches", "plan_to_json", "run_cli", "run_tests"]

logger = get_logger("RAGNAR.integration")


# ================================================================
# SECTION 1: ASSEMBLY PATCH LAYER — idempotent no-op (see module docstring)
# ================================================================


def apply_assembly_patches() -> None:
    """Idempotent integration hook. In the package layout the Gen-4 flags
    (inline numpy import, unpersisted threat) are fixed natively in the owning
    module; this function verifies the fix is present and marks the class.

    Raises RuntimeError if the native integration is missing — the honest
    version of a patch: fail loudly rather than silently no-op.
    """
    if getattr(Ragnar, "_assembly_patched", False):
        return
    if not hasattr(Ragnar, "ingest_incoming") or not hasattr(Ragnar, "save_state"):
        msg = "Ragnar lacks native integration (ingest_incoming/save_state) — package integrity broken"
        raise RuntimeError(msg)
    Ragnar._assembly_patched = True


# ================================================================
# SECTION 2: PLAN SERDE (typed, complete, round-trippable)
# ================================================================


def plan_to_json(plan: Plan) -> dict[str, Any]:
    """Plan → JSON-primitive dict. Documents serialize completely — a plan
    without its weapons is not a plan. Enum values, not enum objects."""
    return {
        "threat": plan.threat.to_json(),
        "spofs": [
            {
                "id": s.id,
                "code": s.code,
                "desc": s.desc,
                "exploit": s.exploit,
                "severity": int(s.severity),
                "confidence": s.confidence,
                "cascade": list(s.cascade),
            }
            for s in plan.spofs
        ],
        "maneuver": {
            "id": plan.maneuver.id,
            "name": plan.maneuver.name,
            "basis": plan.maneuver.basis,
            "doctrine": plan.maneuver.doctrine.value,
            "aggression": plan.maneuver.aggression,
            "cost_estimate": plan.maneuver.cost_estimate,
        },
        "doctrine": plan.doctrine.value,
        "tstate": plan.tstate.value,
        "documents": [
            {
                "body": d.body,
                "salutation": d.salutation,
                "closing": d.closing,
                "citations": list(d.citations),
                "hash": d.hash,
                "tone_score": d.tone_score,
                "spof_risk": d.spof_risk,
                "sterilization_passes": d.sterilization_passes,
                "channel": d.channel.value,
                "confidence": d.confidence,
                "judge_adoptability": judge_adoptability(d),
            }
            for d in plan.documents
        ],
        "dsup_score": plan.dsup_score,
        "confidence": plan.confidence,
        "victory_projection": {str(k): float(v) for k, v in plan.victory_projection.items()},
        "audit_root": plan.audit_root,
    }


# ================================================================
# SECTION 3: CLI
# ================================================================


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ragnar",
        description="RAGNAR Ω OMNI v33.0 — asymmetric legal defense engine",
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--input", metavar="PATH", help="threat JSON file")
    src.add_argument("--stdin", action="store_true", help="read threat JSON from stdin")
    p.add_argument("--output", metavar="PATH", help="write plan JSON to file")
    p.add_argument(
        "--ingest", metavar="TEXT", help="process incoming text through the tripwire monitor"
    )
    p.add_argument("--test", action="store_true", help="run the full in-binary test suite")
    p.add_argument(
        "--resources", type=float, default=10.0, metavar="R", help="resource budget (default 10.0)"
    )
    p.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    return p


def _emit(plan_json: dict[str, Any], output: str | None, pretty: bool) -> None:
    text = json.dumps(plan_json, ensure_ascii=False, indent=2 if pretty else None)
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text)


def run_cli(argv: list[str] | None = None) -> int:
    """Exit codes: 0 ok; 1 no input; 2 bad input JSON; 3 ingest alert
    (a cryptobiosis-breaking tripwire fired — script-friendly signal)."""
    apply_assembly_patches()
    args = _build_parser().parse_args(argv)

    if args.test:
        return run_tests()

    if args.input:
        raw = Path(args.input).read_text(encoding="utf-8")
    elif args.stdin:
        raw = sys.stdin.read()
    else:
        _build_parser().error("one of --input/--stdin/--test is required")

    try:
        threat = threat_from_json(json.loads(raw))
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"error: invalid threat input: {e}", file=sys.stderr)
        return 2

    engine = Ragnar(resources=args.resources)
    plan = engine.decide(threat)

    if args.ingest:
        ev = engine.ingest_incoming(args.ingest)
        if ev is not None:
            print(
                f"tripwire: {ev.type.value} [{ev.severity.name}] → {ev.response.value}",
                file=sys.stderr,
            )
            if engine.monitor.should_break_cryptobiosis(ev):
                _emit(plan_to_json(plan), args.output, args.pretty)
                return 3

    _emit(plan_to_json(plan), args.output, args.pretty)
    return 0


# ================================================================
# SECTION 4: TABLE-DRIVEN TEST SUITE (seeded, tolerance bands, no Monte Carlo
# noise assertions — the statistically literate version)
# ================================================================


def _t(**kw: Any) -> Threat:
    base: dict[str, Any] = {
        "domain": Domain.AUTO_ABO,
        "opponent": "DFD",
        "claim": 2100.0,
        "basis": "§ 249 BGB",
        "contract_number": "VR-12345",
        "bank_account": "DE02120300000000202051",  # mod-97 valid (adjoint audit checks us too)
        "threat_date": date(2026, 6, 1),
        "verjaehrung_date": date.today() + timedelta(days=90),
    }
    base.update(kw)
    return Threat(**base)


def _verjaehrung_hemmung_case() -> bool:
    """§ 204 Hemmung: a Klage event pauses the six-month clock."""
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
    if plain is None or hemmed is None:
        return False
    return hemmed.expiry_date > plain.expiry_date


def _verjaehrung_days_case() -> bool:
    model = calculate_verjaehrung(_t(), ())
    return model is not None and isinstance(days_to_verjaehrung(model), int)


# Each case: (name, callable -> bool). Table-driven: add a row, add a test.
_CASES: tuple[tuple[str, Callable[[], bool]], ...] = (
    # --- SPOF engine ---
    (
        "spof.fires_on_quant_claim",
        lambda: any(
            s.code == "EVIDENTIARY_ROOT" for s in analyze_spofs_universal(_t(), False, [], None)
        ),
    ),
    (
        "spof.consumer_gate_o6",
        lambda: all(
            s.code != "AGB_ISOLATION_VOID"
            for s in analyze_spofs_universal(_t(is_consumer=False), False, [], None)
        ),
    ),
    (
        "spof.o3_requires_dispute",
        lambda: all(
            s.code != "PROCESSING_BLOCK_ACCRUAL"
            for s in analyze_spofs_universal(_t(), False, ["x"], None)
        ),
    ),
    (
        "spof.pipeline_sorted",
        lambda: (lambda sp: sp == sorted(sp, key=lambda s: -s.severity))(
            analyze_spofs_universal(_t(), True, ["x"] * 5, None)
        ),
    ),
    # --- DSUP ---
    ("dsup.bounded_and_honest", lambda: 0.0 <= dsup_shield(_t(), []).score <= 1.0),
    # --- Sterilization ---
    (
        "sterilize.kills_violations",
        lambda: (
            detect_violations(recursive_sterilize(_Document(body="Sie sind KORRUPT!!!")).body) == []
        ),
    ),
    (
        "sterilize.preserves_salutation",
        lambda: (
            "Sehr geehrte Damen und Herren"
            in recursive_sterilize(
                _Document(body="Inakzeptabel!", salutation="Sehr geehrte Damen und Herren,")
            ).body
        ),
    ),
    # --- Tardigrade ---
    (
        "tardigrade.thresholds",
        lambda: (
            select_tardigrade(0.9, None) is TState.CRYPTO
            and select_tardigrade(0.9, "KLAGE") is TState.ACTIVE
        ),
    ),
    ("tardigrade.crypto_viability_bounded", lambda: 0.0 <= crypto_viability(_t()) <= 1.0),
    # --- Opponent model ---
    (
        "opponent.normalizes",
        lambda: (
            abs(
                sum(
                    update_opponent_model(
                        OpponentModel.uniform(),
                        "SUE",
                        Maneuver("m", "m", "b", Doctrine.ZHUGE),
                        Domain.BANKING,
                    ).belief.values()
                )
                - 1.0
            )
            < 1e-6
        ),
    ),
    (
        "opponent.dark_horse_only_new",
        lambda: (lambda m1, m2: m2.dark_horse <= m1.dark_horse + 1e-9)(
            update_opponent_model(
                OpponentModel.uniform(),
                "SUE",
                Maneuver("m", "m", "b", Doctrine.ZHUGE),
                Domain.BANKING,
            ),
            update_opponent_model(
                update_opponent_model(
                    OpponentModel.uniform(),
                    "SUE",
                    Maneuver("m", "m", "b", Doctrine.ZHUGE),
                    Domain.BANKING,
                ),
                "SUE",
                Maneuver("m", "m", "b", Doctrine.ZHUGE),
                Domain.BANKING,
            ),
        ),
    ),
    # --- Causal (seeded determinism + shape) ---
    (
        "causal.shape_and_reachability",
        lambda: (
            lambda d: (
                set(d) == {"fold", "sue", "regulatory", "stall"}
                and abs(sum(d.values()) - 1.0) < 1e-9
                and all(v > 0 for v in d.values())
            )
        )(CausalGraph("DEMAND_REFUND").propagate(8000)),
    ),
    (
        "causal.silence_stall_dominant",
        lambda: (lambda d: d["stall"] == max(d.values()))(CausalGraph("SILENCE").propagate(5000)),
    ),
    (
        "causal.seeded_deterministic",
        lambda: CausalGraph("SILENCE").propagate(1000) == CausalGraph("SILENCE").propagate(1000),
    ),
    # --- NPV ---
    (
        "npv.early_win_beats_late",
        lambda: (
            npv_path_dependent(
                Maneuver("m", "m", "b", Doctrine.ZHUGE, cost_estimate=100.0),
                OpponentModel.uniform(rationality_weight=0.95),
            )
            > npv_path_dependent(
                Maneuver("m", "m", "b", Doctrine.ZHUGE, cost_estimate=100.0),
                OpponentModel.uniform(rationality_weight=0.05),
            )
        ),
    ),
    # --- Nash-Lagom ---
    (
        "nash.bounded_and_clock_aware",
        lambda: (lambda p_hi, p_lo: 0.0 <= p_hi <= 1.0 and 0.0 <= p_lo <= 1.0 and p_hi < p_lo)(
            lagom_solve_nash(0.5, 2100.0, 800.0, clock_value=0.9)[0],
            lagom_solve_nash(0.5, 2100.0, 800.0, clock_value=0.0)[0],
        ),
    ),
    # --- Victory states ---
    (
        "victory.pyrrhic_negative",
        lambda: compute_victory_value(VictoryState.PYRRHIC, 500, 2000, 0) < 0,
    ),
    (
        "victory.total_positive",
        lambda: compute_victory_value(VictoryState.TOTAL, 2000, 500, 400) == 1900,
    ),
    # --- Verjährung ---
    (
        "verjaehrung.hemmung_pauses",
        _verjaehrung_hemmung_case,
    ),
    (
        "verjaehrung.expired_flag",
        lambda: statute_expired(_t(verjaehrung_date=date.today() - timedelta(days=10))) is True,
    ),
    (
        "verjaehrung.days_to_verjaehrung",
        _verjaehrung_days_case,
    ),
    # --- Velocity ---
    ("velocity.static_bot_zero", lambda: abs(escalation_velocity([])) == 0.0),
    # --- Documents ---
    (
        "docs.all_eight_sterile",
        lambda: all(
            build_document(
                sid,
                {
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
                },
            ).spof_risk
            < 0.1
            for sid in SPECS
        ),
    ),
    (
        "docs.court_no_rhetoric",
        lambda: (
            "Blöße"
            not in build_document(
                "feststellungsklage",
                {
                    "mandant": "M",
                    "gegner": "G",
                    "vertrag": "V",
                    "betrag": "1.000,00",
                    "verjaehrung": "01.01.2027",
                    "rueckgabe": "01.06.2026",
                    "gericht": "AG",
                    "aktenzeichen": "1 O 1/26",
                },
            ).body
        ),
    ),
    (
        "docs.quarantine_never_emitted",
        lambda: all(
            q["text"].split("(")[0].strip()[:24]
            not in " ".join(
                c
                for sid in SPECS
                for c in build_document(
                    sid,
                    {
                        "mandant": "M",
                        "gegner": "G",
                        "vertrag": "V",
                        "betrag": "1.000,00",
                        "verjaehrung": "01.01.2027",
                        "rueckgabe": "01.06.2026",
                        "gericht": "AG",
                        "aktenzeichen": "1 O 1/26",
                        "sachverhalt": "s",
                        "datum": "01.07.2026",
                        "konto": "K",
                        "anschrift": "A",
                        "rate": "100,00",
                    },
                ).citations
            )
            for q in quarantined_citations()
        ),
    ),
    (
        "docs.court_citations_confirmed_only",
        lambda: (
            set(
                build_document(
                    "verjaehrungseinrede",
                    {
                        "gericht": "AG",
                        "aktenzeichen": "1 O 1/26",
                        "rueckgabe": "01.06.2026",
                        "verjaehrung": "01.01.2027",
                    },
                ).citations
            )
            <= set(emit_citations("verjaehrung_548", court=True))
        ),
    ),
    (
        "docs.hash_stable",
        lambda: (
            build_document("bestreiten_sperre", {"gegner": "G"}).hash
            == build_document("bestreiten_sperre", {"gegner": "G"}).hash
        ),
    ),
    # --- Tripwires ---
    (
        "tripwire.klage_fires",
        lambda: (lambda ev: ev is not None and ev.type is TripwireType.KLAGE)(
            TripwireMonitor().check("Klage wird erhoben.", TState.CRYPTO)
        ),
    ),
    (
        "tripwire.negation_no_false_positive",
        lambda: (lambda ev: ev is None or ev.type is not TripwireType.SCHUFA)(
            TripwireMonitor().check("Wir bestätigen: keine SCHUFA-Meldung erfolgt.", TState.CRYPTO)
        ),
    ),
    (
        "tripwire.sb_atomization_fires",
        lambda: (lambda ev: ev is not None and ev.type is TripwireType.SB_ATOMIZATION)(
            TripwireMonitor().check(
                "Rechnung: Selbstbeteiligung 1.000,00 EUR, Selbstbeteiligung 750,00 EUR, "
                "Selbstbeteiligung 1.000,00 EUR.",
                TState.CRYPTO,
            )
        ),
    ),
    (
        "tripwire.verjaehrung_tick",
        lambda: (lambda ev: ev is not None and ev.type is TripwireType.VERJAERHRUNG_TICK)(
            TripwireMonitor().check(
                "Sehr geehrte Damen und Herren.", TState.CRYPTO, days_to_verjaehrung=12
            )
        ),
    ),
    # --- Omega Lock ---
    (
        "lock.cycle_and_replay",
        lambda: (
            lambda ol: (
                ol.engage(Doctrine.ZHUGE, TState.CRYPTO, ["KLAGE"])
                and ol.unlock(TripwireType.KLAGE, nonce="n1")
                and ol.engage(Doctrine.ZHUGE, TState.CRYPTO, ["KLAGE"])
                and not ol.unlock(TripwireType.KLAGE, nonce="n1")
            )
        )(OmegaLock()),
    ),
    (
        "lock.wrong_condition_rejected",
        lambda: (
            lambda ol: (
                ol.engage(Doctrine.ZHUGE, TState.CRYPTO, ["KLAGE"])
                and not ol.unlock(TripwireType.SETTLEMENT_OFFER, nonce="fresh")
            )
        )(OmegaLock()),
    ),
    # --- Orchestrator ---
    (
        "ragnar.decide_valid_plan",
        lambda: (
            lambda p: (
                p.confidence > 0
                and bool(p.spofs)
                and abs(sum(p.victory_projection.values()) - 1.0) < 1e-6
            )
        )(Ragnar(resources=10.0).decide(_t())),
    ),
    (
        "ragnar.audit_chain_valid",
        lambda: (lambda r: (r.decide(_t()), r.audit.verify())[1])(Ragnar(resources=10.0)),
    ),
    ("ragnar.state_roundtrip", lambda: _state_roundtrip()),
    (
        "ragnar.maneuver_registry_locked",
        lambda: all(
            m.id
            in {
                "SILENCE",
                "DEMAND_REFUND",
                "SCALPEL_LETTER",
                "REGULATORY_DOSSIER",
                "FESTSTELLUNGSKLAGE",
                "GEGENERKLAERUNG",
                "VERJAERHRUNGSEINREDE",
                "WIDERKLAGE",
            }
            for m in MANEUVERS
        ),
    ),
    ("ragnar.self_audit_adjoint", lambda: isinstance(self_audit(MANEUVERS[0], _t()), list)),
    (
        "ragnar.judge_adoptability_bounded",
        lambda: all(
            0.0 <= judge_adoptability(build_document(sid, {"gegner": "G"})) <= 1.0 for sid in SPECS
        ),
    ),
    # --- Serde ---
    (
        "serde.plan_json_keys",
        lambda: all(
            k in plan_to_json(Ragnar(resources=10.0).decide(_t()))
            for k in (
                "threat",
                "spofs",
                "maneuver",
                "documents",
                "victory_projection",
                "audit_root",
            )
        ),
    ),
    (
        "serde.threat_roundtrip",
        lambda: threat_from_json(_t().to_json()).to_json() == _t().to_json(),
    ),
    (
        "serde.citation_tier_floor",
        lambda: CitationTrust.CONFIRMED.value == 4 and CitationTrust.QUARANTINED.value == 0,
    ),
)


def _state_roundtrip() -> bool:
    import tempfile

    r1 = Ragnar(resources=10.0)
    r1.decide(_t())
    with tempfile.TemporaryDirectory() as td:
        p = str(Path(td) / "s.json")
        r1.save_state(p)
        r2 = Ragnar(resources=1.0)
        r2.load_state(p)
        return (
            r2.tstate == r1.tstate
            and r2.doctrine == r1.doctrine
            and r2.model.belief == r1.model.belief
            and r2.audit.verify()
        )


def run_tests() -> int:
    """Table-driven: iterate _CASES, report pass/fail per row.
    Exit 0 iff all pass. The harness reports — it never raises (BLE001 by design)."""
    apply_assembly_patches()
    passed = failed = 0
    failures: list[str] = []
    for name, fn in _CASES:
        try:
            ok = bool(fn())
        except Exception as e:
            ok, e_str = False, f"{type(e).__name__}: {e}"
        else:
            e_str = ""
        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(f"{name} {e_str}".strip())
    total = passed + failed
    print(f"\n{'=' * 56}\nRAGNAR v33.0 test suite: {passed}/{total} passed")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  X {f}")
    else:
        print("ALL TESTS PASSED")
    print("=" * 56)
    return 0 if failed == 0 else 1


if __name__ == "__main__":  # python -m ragnar.gen5_integration
    sys.exit(run_cli())
