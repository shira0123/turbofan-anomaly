"""Versioned JSONL experiment-ledger validation and append-only writing."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from turbofan_anomaly.evaluation.provenance import canonical_repo_relative


LEDGER_SCHEMA_VERSION = "2.0.0"
REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "source_run_id",
        "timestamp",
        "owner",
        "experiment_name",
        "model",
        "parameters",
        "population",
        "metric",
        "evidence_class",
        "result_classification",
        "evidence_boundary",
        "split",
        "config",
        "artifact",
        "notes",
        "provenance",
    }
)


def validate_run_record(record: Mapping[str, Any]) -> None:
    """Validate the active schema and frozen-evaluation safety boundary."""
    missing = REQUIRED_FIELDS - set(record)
    if missing:
        raise ValueError(f"Ledger record is missing fields: {sorted(missing)}")
    if record["schema_version"] != LEDGER_SCHEMA_VERSION:
        raise ValueError(f"Unsupported ledger schema: {record['schema_version']!r}")
    if not isinstance(record["run_id"], str) or not record["run_id"]:
        raise ValueError("Ledger run_id must be a non-empty string")
    if not isinstance(record["parameters"], Mapping):
        raise ValueError("Ledger parameters must be a JSON object")
    boundary = record["evidence_boundary"]
    for field in ("final_result", "threshold_selected", "held_out_internal_test_accessed"):
        if not isinstance(boundary.get(field), bool):
            raise ValueError(f"Evidence boundary {field} must be boolean")
    if boundary["held_out_internal_test_accessed"]:
        if record["evidence_class"] != "confirmatory_internal_held_out_test_result":
            raise ValueError("Only confirmatory result records may claim internal-test access")
        if boundary["final_result"] is not True:
            raise ValueError("A confirmatory held-out record must be final")
        if boundary.get("official_nasa_test_accessed") is not False:
            raise ValueError("Confirmatory records must explicitly deny official-test access")
    for identity in ("split", "config", "artifact"):
        value = record[identity]
        if not isinstance(value, Mapping):
            raise ValueError(f"Ledger {identity} must be a JSON object")
        canonical_repo_relative(value["path"])


def load_run_ledger(path: Path) -> list[dict[str, Any]]:
    """Load, validate, and uniqueness-check every nonblank JSONL record."""
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid ledger JSON on line {line_number}") from error
        if not isinstance(record, dict):
            raise ValueError(f"Ledger line {line_number} must contain a JSON object")
        validate_run_record(record)
        run_id = record["run_id"]
        if run_id in seen:
            raise ValueError(f"Duplicate ledger run_id: {run_id}")
        seen.add(run_id)
        records.append(record)
    return records


def append_run_record(path: Path, record: Mapping[str, Any]) -> None:
    """Append one validated, unique record using canonical one-line JSON and LF."""
    validate_run_record(record)
    destination = Path(path)
    existing = load_run_ledger(destination) if destination.exists() else []
    if record["run_id"] in {item["run_id"] for item in existing}:
        raise ValueError(f"Duplicate ledger run_id: {record['run_id']}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(record), ensure_ascii=False, separators=(",", ":"))
    with destination.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(payload + "\n")
