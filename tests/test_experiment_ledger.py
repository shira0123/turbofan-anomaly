from __future__ import annotations

import json
from pathlib import Path

from turbofan_anomaly.evaluation.ledger import load_run_ledger


LEDGER = Path(__file__).resolve().parents[1] / "experiments" / "runs_v2.jsonl"


def test_current_protocol_ledger_round_trips_and_preserves_boundaries() -> None:
    raw_lines = [line for line in LEDGER.read_text(encoding="utf-8").splitlines() if line]
    records = [json.loads(line) for line in raw_lines]
    assert load_run_ledger(LEDGER) == records

    assert len(records) == 22
    assert all(isinstance(record, dict) for record in records)
    assert all(record["schema_version"] == "2.0.0" for record in records)
    assert len({record["run_id"] for record in records}) == len(records)
    assert {record["evidence_class"] for record in records} == {
        "current_protocol",
        "validation_only",
        "validation_proxy_only",
    }
    assert all(record["evidence_boundary"]["final_result"] is False for record in records)
    assert all(
        record["evidence_boundary"]["held_out_internal_test_accessed"] is False
        for record in records
    )
    assert all("\\" not in record["config"]["path"] for record in records)
    assert all("\\" not in record["split"]["path"] for record in records)
    assert all(
        json.loads(json.dumps(record, sort_keys=True)) == record for record in records
    )
