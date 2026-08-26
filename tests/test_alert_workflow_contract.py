from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tomllib

import numpy as np
import pandas as pd
import pytest

import turbofan_anomaly.workflows.run_alert_policy_study as workflow
from turbofan_anomaly.evaluation.ledger import append_run_record, load_run_ledger
from turbofan_anomaly.workflows.run_alert_policy_study import (
    _atomic_write_json,
    _atomically_extend_ledger,
    _score_frame,
    validate_alert_policy_protocol,
    validate_allowed_input_path,
    validate_allowed_split_name,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    REPO_ROOT / "configs" / "alerting" / "fd002-alert-policy-study-protocol-v1.json"
)
PROTOCOL_V2 = (
    REPO_ROOT / "configs" / "alerting" / "fd002-alert-policy-study-protocol-v2.json"
)


def _record(run_id: str) -> dict:
    return {
        "schema_version": "2.0.0",
        "run_id": run_id,
        "source_run_id": run_id,
        "timestamp": "2026-08-25T00:00:00+00:00",
        "owner": "fixture",
        "experiment_name": "fixture",
        "model": "fixture",
        "parameters": {},
        "population": {},
        "metric": {},
        "evidence_class": "validation_proxy_only",
        "result_classification": "fixture",
        "evidence_boundary": {
            "final_result": False,
            "threshold_selected": False,
            "held_out_internal_test_accessed": False,
        },
        "split": {"path": "configs/splits/fixture.json"},
        "config": {"path": "configs/alerting/fixture.json"},
        "artifact": {"path": "reports/alerting_v1/fixture.csv"},
        "notes": "fixture",
        "provenance": {},
    }


def test_registered_protocol_round_trips_and_freezes_exact_grid() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_alert_policy_protocol(protocol)
    assert protocol["status"] == "registered_before_execution"
    assert protocol["evidence_boundary"]["allowed_splits"] == ["train", "validation"]
    assert set(protocol["evidence_boundary"]["prohibited_inputs"]) >= {
        "held_out_internal_test",
        "official_nasa_test",
    }
    grid = protocol["grid"]
    count = (
        len(grid["score_source_order"])
        * len(grid["threshold_context_order"])
        * len(grid["threshold_rules"])
        * len(grid["ewma_states"])
        * len(grid["persistence_values"])
    )
    assert count == 1280
    assert count * len(protocol["proxy_policies"]) == 6400
    assert json.loads(json.dumps(protocol, sort_keys=True)) == protocol


def test_v2_protocol_changes_only_governed_metadata_lineage() -> None:
    v1_bytes = PROTOCOL.read_bytes()
    assert hashlib.sha256(v1_bytes).hexdigest() == (
        "9734c465071401387f7ad2fc79abfc207d0eeb0e8724685267f74b7528f8cb6c"
    )
    v1 = json.loads(v1_bytes)
    v2 = json.loads(PROTOCOL_V2.read_text(encoding="utf-8"))
    validate_alert_policy_protocol(v2)

    lineage = v2["metadata_lineage_correction"]
    assert lineage["blocked_protocol_v1"]["path"] == (
        "configs/alerting/fd002-alert-policy-study-protocol-v1.json"
    )
    assert lineage["blocked_protocol_v1"]["sha256"] == hashlib.sha256(
        v1_bytes
    ).hexdigest()
    assert lineage["window_context_semantics"] == (
        "p1_k6_endpoint_cycle_mode_v1"
    )
    assert lineage["original_metadata_unchanged"] is True
    assert lineage["test_data_accessed"] is False
    assert lineage["threshold_selected"] is False

    comparable_v2 = json.loads(json.dumps(v2))
    comparable_v2.pop("metadata_lineage_correction")
    comparable_v2["inputs"]["metadata"] = v1["inputs"]["metadata"]
    assert comparable_v2 == v1


def test_phase5_split_and_path_allow_list_rejects_test_like_inputs() -> None:
    assert validate_allowed_split_name("train") == "train"
    assert validate_allowed_split_name("validation") == "validation"
    for split in ("test", "held_out_internal_test", "official_nasa_test"):
        with pytest.raises(ValueError):
            validate_allowed_split_name(split)
    with pytest.raises(ValueError, match="Prohibited"):
        validate_allowed_input_path(
            "data/processed/sequences_v2/p1_k6/internal_test.npy", "train"
        )
    with pytest.raises(ValueError, match="Prohibited"):
        validate_allowed_input_path("data/raw/test_FD002.txt", "validation")


def test_score_frame_requires_exact_alignment_and_rejects_duplicate_ids() -> None:
    metadata = pd.DataFrame(
        {
            "window_id": ["w1", "w2"],
            "engine": [1, 1],
            "start_cycle": [1, 2],
            "end_cycle": [30, 31],
            "max_cycle": [100, 100],
            "op_mode": [0, 1],
        }
    )
    frame = _score_frame(
        metadata,
        detector_id="lof",
        split="train",
        alert_score=np.array([0.2, 0.8]),
        raw_score=np.array([1.0, 2.0]),
    )
    assert frame["window_id"].tolist() == ["w1", "w2"]
    with pytest.raises(ValueError, match="aligned"):
        _score_frame(
            metadata,
            detector_id="lof",
            split="train",
            alert_score=np.array([0.2]),
            raw_score=np.array([1.0]),
        )
    duplicate = metadata.copy()
    duplicate.loc[1, "window_id"] = "w1"
    with pytest.raises(RuntimeError, match="unique"):
        _score_frame(
            duplicate,
            detector_id="lof",
            split="train",
            alert_score=np.array([0.2, 0.8]),
            raw_score=np.array([1.0, 2.0]),
        )


def test_atomic_json_failure_leaves_no_destination_or_temporary_file(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "result.json"
    with pytest.raises(TypeError):
        _atomic_write_json({"not_json": object()}, destination)
    assert not destination.exists()
    assert not (tmp_path / ".result.json.tmp").exists()


def test_atomic_ledger_failure_preserves_original_and_removes_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger = tmp_path / "runs.jsonl"
    append_run_record(ledger, _record("existing"))
    original = ledger.read_bytes()

    def fail_append(path: Path, record: dict) -> None:
        raise RuntimeError("fixture append failure")

    monkeypatch.setattr(workflow, "append_run_record", fail_append)
    with pytest.raises(RuntimeError, match="fixture append failure"):
        _atomically_extend_ledger(ledger, [_record("new")])
    assert ledger.read_bytes() == original
    assert load_run_ledger(ledger)[0]["run_id"] == "existing"
    assert not (tmp_path / ".runs.jsonl.phase5.tmp").exists()


@pytest.mark.parametrize(
    ("module", "entry_name"),
    [
        ("scripts.run_alert_policy_study", "turbofan-run-alert-policy-study"),
        ("scripts.verify_alert_policy_study", "turbofan-verify-alert-policy-study"),
    ],
)
def test_phase5_script_and_console_help_do_not_execute(
    module: str, entry_name: str
) -> None:
    subprocess.run(
        [sys.executable, "-m", module, "--help"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        target = tomllib.load(handle)["project"]["scripts"][entry_name]
    target_module, function_name = target.split(":", 1)
    source = f"from {target_module} import {function_name}; {function_name}()"
    subprocess.run(
        [sys.executable, "-c", source, "--help"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
