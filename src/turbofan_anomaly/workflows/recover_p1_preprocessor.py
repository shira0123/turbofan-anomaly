"""Recover the frozen FD002 P1/K=6 preprocessor from governed training lineage.

The source may contain trajectories assigned to other partitions.  Parsing is
limited to structural validation and immediate fail-closed filtering through
the protocol's exact training-engine allowlist.  Only retained training rows
may reach fitting code.  Validation is loaded only after fitted state freezes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
from typing import Any, Mapping

# K-Means reduction order must be stable across repeated recovery processes.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import joblib
import numpy as np
import pandas as pd
import sklearn

from turbofan_anomaly.alerting.persistence import apply_alert_policy
from turbofan_anomaly.alerting.thresholds import FittedThresholds
from turbofan_anomaly.data.io import FD002_COLUMNS, validate_fd002_frame
from turbofan_anomaly.data.metadata import (
    assign_endpoint_operating_modes,
    validate_p1_k6_mode_coverage,
)
from turbofan_anomaly.data.preprocessing import (
    OP_COLUMNS,
    SENSOR_COLUMNS,
    RegimeSensorPreprocessor,
    load_preprocessor,
    save_preprocessor,
)
from turbofan_anomaly.data.windows import build_window_array, summary_features
from turbofan_anomaly.evaluation.provenance import (
    find_repository_root,
    resolve_repo_path,
    sha256_file,
)
from turbofan_anomaly.evaluation.proxies import (
    registered_validation_policies,
    training_eligible_windows,
)
from turbofan_anomaly.evaluation.alerts import evaluate_alert_policy
from turbofan_anomaly.evaluation.ranking import proxy_ranking_metrics
from turbofan_anomaly.models.classical import load_baseline_artifact


DEFAULT_PROTOCOL = Path(
    "configs/preprocessing/fd002-p1-k6-recovery-protocol-v1.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--validation-source",
        type=Path,
        default=Path(
            r"C:\Users\shiva_lajayge\turbofan-project\data\splits\validation.csv"
        ),
    )
    return parser.parse_args()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _write_json(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _sha256_array(values: np.ndarray, dtype: str) -> str:
    canonical = np.ascontiguousarray(np.asarray(values, dtype=dtype))
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


def load_recovery_protocol(path: Path) -> dict[str, Any]:
    protocol = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_recovery_protocol(protocol)
    return protocol


def validate_recovery_protocol(protocol: Mapping[str, Any]) -> None:
    _require(protocol.get("schema_version") == "1.0.0", "Recovery schema changed")
    _require(
        protocol.get("protocol_id") == "fd002-p1-k6-recovery-protocol-v1",
        "Recovery protocol identity changed",
    )
    source = protocol.get("source_lineage_correction", {})
    _require(
        source.get("unavailable_historical_source_sha256")
        == "bc1d293b8dc6173c1bfb0fff64fe797c2cde35dbb1a1a075dae8ca1177b49a52",
        "Historical source-copy reference changed",
    )
    _require(
        source.get("authorized_local_source", {}).get("sha256")
        == "dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f",
        "Authorized local source hash changed",
    )
    _require(
        source.get("authorized_local_source", {}).get("size_bytes") == 9_082_480,
        "Authorized local source size changed",
    )
    membership = protocol.get("frozen_partition", {})
    train_ids = tuple(int(value) for value in membership.get("training_engine_ids", []))
    _require(len(train_ids) == 156 and len(set(train_ids)) == 156, "Training allowlist changed")
    _require(train_ids == tuple(sorted(train_ids)), "Training allowlist is not sorted")
    _require(membership.get("expected_training_rows") == 32_107, "Training row count changed")
    _require(membership.get("expected_source_engines") == 260, "Source engine count changed")
    parameters = protocol.get("frozen_preprocessing", {})
    expected = {
        "pipeline_id": "p1_k6",
        "n_clusters": 6,
        "healthy_fraction": 0.3,
        "random_state": 42,
        "n_init": 20,
        "min_mode_fit_rows": 30,
    }
    for key, value in expected.items():
        _require(parameters.get(key) == value, f"Frozen preprocessing changed: {key}")
    boundary = protocol.get("access_boundary", {})
    _require(boundary.get("raw_run_to_failure_source_opened_for_partition_reconstruction") is True, "Raw-source access not registered")
    for field in (
        "internal_held_out_split_artifact_opened",
        "official_nasa_test_artifact_opened",
        "held_out_rows_retained",
        "held_out_rows_summarized",
        "held_out_rows_exported",
        "held_out_rows_used_for_fit_selection_or_evaluation",
        "confirmatory_evaluation_executed",
    ):
        _require(boundary.get(field) is False, f"Forbidden access registered: {field}")
    routes = protocol.get("acceptance_routes", {})
    _require(set(routes) == {"route_a", "route_b"}, "Recovery routes changed")
    _require(
        routes["route_a"].get("legacy_training_csv_sha256")
        == "fd02f93b96a0e9a9022b165b7a6a7f4ce884d8c58ea57844ab0ad5419fe1c8b9",
        "Legacy split hash changed",
    )


def manifest_memberships(manifest: Mapping[str, Any]) -> dict[str, tuple[int, ...]]:
    memberships = {
        split: tuple(
            sorted(
                int(record["engine"])
                for record in manifest["engines"]
                if record["split"] == split
            )
        )
        for split in ("train", "validation", "test")
    }
    all_ids = [engine for ids in memberships.values() for engine in ids]
    _require(len(all_ids) == len(set(all_ids)), "Manifest partition memberships overlap")
    return memberships


def validate_reconstructed_training_frame(
    frame: pd.DataFrame,
    *,
    train_ids: tuple[int, ...],
    forbidden_ids: set[int],
    expected_rows: int,
) -> None:
    _require(list(frame.columns) == FD002_COLUMNS, "Training schema or column order changed")
    validate_fd002_frame(frame)
    _require(len(frame) == expected_rows, "Reconstructed training row count changed")
    observed = tuple(sorted(frame["engine"].astype(int).unique()))
    _require(observed == train_ids, "Reconstructed training membership changed")
    _require(not (set(observed) & forbidden_ids), "Non-training engine retained")
    expected_order = frame.sort_values(["engine", "cycle"], kind="stable").index
    _require(expected_order.equals(frame.index), "Training rows are not deterministically ordered")
    numeric = frame.loc[:, [*OP_COLUMNS, *SENSOR_COLUMNS]].to_numpy(dtype=float)
    _require(np.isfinite(numeric).all(), "Training operating settings or sensors are non-finite")


def reconstruct_training_partition(
    source_path: Path,
    manifest: Mapping[str, Any],
    protocol: Mapping[str, Any],
    *,
    chunk_size: int = 4096,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Structurally validate the source and retain only allowlisted train rows."""
    source = Path(source_path)
    lineage = protocol["source_lineage_correction"]["authorized_local_source"]
    _require(source.stat().st_size == int(lineage["size_bytes"]), "Source size mismatch")
    _require(sha256_file(source) == lineage["sha256"], "Source SHA-256 mismatch")
    memberships = manifest_memberships(manifest)
    train_ids = tuple(int(value) for value in protocol["frozen_partition"]["training_engine_ids"])
    _require(train_ids == memberships["train"], "Protocol allowlist differs from manifest")
    manifest_all_ids = set().union(*map(set, memberships.values()))
    observed_source_ids: set[int] = set()
    last_cycle: dict[int, int] = {}
    retained: list[pd.DataFrame] = []
    source_rows = 0
    for chunk in pd.read_csv(
        source,
        sep=r"\s+",
        header=None,
        names=FD002_COLUMNS,
        chunksize=chunk_size,
    ):
        _require(chunk.shape[1] == 26, "Source does not have 26 columns")
        source_rows += len(chunk)
        engines = chunk["engine"].to_numpy(dtype=int)
        cycles = chunk["cycle"].to_numpy(dtype=int)
        values = chunk.loc[:, [*OP_COLUMNS, *SENSOR_COLUMNS]].to_numpy(dtype=float)
        _require(np.isfinite(values).all(), "Source contains non-finite values")
        for engine, cycle in zip(engines, cycles, strict=True):
            engine_id = int(engine)
            cycle_id = int(cycle)
            _require(engine_id in manifest_all_ids, "Source contains unknown engine ID")
            previous = last_cycle.get(engine_id)
            _require(previous is None or cycle_id == previous + 1, "Source keys are duplicate or unordered")
            last_cycle[engine_id] = cycle_id
            observed_source_ids.add(engine_id)
        train_mask = chunk["engine"].astype(int).isin(train_ids)
        if train_mask.any():
            retained.append(chunk.loc[train_mask, FD002_COLUMNS].copy())
    _require(len(observed_source_ids) == protocol["frozen_partition"]["expected_source_engines"], "Source engine count mismatch")
    _require(observed_source_ids == manifest_all_ids, "Source engines differ from manifest")
    _require(source_rows == int(manifest["dataset"]["rows"]), "Source row count differs from manifest")
    training = pd.concat(retained, ignore_index=True)
    training = training.sort_values(["engine", "cycle"], kind="stable").reset_index(drop=True)
    validate_reconstructed_training_frame(
        training,
        train_ids=train_ids,
        forbidden_ids=set(memberships["validation"]) | set(memberships["test"]),
        expected_rows=int(protocol["frozen_partition"]["expected_training_rows"]),
    )
    return training, {
        "source_rows_structurally_validated": source_rows,
        "source_engine_count": len(observed_source_ids),
        "retained_training_rows": len(training),
        "retained_training_engines": len(train_ids),
        **protocol["access_boundary"],
    }


def derive_canonical_mode_mapping(
    raw_modes: np.ndarray,
    registered_modes: np.ndarray,
    *,
    n_clusters: int = 6,
) -> dict[int, int]:
    raw = np.asarray(raw_modes, dtype=int).reshape(-1)
    registered = np.asarray(registered_modes, dtype=int).reshape(-1)
    _require(len(raw) == len(registered), "Mode vectors differ in length")
    expected = set(range(n_clusters))
    _require(set(raw) == expected and set(registered) == expected, "Six-mode coverage changed")
    mapping: dict[int, int] = {}
    for raw_mode in range(n_clusters):
        targets = np.unique(registered[raw == raw_mode])
        _require(len(targets) == 1, "K-Means mismatch is not a label permutation")
        mapping[raw_mode] = int(targets[0])
    _require(set(mapping.values()) == expected, "Mode mapping is not one-to-one")
    remapped = np.fromiter((mapping[int(value)] for value in raw), dtype=int)
    _require(np.array_equal(remapped, registered), "Canonical mode agreement is not exact")
    return mapping


def compare_cycle_frames(
    observed: pd.DataFrame,
    registered: pd.DataFrame,
    *,
    rtol: float,
    atol: float,
) -> dict[str, Any]:
    identity = ["engine", "cycle", *OP_COLUMNS]
    _require(observed[identity].equals(registered[identity]), "Cycle-frame identity changed")
    _require(np.array_equal(observed["op_mode"], registered["op_mode"]), "Operating modes changed")
    left = observed.loc[:, list(SENSOR_COLUMNS)].to_numpy(dtype=float)
    right = registered.loc[:, list(SENSOR_COLUMNS)].to_numpy(dtype=float)
    difference = np.abs(left - right)
    _require(np.allclose(left, right, rtol=rtol, atol=atol), "Transformed sensor values exceed tolerance")
    return {
        "rows": len(observed),
        "maximum_absolute_sensor_difference": float(difference.max(initial=0.0)),
        "mode_counts": {
            str(mode): int(count)
            for mode, count in observed["op_mode"].value_counts().sort_index().items()
        },
    }


def compare_arrays(
    observed: np.ndarray,
    registered: np.ndarray,
    *,
    rtol: float,
    atol: float,
) -> dict[str, Any]:
    _require(observed.shape == registered.shape, "Sequence shape changed")
    difference = np.abs(observed.astype(float) - registered.astype(float))
    exact = bool(np.array_equal(observed, registered))
    _require(exact or np.allclose(observed, registered, rtol=rtol, atol=atol), "Sequence values exceed tolerance")
    return {
        "shape": list(observed.shape),
        "exact": exact,
        "maximum_absolute_difference": float(difference.max(initial=0.0)),
    }


def compare_endpoint_context(
    observed: pd.DataFrame, registered: pd.DataFrame
) -> None:
    """Require exact metadata values while accepting nullable integer dtype."""
    _require(observed.shape == registered.shape, "Endpoint context shape changed")
    _require(
        observed.columns.tolist() == registered.columns.tolist(),
        "Endpoint context columns changed",
    )
    for column in observed.columns:
        if column == "op_mode":
            left = pd.to_numeric(observed[column], errors="raise").to_numpy(dtype=int)
            right = pd.to_numeric(registered[column], errors="raise").to_numpy(dtype=int)
            _require(np.array_equal(left, right), "Endpoint operating modes changed")
        else:
            _require(
                observed[column].equals(registered[column]),
                f"Endpoint context values changed: {column}",
            )


def select_recovery_route(
    reconstructed_sha256: str, legacy_sha256: str
) -> str:
    """Classify byte-exact versus governed semantic reconstruction."""
    if reconstructed_sha256 == legacy_sha256:
        return "route_a_byte_exact"
    return "route_b_governed_semantic_reconstruction"


def preprocessor_state_fingerprints(preprocessor: RegimeSensorPreprocessor) -> dict[str, Any]:
    preprocessor._require_fitted()
    assert preprocessor.op_scaler_ is not None
    assert preprocessor.kmeans_ is not None
    assert preprocessor.global_sensor_scaler_ is not None
    scalers: dict[str, Any] = {}
    for raw_mode, scaler in sorted(preprocessor.sensor_scalers_per_mode_.items()):
        canonical = preprocessor.canonical_mode_mapping_[raw_mode]
        scalers[str(canonical)] = {
            "mean_sha256_float64_le": _sha256_array(scaler.mean_, "<f8"),
            "scale_sha256_float64_le": _sha256_array(scaler.scale_, "<f8"),
            "variance_sha256_float64_le": _sha256_array(scaler.var_, "<f8"),
            "sample_count": int(preprocessor.sensor_fit_rows_per_mode_[raw_mode]),
        }
    return {
        "operating_scaler_mean_sha256_float64_le": _sha256_array(preprocessor.op_scaler_.mean_, "<f8"),
        "operating_scaler_scale_sha256_float64_le": _sha256_array(preprocessor.op_scaler_.scale_, "<f8"),
        "kmeans_centers_sha256_float64_le": _sha256_array(preprocessor.kmeans_.cluster_centers_, "<f8"),
        "kmeans_inertia": float(preprocessor.kmeans_.inertia_),
        "canonical_mode_mapping": {str(k): v for k, v in sorted(preprocessor.canonical_mode_mapping_.items())},
        "global_sensor_mean_sha256_float64_le": _sha256_array(preprocessor.global_sensor_scaler_.mean_, "<f8"),
        "per_mode_sensor_scalers": scalers,
    }


def verify_frozen_phase5_policy(
    validation_metadata: pd.DataFrame,
    raw_scores: np.ndarray,
    calibrated_scores: np.ndarray,
    repo_root: Path,
    *,
    atol: float,
) -> dict[str, Any]:
    """Apply the already frozen Gate 4 policy without refitting thresholds."""
    final_protocol_path = repo_root / "configs/evaluation/fd002-final-evaluation-protocol-v1.json"
    _require(
        sha256_file(final_protocol_path)
        == "ed5d3ca6a847365256a238684086266fae8bab72a79ff6b4f9d8af3fa6a84133",
        "Protected final-evaluation v1 protocol changed",
    )
    final_protocol = json.loads(final_protocol_path.read_text(encoding="utf-8"))
    policy = final_protocol["frozen_primary_alert_policy"]
    threshold_rows = policy["thresholds"]
    thresholds = FittedThresholds(
        context="per_mode",
        rule_id="quantile_0.995",
        values={int(row["operating_mode"]): float(row["threshold"]) for row in threshold_rows},
        reference_counts={int(row["operating_mode"]): int(row["reference_count"]) for row in threshold_rows},
    )
    score_frame = validation_metadata[
        ["window_id", "engine", "start_cycle", "end_cycle", "max_cycle", "op_mode"]
    ].copy()
    score_frame["raw_score"] = np.asarray(raw_scores, dtype=float)
    score_frame["alert_score"] = np.asarray(calibrated_scores, dtype=float)
    score_frame["detector_id"] = "pca_reconstruction"
    score_frame["pipeline_id"] = "p1_k6"
    score_frame["split"] = "validation"
    trace = apply_alert_policy(
        score_frame,
        thresholds,
        ewma_alpha=float(policy["ewma_alpha"]),
        persistence=int(policy["persistence"]),
    )
    trace.insert(0, "candidate_id", policy["candidate_id"])

    results_path = repo_root / "configs/alerting/fd002-alert-policy-study-results-v1.json"
    _require(
        sha256_file(results_path)
        == "57080e52d05d6b95747c831fcf819a606d334cf874257421847a5c24aacb8ac2",
        "Registered Phase 5 results authority changed",
    )
    results = json.loads(results_path.read_text(encoding="utf-8"))
    report_dir = repo_root / "reports/alerting_v1/fd002-alert-policy-study-v1"
    report_hashes = results["outputs"]["report_sha256"]
    for filename in (
        "candidate_policy_metrics.csv",
        "overall_recommendation.csv",
        "selected_validation_alert_trace.csv",
        "target_attainment.csv",
    ):
        _require(
            sha256_file(report_dir / filename) == report_hashes[filename],
            f"Registered Phase 5 report changed: {filename}",
        )
    registered_trace = pd.read_csv(report_dir / "selected_validation_alert_trace.csv")
    _require(trace.columns.tolist() == registered_trace.columns.tolist(), "Selected alert trace columns changed")
    maximum_float_difference = 0.0
    for column in trace.columns:
        if pd.api.types.is_float_dtype(registered_trace[column]):
            left = trace[column].to_numpy(dtype=float)
            right = registered_trace[column].to_numpy(dtype=float)
            difference = float(np.max(np.abs(left - right)))
            maximum_float_difference = max(maximum_float_difference, difference)
            _require(np.allclose(left, right, rtol=0.0, atol=atol), f"Selected alert trace changed: {column}")
        else:
            _require(
                trace[column].astype(str).tolist()
                == registered_trace[column].astype(str).tolist(),
                f"Selected alert trace changed: {column}",
            )

    registered_metrics = pd.read_csv(report_dir / "candidate_policy_metrics.csv")
    registered_metrics = registered_metrics[
        registered_metrics["candidate_id"] == policy["candidate_id"]
    ].set_index("policy_id")
    maximum_metric_difference = 0.0
    for proxy in registered_validation_policies():
        policy_frame = proxy.apply(validation_metadata)
        observed_metric, _, _ = evaluate_alert_policy(trace, policy_frame)
        registered = registered_metrics.loc[observed_metric["policy_id"]]
        for key, value in observed_metric.items():
            expected = registered.name if key == "policy_id" else registered[key]
            if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, (bool, np.bool_)):
                if pd.isna(value) and pd.isna(expected):
                    continue
                difference = abs(float(value) - float(expected))
                maximum_metric_difference = max(maximum_metric_difference, difference)
                _require(difference <= atol, f"Phase 5 alert metric changed: {key}")
            else:
                _require(value == expected, f"Phase 5 alert metric changed: {key}")
    recommendation = pd.read_csv(report_dir / "overall_recommendation.csv")
    target = pd.read_csv(report_dir / "target_attainment.csv")
    _require(len(recommendation) == 1, "Registered Phase 5 recommendation changed")
    _require(recommendation.iloc[0]["candidate_id"] == policy["candidate_id"], "Phase 5 selected candidate changed")
    _require(set(target["candidate_id"]) == {policy["candidate_id"]}, "Phase 5 target evidence changed")
    return {
        "candidate_id": policy["candidate_id"],
        "threshold_source": "frozen_final_evaluation_protocol_v1_no_refit",
        "thresholds_exact": True,
        "selected_trace_rows": len(trace),
        "maximum_selected_trace_float_difference": maximum_float_difference,
        "maximum_alert_metric_difference": maximum_metric_difference,
        "candidate_policy_count": len(registered_metrics),
        "overall_recommendation_exact": True,
        "target_attainment_exact": True,
        "threshold_refitted_or_selected": False,
    }


def assert_ignored_untracked(repo_root: Path, path: Path) -> None:
    relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
    tracked = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", relative],
        capture_output=True,
        text=True,
        check=False,
    )
    _require(tracked.returncode != 0, f"Local artifact is tracked: {relative}")
    ignored = subprocess.run(
        ["git", "-C", str(repo_root), "check-ignore", "--", relative],
        capture_output=True,
        text=True,
        check=False,
    )
    _require(ignored.returncode == 0, f"Local artifact is not ignored: {relative}")


def _registered_paths(protocol: Mapping[str, Any], repo_root: Path) -> dict[str, Path]:
    resolved = {
        key: resolve_repo_path(reference["path"], repo_root)
        for key, reference in protocol["registered_reproduction_targets"].items()
    }
    for key, path in resolved.items():
        expected = protocol["registered_reproduction_targets"][key]["sha256"]
        _require(path.is_file(), f"Registered reproduction target is missing: {key}")
        _require(sha256_file(path) == expected, f"Registered reproduction target hash changed: {key}")
    return resolved


def execute_recovery(
    protocol: Mapping[str, Any],
    repo_root: Path,
    validation_source: Path,
) -> dict[str, Any]:
    manifest_path = resolve_repo_path(protocol["frozen_partition"]["manifest_path"], repo_root)
    _require(sha256_file(manifest_path) == protocol["frozen_partition"]["manifest_sha256"], "Split manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = resolve_repo_path(protocol["source_lineage_correction"]["authorized_local_source"]["path"], repo_root)
    assert_ignored_untracked(repo_root, source_path)
    train, access_audit = reconstruct_training_partition(source_path, manifest, protocol)

    split_dir = repo_root / "data" / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    train_path = split_dir / "train.csv"
    train.to_csv(train_path, index=False, lineterminator="\n")
    assert_ignored_untracked(repo_root, train_path)
    train_hash = sha256_file(train_path)
    legacy_hash = protocol["acceptance_routes"]["route_a"]["legacy_training_csv_sha256"]
    route = select_recovery_route(train_hash, legacy_hash)

    validation_expected = protocol["registered_validation_split"]
    _require(Path(validation_source).is_file(), "Registered validation source is unavailable")
    _require(sha256_file(validation_source) == validation_expected["sha256"], "Validation source hash mismatch")
    validation_path = split_dir / "validation.csv"
    validation_path.write_bytes(Path(validation_source).read_bytes())
    assert_ignored_untracked(repo_root, validation_path)
    _require(sha256_file(validation_path) == validation_expected["sha256"], "Provisioned validation hash mismatch")
    validation = pd.read_csv(validation_path)
    validate_fd002_frame(validation)
    memberships = manifest_memberships(manifest)
    _require(len(validation) == validation_expected["rows"], "Validation row count changed")
    _require(tuple(sorted(validation["engine"].astype(int).unique())) == memberships["validation"], "Validation membership changed")
    _require(not (set(train["engine"].astype(int)) & set(validation["engine"].astype(int))), "Train/validation overlap")

    frozen = protocol["frozen_preprocessing"]
    preprocessor = RegimeSensorPreprocessor(
        split_manifest_id=manifest["manifest_id"],
        n_clusters=frozen["n_clusters"],
        healthy_fraction=frozen["healthy_fraction"],
        random_state=frozen["random_state"],
        n_init=frozen["n_init"],
        min_mode_fit_rows=frozen["min_mode_fit_rows"],
    ).fit(train)
    targets = _registered_paths(protocol, repo_root)
    registered_train = pd.read_csv(targets["training_cycle_frame"])
    identity = ["engine", "cycle", *OP_COLUMNS]
    _require(train[identity].equals(registered_train[identity]), "Reconstructed training identity differs from registered P1 frame")
    mapping = derive_canonical_mode_mapping(
        preprocessor.predict_raw_modes(train),
        registered_train["op_mode"].to_numpy(dtype=int),
    )
    preprocessor.set_canonical_mode_mapping(mapping)
    transformed_train = preprocessor.transform(train)

    artifact_path = resolve_repo_path(protocol["outputs"]["preprocessor_path"], repo_root)
    save_preprocessor(preprocessor, artifact_path)
    assert_ignored_untracked(repo_root, artifact_path)
    reloaded, metadata = load_preprocessor(
        artifact_path, expected_split_manifest_id=manifest["manifest_id"]
    )
    reloaded_train = reloaded.transform(train)
    _require(np.array_equal(transformed_train["op_mode"], reloaded_train["op_mode"]), "Reloaded modes changed")
    reload_max = float(
        np.max(
            np.abs(
                transformed_train.loc[:, list(SENSOR_COLUMNS)].to_numpy(dtype=float)
                - reloaded_train.loc[:, list(SENSOR_COLUMNS)].to_numpy(dtype=float)
            )
        )
    )
    _require(reload_max == 0.0, "Reloaded training transform changed")

    transformed_validation = reloaded.transform(validation)
    registered_validation = pd.read_csv(targets["validation_cycle_frame"])
    tolerances = protocol["reproduction_tolerances"]
    train_cycle = compare_cycle_frames(
        transformed_train,
        registered_train,
        rtol=tolerances["float64_transforms"]["rtol"],
        atol=tolerances["float64_transforms"]["atol"],
    )
    validation_cycle = compare_cycle_frames(
        transformed_validation,
        registered_validation,
        rtol=tolerances["float64_transforms"]["rtol"],
        atol=tolerances["float64_transforms"]["atol"],
    )

    original_train_metadata = pd.read_csv(targets["original_training_metadata"])
    original_validation_metadata = pd.read_csv(targets["original_validation_metadata"])
    observed_train_context = assign_endpoint_operating_modes(original_train_metadata, transformed_train)
    observed_validation_context = assign_endpoint_operating_modes(original_validation_metadata, transformed_validation)
    registered_train_context = pd.read_csv(targets["training_endpoint_context"])
    registered_validation_context = pd.read_csv(targets["validation_endpoint_context"])
    compare_endpoint_context(observed_train_context, registered_train_context)
    compare_endpoint_context(observed_validation_context, registered_validation_context)
    eligible_context = training_eligible_windows(
        observed_train_context, frozen["healthy_fraction"]
    ).to_numpy(dtype=bool)
    coverage = validate_p1_k6_mode_coverage(
        observed_train_context,
        observed_validation_context,
        eligible_context,
        minimum_eligible_training_windows_per_mode=100,
        expected_eligible_training_windows=5037,
    )

    observed_train_sequences = build_window_array(transformed_train, observed_train_context)
    observed_validation_sequences = build_window_array(transformed_validation, observed_validation_context)
    registered_train_sequences = np.load(targets["training_sequences"], allow_pickle=False, mmap_mode="r")
    registered_validation_sequences = np.load(targets["validation_sequences"], allow_pickle=False, mmap_mode="r")
    train_sequences = compare_arrays(
        observed_train_sequences,
        registered_train_sequences,
        rtol=tolerances["float32_sequences"]["rtol"],
        atol=tolerances["float32_sequences"]["atol"],
    )
    validation_sequences = compare_arrays(
        observed_validation_sequences,
        registered_validation_sequences,
        rtol=tolerances["float32_sequences"]["rtol"],
        atol=tolerances["float32_sequences"]["atol"],
    )

    pca_path = targets["frozen_pca_bundle"]
    pca_model, pca_metadata = load_baseline_artifact(
        pca_path,
        expected_split_manifest_id=manifest["manifest_id"],
        expected_preprocessing_decision_id="fd002-preprocessing-selection-v1",
    )
    eligible = eligible_context
    _require(int(eligible.sum()) == 5037, "Eligible PCA training-window count changed")
    train_features = summary_features(observed_train_sequences[eligible])
    validation_features = summary_features(observed_validation_sequences)
    observed_train_raw, observed_train_scores = pca_model.score(train_features)
    observed_raw, observed_scores = pca_model.score(validation_features)
    registered_scores = pd.read_csv(targets["registered_validation_scores"])
    registered_scores = registered_scores[
        (registered_scores["pipeline"] == "p1_k6")
        & (registered_scores["detector"] == "pca")
    ].reset_index(drop=True)
    _require(registered_scores["window_id"].tolist() == observed_validation_context["window_id"].tolist(), "PCA score window order changed")
    raw_diff = float(np.max(np.abs(observed_raw - registered_scores["raw_score"].to_numpy(dtype=float))))
    score_diff = float(np.max(np.abs(observed_scores - registered_scores["calibrated_score"].to_numpy(dtype=float))))
    score_tolerance = tolerances["pca_scores"]
    _require(np.allclose(observed_raw, registered_scores["raw_score"], rtol=score_tolerance["rtol"], atol=score_tolerance["atol"]), "PCA raw scores exceed tolerance")
    _require(np.allclose(observed_scores, registered_scores["calibrated_score"], rtol=score_tolerance["rtol"], atol=score_tolerance["atol"]), "PCA calibrated scores exceed tolerance")
    _, mean_pr, mean_roc = proxy_ranking_metrics(
        observed_scores,
        [policy.apply(observed_validation_context) for policy in registered_validation_policies()],
    )
    expected_metrics = protocol["registered_phase5_pca_metrics"]
    metric_diff = max(abs(mean_pr - expected_metrics["mean_pr_auc"]), abs(mean_roc - expected_metrics["mean_roc_auc"]))
    _require(metric_diff <= score_tolerance["atol"], "PCA ranking metrics exceed tolerance")
    phase5_policy = verify_frozen_phase5_policy(
        observed_validation_context,
        observed_raw,
        observed_scores,
        repo_root,
        atol=score_tolerance["atol"],
    )

    result = {
        "schema_version": "1.0.0",
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": sha256_file(resolve_repo_path(DEFAULT_PROTOCOL, repo_root)),
        "status": "verified_recovery_complete_before_test_access",
        "selected_recovery_route": route,
        "source_lineage": {
            "unavailable_historical_source_sha256": protocol["source_lineage_correction"]["unavailable_historical_source_sha256"],
            "authorized_local_source_sha256": sha256_file(source_path),
            "authorized_local_source_size_bytes": source_path.stat().st_size,
            "split_manifest_sha256": sha256_file(manifest_path),
            "reconstructed_training_csv_sha256": train_hash,
            "validation_csv_sha256": sha256_file(validation_path),
        },
        "access_audit": access_audit,
        "preprocessor": {
            "path": protocol["outputs"]["preprocessor_path"],
            "sha256": sha256_file(artifact_path),
            "size_bytes": artifact_path.stat().st_size,
            "class": f"{type(reloaded).__module__}.{type(reloaded).__qualname__}",
            "metadata": json.loads(json.dumps(metadata)),
            "state_fingerprints": preprocessor_state_fingerprints(reloaded),
            "reload_maximum_absolute_difference": reload_max,
        },
        "reproduction": {
            "training_cycle_frame": train_cycle,
            "validation_cycle_frame": validation_cycle,
            "training_sequences": train_sequences,
            "validation_sequences": validation_sequences,
            "endpoint_context_exact": {"train": True, "validation": True},
            "mode_coverage": coverage,
            "pca": {
                "bundle_sha256": sha256_file(pca_path),
                "metadata": pca_metadata,
                "maximum_raw_score_difference": raw_diff,
                "maximum_calibrated_score_difference": score_diff,
                "selection_mean_pr_auc": mean_pr,
                "selection_mean_roc_auc": mean_roc,
                "maximum_ranking_metric_difference": metric_diff,
                "training_score_count": len(observed_train_raw),
                "validation_score_count": len(observed_raw),
            },
            "phase5_alert_policy": phase5_policy,
            "frozen_gate_4_candidate": protocol["frozen_gate_4_candidate"],
            "threshold_refitted_or_selected": False,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
            "platform": platform.platform(),
            "native_math_threads": 1,
        },
    }
    result_path = resolve_repo_path(protocol["outputs"]["result_path"], repo_root)
    _write_json(result, result_path)
    return result


def main() -> None:
    args = parse_args()
    repo_root = find_repository_root(Path.cwd())
    protocol_path = resolve_repo_path(args.protocol, repo_root)
    protocol = load_recovery_protocol(protocol_path)
    result = execute_recovery(protocol, repo_root, args.validation_source)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
