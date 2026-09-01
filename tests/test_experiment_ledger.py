from __future__ import annotations

import json
from pathlib import Path

from turbofan_anomaly.evaluation.ledger import load_run_ledger
from turbofan_anomaly.workflows.run_lstm_final_refit import (
    expected_final_refit_ledger_run_ids,
)


LEDGER = Path(__file__).resolve().parents[1] / "experiments" / "runs_v2.jsonl"


def test_current_protocol_ledger_round_trips_and_preserves_boundaries() -> None:
    raw_lines = [line for line in LEDGER.read_text(encoding="utf-8").splitlines() if line]
    records = [json.loads(line) for line in raw_lines]
    assert load_run_ledger(LEDGER) == records

    assert len(records) >= 22
    assert all(isinstance(record, dict) for record in records)
    assert all(record["schema_version"] == "2.0.0" for record in records)
    assert len({record["run_id"] for record in records}) == len(records)
    assert {record["evidence_class"] for record in records} == {
        "current_protocol",
        "validation_only",
        "validation_proxy_only",
        "confirmatory_internal_held_out_test_result",
    }
    confirmatory = [record for record in records if record["evidence_class"] == "confirmatory_internal_held_out_test_result"]
    assert len(confirmatory) == 2
    assert all(record["evidence_boundary"]["final_result"] is True for record in confirmatory)
    assert all(record["evidence_boundary"]["held_out_internal_test_accessed"] is True for record in confirmatory)
    assert all(record["evidence_boundary"]["official_nasa_test_accessed"] is False for record in confirmatory)
    final_refit_ids = set(
        expected_final_refit_ledger_run_ids("fd002-lstm-final-refit-v1")
    )
    final_refit_records = [
        record for record in records if record["run_id"] in final_refit_ids
    ]
    assert {record["run_id"] for record in final_refit_records} == final_refit_ids
    assert len(final_refit_records) == 7
    assert all(
        record["evidence_boundary"] == {
            "final_result": False,
            "threshold_selected": False,
            "held_out_internal_test_accessed": False,
        }
        for record in final_refit_records
    )
    assert all(
        record["evidence_class"] == "validation_proxy_only"
        for record in final_refit_records
    )
    assert all("\\" not in record["config"]["path"] for record in records)
    assert all("\\" not in record["split"]["path"] for record in records)
    assert all(
        json.loads(json.dumps(record, sort_keys=True)) == record for record in records
    )
