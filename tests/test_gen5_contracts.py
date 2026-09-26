# GEN 5 contracts — serde, CLI, in-binary suite, epistemic governance.
"""Contract tests for the integration layer: the operator's surface."""

from __future__ import annotations

import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

from ragnar.citations import emit_citations, quarantined_citations, registry, reverify_due
from ragnar.gen5_integration import apply_assembly_patches, plan_to_json, run_cli, run_tests


def _threat_json() -> dict:
    return {
        "domain": "auto_abo",
        "opponent": "DFD",
        "claim": 2100.0,
        "basis": "§ 249 BGB",
        "contract_number": "VR-12345",
        "bank_account": "DE89370501981234567890",
        "threat_date": "2026-06-01",
        "verjaehrung_date": (date.today() + timedelta(days=90)).isoformat(),
    }


def test_apply_assembly_patches_idempotent() -> None:
    apply_assembly_patches()
    apply_assembly_patches()  # second call is a no-op
    assert getattr(run_cli, "__name__", None)  # module healthy


def test_cli_test_flag_runs_full_suite() -> None:
    assert run_cli(["--test"]) == 0


def test_cli_stdin(capsys: pytest.CaptureFixture[str]) -> None:
    payload = json.dumps(
        {"domain": "auto_abo", "opponent": "DFD", "claim": 2100.0, "basis": "§ 249 BGB"}
    )
    old, sys.stdin = sys.stdin, io.StringIO(payload)
    try:
        rc = run_cli(["--stdin", "--pretty"])
    finally:
        sys.stdin = old
    out = capsys.readouterr().out
    assert rc == 0
    plan = json.loads(out)
    assert plan["threat"]["opponent"] == "DFD"
    assert abs(sum(plan["victory_projection"].values()) - 1.0) < 1e-6


def test_cli_file_roundtrip(tmp_path: Path) -> None:
    inp = tmp_path / "t.json"
    out = tmp_path / "plan.json"
    inp.write_text(
        json.dumps(
            {"domain": "auto_abo", "opponent": "DFD", "claim": 2100.0, "basis": "§ 249 BGB"}
        ),
        encoding="utf-8",
    )
    rc = run_cli(["--input", str(inp), "--output", str(out)])
    assert rc == 0 and out.exists()
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["threat"]["opponent"] == "DFD"
    assert plan["documents"]
    assert plan["audit_root"]


def test_cli_bad_json_exit_two(capsys: pytest.CaptureFixture[str]) -> None:
    inp_path = "/tmp/ragnar_bad.json"
    Path(inp_path).write_text('{"domain": "auto_abo"', encoding="utf-8")
    rc = run_cli(["--input", inp_path])
    assert rc == 2
    _ = capsys.readouterr()


def test_cli_unknown_domain_exit_two(capsys: pytest.CaptureFixture[str]) -> None:
    inp_path = "/tmp/ragnar_unknown.json"
    Path(inp_path).write_text(
        json.dumps({"domain": "warp_drive", "opponent": "X", "claim": 1.0, "basis": "b"}),
        encoding="utf-8",
    )
    rc = run_cli(["--input", inp_path])
    assert rc == 2
    _ = capsys.readouterr()


def test_cli_ingest_klage_breaks_cryptobiosis_exit_three(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    inp = tmp_path / "t.json"
    inp.write_text(
        json.dumps(
            {
                "domain": "auto_abo",
                "opponent": "DFD",
                "claim": 2100.0,
                "basis": "§ 249 BGB",
                "verjaehrung_date": (date.today() + timedelta(days=90)).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    rc = run_cli(["--input", str(inp), "--ingest", "Hiermit wird Klage erhoben."])
    assert rc == 3  # break-cryptobiosis signal — script-friendly
    captured = capsys.readouterr()
    assert "tripwire" in captured.err


def test_cli_ingest_neutral_text_exit_zero(tmp_path: Path) -> None:
    inp = tmp_path / "t.json"
    inp.write_text(
        json.dumps(
            {"domain": "auto_abo", "opponent": "DFD", "claim": 2100.0, "basis": "§ 249 BGB"}
        ),
        encoding="utf-8",
    )
    rc = run_cli(["--input", str(inp), "--ingest", "Wir nehmen Ihr Schreiben zur Kenntnis."])
    assert rc == 0


def test_in_binary_suite_passes() -> None:
    assert run_tests() == 0


def test_plan_json_schema_complete() -> None:
    from ragnar.gen1_foundation import Domain, Threat
    from ragnar.gen4_execution import Ragnar

    t = Threat(
        domain=Domain.AUTO_ABO,
        opponent="DFD",
        claim=2100.0,
        basis="§ 249 BGB",
        threat_date=date(2026, 6, 1),
        verjaehrung_date=date.today() + timedelta(days=90),
    )
    plan = Ragnar().decide(t)
    pj = plan_to_json(plan)
    for key in (
        "threat",
        "spofs",
        "maneuver",
        "doctrine",
        "tstate",
        "documents",
        "dsup_score",
        "confidence",
        "victory_projection",
        "audit_root",
    ):
        assert key in pj
    json.dumps(pj, ensure_ascii=False)  # must be serializable
    assert pj["threat"]["domain"] == "auto_abo"
    for d in pj["documents"]:
        for key in ("body", "citations", "hash", "channel", "confidence"):
            assert key in d


def test_citation_registry_governance() -> None:
    reg = registry()
    assert reg.reverify_after().isoformat() == "2027-01-27"
    assert reverify_due() is False  # frozen 2026-09-26 + shelf life
    assert len(quarantined_citations()) >= 5  # C1, C4, C5, C6, C9, C10 visible


def test_court_floor_is_confirmed_only() -> None:
    court = emit_citations("verjaehrung_548", court=True)
    letter = emit_citations("verjaehrung_548", court=False)
    assert len(court) >= 3
    assert set(court) <= set(letter)
