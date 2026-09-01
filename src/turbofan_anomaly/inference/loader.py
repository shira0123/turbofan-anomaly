"""Fail-closed loading of registered frozen FD002 inference artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from turbofan_anomaly.alerting.calibration import EmpiricalCDFCalibrator
from turbofan_anomaly.alerting.thresholds import FittedThresholds
from turbofan_anomaly.data.preprocessing import RegimeSensorPreprocessor, load_preprocessor
from turbofan_anomaly.evaluation.provenance import resolve_repo_path, sha256_file, verify_registered_hash
from turbofan_anomaly.models.classical import ClassicalAnomalyModel, load_baseline_artifact


PROTOCOL_PATH = "configs/inference/fd002-frozen-inference-protocol-v1.json"
PRIMARY_POLICY = "pca_reconstruction__per_mode__quantile_0.995__ewma_alpha_0.20__persistence_8"


class FrozenArtifactError(ValueError):
    """An artifact fails a pre-deserialization or post-load frozen contract."""


@dataclass(frozen=True)
class FrozenArtifacts:
    preprocessor: RegimeSensorPreprocessor
    pca_model: ClassicalAnomalyModel
    thresholds: FittedThresholds
    protocol: dict[str, Any]
    provenance: dict[str, str]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FrozenArtifactError(message)


class FrozenArtifactLoader:
    """Load only the single repository-registered inference protocol and paths."""

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = Path(repository_root).resolve()

    def _protocol_path(self) -> Path:
        return resolve_repo_path(PROTOCOL_PATH, self.repository_root)

    def load(self) -> FrozenArtifacts:
        protocol_path = self._protocol_path()
        _require(protocol_path.is_file(), "Registered inference protocol is missing")
        try:
            protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FrozenArtifactError("Registered inference protocol is unreadable") from error
        _require(protocol.get("protocol_id") == "fd002-frozen-inference-and-pca-attribution-v1", "Inference protocol identity mismatch")
        _require(protocol.get("frozen_primary_policy") == PRIMARY_POLICY, "Frozen primary policy mismatch")
        _require(protocol.get("windowing", {}).get("window_size") == 30, "Frozen window size mismatch")
        _require(protocol.get("windowing", {}).get("sensor_order") == [f"sensor_{index}" for index in range(1, 22)], "Frozen sensor order mismatch")
        _require(protocol.get("frozen_policy", {}).get("ewma_alpha") == 0.2, "Frozen EWMA mismatch")
        _require(protocol.get("frozen_policy", {}).get("persistence") == 8, "Frozen persistence mismatch")

        provenance = {"inference_protocol_sha256": sha256_file(protocol_path)}
        for name in ("phase5_results", "final_evaluation_protocol_v2", "confirmatory_results"):
            reference = protocol["registered_artifacts"][name]
            path = resolve_repo_path(reference["path"], self.repository_root)
            _require(path.is_file(), f"Registered authority is missing: {name}")
            try:
                verified = verify_registered_hash(path, reference["sha256"])
            except ValueError as error:
                raise FrozenArtifactError(f"Registered authority hash mismatch: {name}") from error
            provenance[f"{name}_sha256"] = verified.observed_raw_sha256

        preprocessor_reference = protocol["registered_artifacts"]["preprocessor"]
        preprocessor_path = resolve_repo_path(preprocessor_reference["path"], self.repository_root)
        _require(preprocessor_path.is_file(), "Registered P1/K=6 preprocessor is missing")
        _require(sha256_file(preprocessor_path) == preprocessor_reference["sha256"], "P1/K=6 preprocessor hash mismatch before deserialization")
        try:
            preprocessor, _ = load_preprocessor(preprocessor_path)
        except Exception as error:  # deserialize only after byte verification
            raise FrozenArtifactError("Registered P1/K=6 preprocessor cannot be loaded") from error
        _require(isinstance(preprocessor, RegimeSensorPreprocessor), "P1 artifact has an unexpected preprocessor type")
        _require(preprocessor.n_clusters == 6, "P1 artifact does not provide six modes")
        _require(set(preprocessor.canonical_mode_mapping_.values()) == set(range(6)), "P1 canonical mode mapping mismatch")
        provenance["preprocessor_sha256"] = preprocessor_reference["sha256"]

        pca_reference = protocol["registered_artifacts"]["pca_bundle"]
        pca_path = resolve_repo_path(pca_reference["path"], self.repository_root)
        _require(pca_path.is_file(), "Registered PCA bundle is missing")
        _require(sha256_file(pca_path) == pca_reference["sha256"], "PCA bundle hash mismatch before deserialization")
        try:
            pca_model, metadata = load_baseline_artifact(pca_path)
        except Exception as error:
            raise FrozenArtifactError("Registered PCA bundle cannot be loaded") from error
        _require(isinstance(pca_model, ClassicalAnomalyModel), "PCA artifact has an unexpected model type")
        _require(pca_model.detector_name == "pca" and pca_model.feature_count_ == 63, "PCA artifact model dimension mismatch")
        _require(isinstance(pca_model.score_calibrator_, EmpiricalCDFCalibrator), "PCA calibration state mismatch")
        _require(getattr(pca_model.score_calibrator_, "sorted_training_scores_", None) is not None, "PCA calibration reference is absent")
        _require(metadata.get("preprocessing_decision_id") == "fd002-preprocessing-selection-v1", "PCA preprocessing lineage mismatch")
        provenance["pca_bundle_sha256"] = pca_reference["sha256"]

        frozen = protocol["frozen_policy"]
        values = {int(mode): float(value) for mode, value in frozen["thresholds"].items()}
        _require(set(values) == set(range(6)), "Frozen threshold configuration lacks six modes")
        thresholds = FittedThresholds("per_mode", "quantile_0.995", values, {mode: 0 for mode in values})
        return FrozenArtifacts(preprocessor, pca_model, thresholds, protocol, provenance)
