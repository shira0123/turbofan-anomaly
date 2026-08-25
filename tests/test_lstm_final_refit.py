from __future__ import annotations

import inspect
import json
from pathlib import Path
import subprocess
import sys
import tomllib

import numpy as np
import pandas as pd
import pytest
import torch

from turbofan_anomaly.alerting.calibration import EmpiricalCDFCalibrator
from turbofan_anomaly.evaluation.ledger import append_run_record, load_run_ledger
from turbofan_anomaly.evaluation.provenance import verify_registered_hash
from turbofan_anomaly.models.lstm_training import (
    FixedEpochSettings,
    LSTMArchitecture,
    aligned_calibrated_score_ensemble,
    ensure_output_paths_available,
    final_refit_artifact_name,
    fit_lstm_autoencoder_fixed_epochs,
    load_lstm_artifact,
    median_locked_epoch,
    reconstruction_errors,
    save_lstm_artifact,
    validate_sequence_collection,
)
from turbofan_anomaly.workflows.run_lstm_final_refit import (
    REGISTERED_SEEDS,
    _ledger_records,
    expected_final_refit_ledger_run_ids,
    validate_allowed_input_path,
    validate_allowed_split_name,
    validate_final_refit_protocol,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    REPO_ROOT / "configs" / "lstm" / "fd002-lstm-final-refit-protocol-v1.json"
)


def _tiny_sequences() -> np.ndarray:
    return np.random.default_rng(17).normal(size=(6, 4, 3)).astype(np.float32)


def _tiny_fixed_fit() -> tuple:
    architecture = LSTMArchitecture("tiny", 4, 2, 1, 0.0)
    settings = FixedEpochSettings(
        batch_size=3,
        epoch_count=2,
        learning_rate=0.001,
        weight_decay=0.0,
        gradient_clip_norm=1.0,
    )
    result = fit_lstm_autoencoder_fixed_epochs(
        _tiny_sequences(),
        architecture=architecture,
        settings=settings,
        seed=43,
        device=torch.device("cpu"),
    )
    return architecture, settings, result


def test_fixed_epoch_fit_has_no_monitor_and_runs_exact_epoch_count() -> None:
    signature = inspect.signature(fit_lstm_autoencoder_fixed_epochs)
    assert "monitor_sequences" not in signature.parameters
    assert "validation_sequences" not in signature.parameters
    _, settings, result = _tiny_fixed_fit()
    assert [row["epoch"] for row in result.history] == [1, 2]
    assert len(result.history) == settings.epoch_count
    assert all(np.isfinite(row["training_loss"]) for row in result.history)


def test_fixed_epoch_fit_is_repeatable_on_small_cpu_fixture() -> None:
    architecture, settings, first = _tiny_fixed_fit()
    second = fit_lstm_autoencoder_fixed_epochs(
        _tiny_sequences(),
        architecture=architecture,
        settings=settings,
        seed=43,
        device=torch.device("cpu"),
    )
    assert first.history == second.history
    for name, value in first.model.state_dict().items():
        assert torch.equal(value, second.model.state_dict()[name])


@pytest.mark.parametrize(
    ("epochs", "expected"),
    [([12, 8, 10], 10), ([1, 2, 3], 2), ([7, 7, 9], 7)],
)
def test_median_epoch_rule(epochs: list[int], expected: int) -> None:
    assert median_locked_epoch(epochs) == expected


@pytest.mark.parametrize(
    "invalid", [[], [1, 2], [1, 2, 3, 4], [0, 1, 2], [1, -2, 3], [1, 2, 3.0], [True, 2, 3]]
)
def test_median_epoch_rule_rejects_invalid_registration(invalid: list) -> None:
    with pytest.raises(ValueError):
        median_locked_epoch(invalid)


def test_per_seed_artifact_names_are_unique_and_outputs_cannot_collide(
    tmp_path: Path,
) -> None:
    names = [final_refit_artifact_name(seed) for seed in (43, 44, 45)]
    assert len(set(names)) == 3
    destinations = [tmp_path / name for name in names]
    ensure_output_paths_available(destinations)
    destinations[0].write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        ensure_output_paths_available(destinations)
    with pytest.raises(ValueError):
        ensure_output_paths_available([destinations[1], destinations[1]])


def _score_frames() -> dict[int, pd.DataFrame]:
    return {
        43: pd.DataFrame(
            {"window_id": ["w1", "w2"], "calibrated_score": [0.1, 0.7]}
        ),
        44: pd.DataFrame(
            {"window_id": ["w2", "w1"], "calibrated_score": [0.8, 0.2]}
        ),
        45: pd.DataFrame(
            {"window_id": ["w1", "w2"], "calibrated_score": [0.3, 0.9]}
        ),
    }


def test_calibrated_ensemble_aligns_reordered_window_ids() -> None:
    ensemble = aligned_calibrated_score_ensemble(_score_frames())
    assert ensemble["window_id"].tolist() == ["w1", "w2"]
    assert np.allclose(ensemble["ensemble_calibrated_score"], [0.2, 0.8])


def test_calibrated_ensemble_rejects_missing_and_duplicate_ids() -> None:
    missing = _score_frames()
    missing[44] = missing[44].iloc[:1]
    with pytest.raises(ValueError, match="not identical"):
        aligned_calibrated_score_ensemble(missing)

    duplicate = _score_frames()
    duplicate[45] = pd.DataFrame(
        {"window_id": ["w1", "w1"], "calibrated_score": [0.3, 0.9]}
    )
    with pytest.raises(ValueError, match="duplicate"):
        aligned_calibrated_score_ensemble(duplicate)


def test_empirical_cdf_stays_fitted_to_training_scores_and_preserves_direction() -> None:
    training = np.array([1.0, 2.0, 4.0])
    calibrator = EmpiricalCDFCalibrator().fit(training)
    frozen_reference = calibrator.sorted_training_scores_.copy()
    validation = calibrator.transform(np.array([0.0, 2.0, 5.0]))
    assert np.array_equal(calibrator.sorted_training_scores_, frozen_reference)
    assert np.allclose(validation, [0.0, 2.0 / 3.0, 1.0])
    assert np.all(np.diff(validation) >= 0.0)


def test_fixed_refit_artifact_round_trip_reproduces_raw_and_calibrated_scores(
    tmp_path: Path,
) -> None:
    architecture, _, result = _tiny_fixed_fit()
    sequences = _tiny_sequences()
    raw = reconstruction_errors(
        result.model, sequences, batch_size=3, device=torch.device("cpu")
    )
    metadata = {
        "split_manifest_id": "fd002-primary-v1",
        "preprocessing_decision_id": "fd002-preprocessing-selection-v1",
        "input_dim": 3,
        "seed": 43,
        "test_data_opened": False,
    }
    artifact = tmp_path / final_refit_artifact_name(43)
    save_lstm_artifact(result.model, architecture, raw, metadata, artifact)
    loaded, reference, loaded_metadata = load_lstm_artifact(
        artifact,
        expected_split_manifest_id="fd002-primary-v1",
        expected_preprocessing_decision_id="fd002-preprocessing-selection-v1",
    )
    reproduced = reconstruction_errors(
        loaded, sequences, batch_size=3, device=torch.device("cpu")
    )
    expected_calibrated = np.searchsorted(np.sort(raw), raw, side="right") / len(raw)
    reproduced_calibrated = np.searchsorted(
        reference, reproduced, side="right"
    ) / len(reference)
    assert np.allclose(raw, reproduced, rtol=1e-5, atol=1e-6)
    assert np.allclose(expected_calibrated, reproduced_calibrated, atol=1e-12)
    assert loaded_metadata == metadata


def test_final_refit_split_and_path_allow_list_rejects_test_inputs() -> None:
    assert validate_allowed_split_name("train") == "train"
    assert validate_allowed_split_name("validation") == "validation"
    assert (
        validate_allowed_input_path(
            "data/processed/sequences_v2/p1_k6/train.npy", "train"
        )
        == "data/processed/sequences_v2/p1_k6/train.npy"
    )
    for forbidden_split in (
        "test",
        "held_out_internal_test",
        "official_nasa_test",
    ):
        with pytest.raises(ValueError):
            validate_allowed_split_name(forbidden_split)
    with pytest.raises(ValueError, match="Prohibited"):
        validate_allowed_input_path(
            "data/processed/sequences_v2/p1_k6/internal_test.npy", "train"
        )
    with pytest.raises(ValueError, match="Prohibited"):
        validate_allowed_input_path("data/raw/test_FD002.txt", "validation")


def test_sequence_contract_requires_exact_shape_count_and_finite_values() -> None:
    valid = np.zeros((3, 30, 21), dtype=np.float32)
    assert (
        validate_sequence_collection(
            valid,
            expected_window_shape=(30, 21),
            expected_count=3,
            name="fixture",
        )
        is valid
    )
    with pytest.raises(ValueError, match="shape"):
        validate_sequence_collection(
            np.zeros((3, 21, 30)), expected_window_shape=(30, 21)
        )
    with pytest.raises(ValueError, match="exactly 4"):
        validate_sequence_collection(
            valid, expected_window_shape=(30, 21), expected_count=4
        )
    invalid = valid.copy()
    invalid[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        validate_sequence_collection(invalid, expected_window_shape=(30, 21))


def test_registered_protocol_and_completed_result_preserve_boundaries() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_final_refit_protocol(protocol)
    assert protocol["status"] == "registered_before_execution"
    assert protocol["outputs"]["result_config"] == (
        "configs/lstm/fd002-lstm-final-refit-results-v1.json"
    )
    result_path = REPO_ROOT / protocol["outputs"]["result_config"]
    assert result_path.is_file()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert isinstance(result, dict)
    assert result["status"] == "completed"
    assert result["study_id"] == "fd002-lstm-final-refit-v1"
    assert result["run_id"] == "fd002-lstm-final-refit-v1"
    assert result["protocol_path"] == (
        "configs/lstm/fd002-lstm-final-refit-protocol-v1.json"
    )
    protocol_hash = verify_registered_hash(PROTOCOL, result["protocol_sha256"])
    assert protocol_hash.match_form == "raw"
    assert result["completed_locked_refits"] == 3
    assert result["outputs"]["ledger_records_appended"] == 7
    assert result["threshold_selected"] is False
    assert result["test_data_opened"] is False
    assert result["result_classification"] == (
        "validation_proxy_diagnostic_not_test_performance"
    )
    assert isinstance(result["locked_epoch_count"], int)
    assert not isinstance(result["locked_epoch_count"], bool)
    assert result["locked_epoch_count"] > 0
    convergence_epochs = result["convergence_best_epochs"]
    assert set(convergence_epochs) == {"43", "44", "45"}
    assert all(
        isinstance(epoch, int) and not isinstance(epoch, bool) and epoch > 0
        for epoch in convergence_epochs.values()
    )
    assert protocol["epoch_lock"]["rule"] == (
        "median_of_three_convergence_best_epochs"
    )
    assert protocol["validation_diagnostics"]["ensemble"]["alignment_key"] == (
        "window_id"
    )


def test_final_refit_ledger_records_round_trip_as_seven_unique_rows(
    tmp_path: Path,
) -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    records = _ledger_records(
        protocol=protocol,
        protocol_path=tmp_path / "configs" / "final-refit.json",
        protocol_sha256="0" * 64,
        repo_root=tmp_path,
        execution_time="2026-08-25T00:00:00+00:00",
        convergence_rows=[
            {"seed": seed, "best_monitor_loss": 0.1}
            for seed in REGISTERED_SEEDS
        ],
        locked_rows=[
            {
                "seed": seed,
                "locked_epoch_count": 21,
                "selection_mean_pr_auc": 0.8,
            }
            for seed in REGISTERED_SEEDS
        ],
        ensemble_row={"selection_mean_pr_auc": 0.81},
        model_hashes={seed: "1" * 64 for seed in REGISTERED_SEEDS},
        report_hashes={
            "convergence_summary.csv": "2" * 64,
            "ranking_metrics.csv": "3" * 64,
            "ensemble_validation_scores.csv": "4" * 64,
        },
        final_model_dir=tmp_path / "models" / "final",
        final_report_dir=tmp_path / "reports" / "final",
        code_commit="5" * 40,
    )
    assert tuple(record["run_id"] for record in records) == (
        expected_final_refit_ledger_run_ids(protocol["study_id"])
    )
    ledger_path = tmp_path / "runs.jsonl"
    for record in records:
        append_run_record(ledger_path, record)
    assert load_run_ledger(ledger_path) == records


@pytest.mark.parametrize(
    ("module", "entry_name"),
    [
        ("scripts.run_lstm_final_refit", "turbofan-run-lstm-final-refit"),
        ("scripts.verify_lstm_final_refit", "turbofan-verify-lstm-final-refit"),
    ],
)
def test_final_refit_script_and_console_target_help_do_not_train(
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
