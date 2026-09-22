#!/usr/bin/env python3
"""Generate manuscript V1 figures, diagrams, tables, captions, and provenance.

This script is deliberately limited to committed aggregate authorities and
registered implementation/configuration files. It never imports the project
package, opens datasets/model artifacts, or executes a scientific workflow.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
import hashlib
import html
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import sys
import textwrap
from typing import Any, Iterable


EVIDENCE_BASE_COMMIT = "4bcab1d13a1d44dccbedb0cecd7aa99ddea7ade1"
GENERATION_COMMAND = (
    "python scripts/manuscript/generate_manuscript_v1_assets.py --repo-root ."
)

ALLOWED_INPUTS = (
    "docs/manuscript/v1/EVIDENCE_MAP.md",
    "docs/manuscript/v1/FIGURE_TABLE_PLAN.md",
    "configs/splits/fd002-primary-v1.json",
    "configs/baselines/fd002-classical-baselines-v1.json",
    "configs/lstm/fd002-lstm-final-refit-results-v1.json",
    "configs/alerting/fd002-alert-policy-study-protocol-v2.json",
    "configs/alerting/fd002-alert-policy-study-results-v1.json",
    "configs/evaluation/fd002-confirmatory-execution-protocol-v1.json",
    "configs/evaluation/fd002-confirmatory-results-v1.json",
    "configs/inference/fd002-frozen-inference-protocol-v1.json",
    "reports/baselines_v2/selected_models.csv",
    "reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/detector_policy_metrics.csv",
    "reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/ranking_metrics.csv",
    "docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json",
    "docs/research/core_literature_comparability_v1.json",
    "docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib",
    "src/turbofan_anomaly/data/preprocessing.py",
    "src/turbofan_anomaly/data/metadata.py",
    "src/turbofan_anomaly/data/windows.py",
    "src/turbofan_anomaly/models/classical.py",
    "src/turbofan_anomaly/models/lstm_training.py",
    "src/turbofan_anomaly/alerting/calibration.py",
    "src/turbofan_anomaly/alerting/thresholds.py",
    "src/turbofan_anomaly/alerting/persistence.py",
    "src/turbofan_anomaly/evaluation/alerts.py",
    "src/turbofan_anomaly/evaluation/proxies.py",
    "src/turbofan_anomaly/evaluation/ranking.py",
    "src/turbofan_anomaly/explainability/pca_attribution.py",
    "src/turbofan_anomaly/inference/pipeline.py",
)

PROHIBITED_ROOT_PREFIXES = (
    "/data/raw/",
    "/data/processed/",
    "/data/splits/",
    "/models/",
)

PROHIBITED_PATH_PARTS = (
    "score_alert_trace",
    "validation_scores",
    "per_engine_metrics",
)

OUTPUT_ROOT = Path("docs/manuscript/v1")
FIGURES_DIR = OUTPUT_ROOT / "figures"
TABLES_DIR = OUTPUT_ROOT / "tables"
SOURCES_DIR = OUTPUT_ROOT / "figure_sources"
MANUSCRIPT_DOCUMENTS = (
    "docs/manuscript/v1/MANUSCRIPT_V1.md",
    "docs/manuscript/v1/manuscript_v1.tex",
    "docs/manuscript/v1/references_v1.bib",
    "docs/manuscript/v1/MANUSCRIPT_CLAIMS_AUDIT_V1.md",
    "docs/manuscript/v1/MANUSCRIPT_REVIEW_CHECKLIST_V1.md",
    "docs/manuscript/v1/PLAIN_LANGUAGE_SUMMARY.md",
)
REVIEW_DOCUMENTS = (
    "docs/manuscript/v1/INDEPENDENT_REVIEW_V1.md",
    "docs/manuscript/v1/REVISION_LOG_V1.md",
    "docs/manuscript/v1/README.md",
    "docs/manuscript/v1/HANDOFF.md",
    "docs/manuscript/v1/review_package/GUIDE_FEEDBACK.md",
    "docs/manuscript/v1/review_package/MANUSCRIPT_V1_GUIDE_REVIEW.pdf",
    "docs/manuscript/v1/review_package/MANUSCRIPT_V1_GUIDE_REVIEW.docx",
    "docs/manuscript/v1/review_package/manuscript_v1_latex_source.zip",
)

PALETTE = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "black": "#222222",
    "gray": "#6B7280",
    "light_gray": "#E5E7EB",
    "lighter_gray": "#F3F4F6",
    "white": "#FFFFFF",
}


@dataclass(frozen=True)
class Evidence:
    root: Path
    split: dict[str, Any]
    baseline: dict[str, Any]
    lstm: dict[str, Any]
    alert_protocol: dict[str, Any]
    alert_results: dict[str, Any]
    confirm_protocol: dict[str, Any]
    confirm_results: dict[str, Any]
    inference_protocol: dict[str, Any]
    detector_metrics: list[dict[str, str]]
    ranking_metrics: list[dict[str, str]]
    selected_models: list[dict[str, str]]
    core_evidence: dict[str, Any]
    comparability: dict[str, Any]
    bibtex: str
    source_hashes: dict[str, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--skip-png",
        action="store_true",
        help="Generate SVG/tables only and skip System.Drawing PNG previews",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_text(normalized, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def read_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def read_csv(root: Path, relative: str) -> list[dict[str, str]]:
    with (root / relative).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_allowlist(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in ALLOWED_INPUTS:
        normalized = "/" + relative.replace("\\", "/").lower()
        if normalized.startswith(PROHIBITED_ROOT_PREFIXES) or any(
            part in normalized for part in PROHIBITED_PATH_PARTS
        ):
            raise RuntimeError(f"Prohibited input in allowlist: {relative}")
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Required aggregate authority is missing: {relative}")
        hashes[relative] = sha256_file(path)
    return hashes


def load_evidence(root: Path) -> Evidence:
    root = root.resolve()
    source_hashes = validate_allowlist(root)
    return Evidence(
        root=root,
        split=read_json(root, "configs/splits/fd002-primary-v1.json"),
        baseline=read_json(root, "configs/baselines/fd002-classical-baselines-v1.json"),
        lstm=read_json(root, "configs/lstm/fd002-lstm-final-refit-results-v1.json"),
        alert_protocol=read_json(root, "configs/alerting/fd002-alert-policy-study-protocol-v2.json"),
        alert_results=read_json(root, "configs/alerting/fd002-alert-policy-study-results-v1.json"),
        confirm_protocol=read_json(root, "configs/evaluation/fd002-confirmatory-execution-protocol-v1.json"),
        confirm_results=read_json(root, "configs/evaluation/fd002-confirmatory-results-v1.json"),
        inference_protocol=read_json(root, "configs/inference/fd002-frozen-inference-protocol-v1.json"),
        detector_metrics=read_csv(root, "reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/detector_policy_metrics.csv"),
        ranking_metrics=read_csv(root, "reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/ranking_metrics.csv"),
        selected_models=read_csv(root, "reports/baselines_v2/selected_models.csv"),
        core_evidence=read_json(root, "docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json"),
        comparability=read_json(root, "docs/research/core_literature_comparability_v1.json"),
        bibtex=(root / "docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib").read_text(encoding="utf-8"),
        source_hashes=source_hashes,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def confirmatory_rows(evidence: Evidence) -> list[dict[str, Any]]:
    metric_by_policy = {
        row["policy_id"]: row
        for row in evidence.detector_metrics
        if row["detector_id"] == "pca_reconstruction"
        and row["policy_id"].endswith("_endpoint")
    }
    ranking_by_policy = {
        row["policy_id"]: row
        for row in evidence.ranking_metrics
        if row["detector_id"] == "pca_reconstruction"
        and row["policy_id"].endswith("_endpoint")
    }
    labels = {
        "normalized_life_last_10pct_endpoint": "Final 10%",
        "normalized_life_last_20pct_endpoint": "Final 20%",
        "normalized_life_last_30pct_endpoint": "Final 30%",
    }
    rows: list[dict[str, Any]] = []
    for registered in evidence.confirm_results["primary_endpoint_results"]:
        policy_id = registered["policy_id"]
        metric = metric_by_policy[policy_id]
        ranking = ranking_by_policy[policy_id]
        far_per_1000 = float(metric["false_positive_alerted_endpoints_per_1000_healthy_endpoints"])
        require(
            math.isclose(
                far_per_1000 / 10.0,
                float(registered["endpoint_false_alert_rate_percent"]),
                rel_tol=0.0,
                abs_tol=1e-12,
            ),
            f"FAR authority mismatch for {policy_id}",
        )
        require(
            math.isclose(
                float(metric["engine_detection_coverage"]),
                float(registered["engine_detection_coverage_percent"]),
                rel_tol=0.0,
                abs_tol=1e-12,
            ),
            f"Coverage authority mismatch for {policy_id}",
        )
        require(
            math.isclose(float(ranking["pr_auc"]), float(registered["pr_auc"]), abs_tol=1e-12)
            and math.isclose(float(ranking["roc_auc"]), float(registered["roc_auc"]), abs_tol=1e-12),
            f"Ranking authority mismatch for {policy_id}",
        )
        rows.append(
            {
                "policy_id": policy_id,
                "proxy": labels[policy_id],
                "false_positive_endpoints": int(metric["fp"]),
                "healthy_endpoints": int(metric["healthy_evaluated_endpoints"]),
                "far_per_1000": far_per_1000,
                "far_percent": float(registered["endpoint_false_alert_rate_percent"]),
                "detected_engines": int(metric["detected_engine_count"]),
                "engine_count": int(metric["validation_engine_count"]),
                "coverage_percent": float(registered["engine_detection_coverage_percent"]),
                "median_delay_cycles": float(registered["median_delay_cycles"]),
                "pr_auc": float(registered["pr_auc"]),
                "roc_auc": float(registered["roc_auc"]),
                "delay_population": "detected engines only; misses retained in coverage",
            }
        )
    delays = sorted(row["median_delay_cycles"] for row in rows)
    aggregate = float(evidence.confirm_results["target_attainment"]["aggregate_median_delay_cycles"])
    require(delays[1] == aggregate == 25.0, "Aggregate delay is not the median of proxy medians")
    return rows


def validation_model_rows(evidence: Evidence) -> list[dict[str, Any]]:
    label_map = {
        "lof": "LOF",
        "one_class_svm": "One-Class SVM",
        "lstm_calibrated_ensemble": "LSTM calibrated ensemble",
        "isolation_forest": "Isolation Forest",
        "pca_reconstruction": "PCA reconstruction",
    }
    rows = []
    for item in evidence.alert_results["score_reproduction"]:
        detector_id = item["detector_id"]
        rows.append(
            {
                "detector_id": detector_id,
                "label": label_map[detector_id],
                "mean_pr_auc": float(item["registered_selection_mean_pr_auc"]),
                "mean_roc_auc": float(item["registered_selection_mean_roc_auc"]),
            }
        )
    order = {name: index for index, name in enumerate(label_map)}
    rows.sort(key=lambda row: order[row["detector_id"]])
    require(len(rows) == 5, "Expected five comparable validation score sources")
    require(evidence.alert_results["fusion_evaluated"] is False, "Fusion boundary changed")
    return rows


def bibtex_keys(text: str) -> set[str]:
    return set(re.findall(r"@[A-Za-z]+\{([^,]+),", text))


def literature_rows(evidence: Evidence) -> list[dict[str, Any]]:
    selected_ids = (
        "LIT-010",
        "LIT-013",
        "LIT-007",
        "LIT-008",
        "LIT-009",
        "LIT-012",
        "LIT-018",
        "LIT-006",
    )
    comp_by_id = {row["paper_id"]: row for row in evidence.comparability["rows"]}
    paper_ids = {row["core_paper_id"] for row in evidence.core_evidence["papers"]}
    keys = bibtex_keys(evidence.bibtex)
    rows: list[dict[str, Any]] = []
    native_result_override = {
        "LIT-013": "FD002: precision 0.374; recall 0.799; specificity 0.982; F1 0.510; anomaly fraction 0.013",
        "LIT-007": "FD004: F1 0.892; precision 0.896; recall 0.724",
        "LIT-012": "FD001/FD003: accuracy, precision, recall, F1, and correct-detection rate; values at LIT-012-V01–V10",
        "LIT-006": "FD001-equivalent: timeliness 256; accuracy 0.67; MAE 10 cycles; MSE 164 cycles²; MAPE1 0.18; MAPE2 0.05; FPR 0.13; FNR 0.20",
    }
    for paper_id in selected_ids:
        require(paper_id in paper_ids, f"Core evidence is missing {paper_id}")
        item = comp_by_id[paper_id]
        key = f"core{paper_id[-3:]}"
        require(key in keys, f"BibTeX key {key} is missing")
        rows.append(
            {
                "panel": "literature",
                "study": paper_id,
                "citation_key": key,
                "category": item["comparison_category"],
                "dataset_task": f"{item['dataset_subset']}; {item['task']}",
                "split_and_labels": f"{item['split']}; labels/onset: {item['label_definition']}",
                "learning_and_model": f"{item['learning_status']}; {item['model']}",
                "reported_native_metrics": native_result_override.get(
                    paper_id, item["published_value"]
                ),
                "project_compatible_far": "NR—not comparable",
                "project_compatible_other_metrics": "NR—not comparable",
                "evidence_location": item["evidence_location"],
                "comparability_caveat": item["caveat"],
            }
        )
    require(
        {row["category"] for row in rows if row["study"] in {"LIT-010", "LIT-013"}} == {"B"},
        "Category B selection changed",
    )
    require(
        all(row["category"] == "C" for row in rows if row["study"] not in {"LIT-010", "LIT-013"}),
        "Context rows must remain Category C",
    )
    return rows


def dataset_rows(evidence: Evidence) -> list[dict[str, Any]]:
    cycle_counts = {"train": 0, "validation": 0, "test": 0}
    for engine in evidence.split["engines"]:
        cycle_counts[engine["split"]] += int(engine["cycle_count"])
    counts = evidence.split["split"]["counts"]
    sequence_shapes = evidence.baseline["sequence_shapes"]["p1_k6"]
    held_out = evidence.confirm_results["population"]
    require(cycle_counts == {"train": 32107, "validation": 10873, "test": 10779}, "Cycle counts changed")
    return [
        {
            "partition": "Training",
            "manifest_name": "train",
            "engines": int(counts["train"]),
            "cycle_rows": cycle_counts["train"],
            "length_30_windows": int(sequence_shapes["train"][0]),
            "role": "Fit preprocessing, detectors, calibrators, and training-reference thresholds",
            "fitting_allowed": "Yes—only registered training populations",
            "evidence_status": "Development/fitting",
        },
        {
            "partition": "Validation",
            "manifest_name": "validation",
            "engines": int(counts["validation"]),
            "cycle_rows": cycle_counts["validation"],
            "length_30_windows": int(sequence_shapes["validation"][0]),
            "role": "Select K, models, and alert policy under registered proxies",
            "fitting_allowed": "No learned-state fitting",
            "evidence_status": "Validation/model selection",
        },
        {
            "partition": "Internal held-out",
            "manifest_name": "test",
            "engines": int(held_out["engines"]),
            "cycle_rows": int(held_out["cycle_rows"]),
            "length_30_windows": int(held_out["windows"]),
            "role": "First valid frozen confirmatory evaluation",
            "fitting_allowed": "No refit, recalibration, reselection, or fusion",
            "evidence_status": "Completed internal held-out",
        },
        {
            "partition": "Official NASA test",
            "manifest_name": "external/deferred",
            "engines": "NR",
            "cycle_rows": "NR",
            "length_30_windows": "NR",
            "role": "Separately preregistered future external evaluation",
            "fitting_allowed": "Outside completed study",
            "evidence_status": "Not accessed; deferred",
        },
    ]


def policy_rows(evidence: Evidence) -> list[dict[str, Any]]:
    primary = evidence.confirm_protocol["primary"]
    thresholds = primary["thresholds"]
    threshold_text = "; ".join(
        f"mode {mode}: {float(value):.16g}" for mode, value in sorted(thresholds.items(), key=lambda item: int(item[0]))
    )
    return [
        {
            "component": "Engine split",
            "verified_setting": "156 train / 52 validation / 52 internal held-out; whole-engine separation; seed 42",
            "fit_or_derivation_boundary": "Split manifest only",
            "source_selector": "configs/splits/fd002-primary-v1.json: split",
        },
        {
            "component": "Healthy-training eligibility",
            "verified_setting": "Window end cycle ≤ floor(0.30 × engine maximum cycle); 5,037 eligible windows",
            "fit_or_derivation_boundary": "Training engines only; ineligible windows remain unlabeled",
            "source_selector": "baseline config: training_policy",
        },
        {
            "component": "P1/K=6 preprocessing",
            "verified_setting": "Scaled 3-setting K-Means (K=6); per-mode sensor scaling with global healthy fallback",
            "fit_or_derivation_boundary": "Operating scaler/K-Means: all training rows; sensor scalers: early-life training rows",
            "source_selector": "preprocessing.RegimeSensorPreprocessor.fit",
        },
        {
            "component": "Window and endpoint mode",
            "verified_setting": "30 cycles × 21 sensors, stride 1; mode from exact (engine, end_cycle) join",
            "fit_or_derivation_boundary": "Transform/derivation only",
            "source_selector": "confirmatory protocol: preprocessing; metadata.assign_endpoint_operating_modes",
        },
        {
            "component": "PCA representation",
            "verified_setting": "63 ordered features: 21 means, 21 population SDs (ddof=0), 21 endpoint-minus-start differences",
            "fit_or_derivation_boundary": "Summary reduction fits no state",
            "source_selector": "windows.summary_features; inference protocol: pca_score_and_attribution",
        },
        {
            "component": "PCA model and raw score",
            "verified_setting": "n_components=0.90; mean squared reconstruction residual across standardized 63-feature space",
            "fit_or_derivation_boundary": "Feature scaler and PCA fitted on eligible training features",
            "source_selector": "selected_models.csv p1_k6/pca; classical._raw_scores_scaled",
        },
        {
            "component": "Calibration",
            "verified_setting": "Right-sided empirical CDF: count(training score ≤ score) / n",
            "fit_or_derivation_boundary": "Eligible training scores only; frozen transform on validation/held-out",
            "source_selector": "calibration.EmpiricalCDFCalibrator",
        },
        {
            "component": "Per-mode threshold",
            "verified_setting": "q=0.995, NumPy method='higher'; " + threshold_text,
            "fit_or_derivation_boundary": "Six training-reference thresholds, frozen before held-out access",
            "source_selector": "confirmatory protocol: primary.thresholds",
        },
        {
            "component": "Runtime state",
            "verified_setting": "Calibrated score → EWMA α=0.20 → strict current-mode threshold comparison → persistence 8",
            "fit_or_derivation_boundary": "No online recalibration; alert begins on eighth consecutive violation without backdating",
            "source_selector": "persistence.apply_alert_policy; confirmatory protocol: primary",
        },
        {
            "component": "State reset and events",
            "verified_setting": "Reset at engine boundary or endpoint gap, not mode change; contiguous active endpoints form events",
            "fit_or_derivation_boundary": "Deterministic state machine",
            "source_selector": "alert protocol: state_contract; alerts.extract_alert_events",
        },
        {
            "component": "PCA sensor contribution",
            "verified_setting": "Per sensor: mean/std/slope squared residuals summed and divided by 63; contributions sum to raw PCA MSE",
            "fit_or_derivation_boundary": "Local normalized-feature-space model fidelity only",
            "source_selector": "pca_attribution.attribute_pca_reconstruction",
        },
        {
            "component": "Comparator and fusion boundary",
            "verified_setting": "Three-seed calibrated LSTM score mean is an unfused comparator; PCA–LSTM fusion not evaluated",
            "fit_or_derivation_boundary": "Comparator policy frozen separately; primary remains PCA",
            "source_selector": "confirmatory protocol: comparator; alert result: fusion_evaluated=false",
        },
    ]


def canonical_digest(rows: list[dict[str, Any]], fieldnames: list[str]) -> str:
    payload = [[row.get(field, "") for field in fieldnames] for row in rows]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_csv_table(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "≤": r"$\leq$",
        "×": r"$\times$",
        "→": r"$\rightarrow$",
        "α": r"$\alpha$",
        "²": r"$^2$",
        "–": "--",
        "—": "---",
    }
    return "".join(replacements.get(char, char) for char in text)


def write_markdown_table(
    path: Path,
    title: str,
    note: str,
    rows: list[dict[str, Any]],
    fields: list[str],
    headers: list[str],
    display: callable | None = None,
) -> None:
    digest = canonical_digest(rows, fields)
    lines = [f"# {title}", "", note, "", f"<!-- canonical-sha256: {digest} -->", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        values = [display(field, row.get(field, ""), row) if display else row.get(field, "") for field in fields]
        lines.append("| " + " | ".join(md_escape(value) for value in values) + " |")
    lines.append("")
    write_text(path, "\n".join(lines))


def write_latex_table(
    path: Path,
    caption: str,
    label: str,
    note: str,
    rows: list[dict[str, Any]],
    fields: list[str],
    headers: list[str],
    column_spec: str,
    display: callable | None = None,
) -> None:
    digest = canonical_digest(rows, fields)
    lines = [
        f"% canonical-sha256: {digest}",
        "% Generated by scripts/manuscript/generate_manuscript_v1_assets.py",
        r"\begin{table*}[t]",
        r"\centering",
        r"\small",
        f"\\caption{{{latex_escape(caption)}}}",
        f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{{column_spec}}}",
        r"\hline",
        " & ".join(latex_escape(header) for header in headers) + r" \\",
        r"\hline",
    ]
    for row in rows:
        values = [display(field, row.get(field, ""), row) if display else row.get(field, "") for field in fields]
        lines.append(" & ".join(latex_escape(value) for value in values) + r" \\")
    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\vspace{0.5ex}",
            f"\\parbox{{0.98\\textwidth}}{{\\footnotesize {latex_escape(note)}}}",
            r"\end{table*}",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def format_delay(value: float) -> str:
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}"


def result_display(field: str, value: Any, row: dict[str, Any]) -> Any:
    if field == "far_per_1000":
        return f"{float(value):.3f}"
    if field == "far_percent":
        return f"{float(value):.4f}"
    if field == "coverage_percent":
        return f"{float(value):.2f}"
    if field == "median_delay_cycles":
        return format_delay(float(value))
    if field in {"pr_auc", "roc_auc"}:
        return f"{float(value):.5f}"
    if field == "fp_over_healthy":
        return f"{row['false_positive_endpoints']}/{row['healthy_endpoints']}"
    if field == "detected_over_engines":
        return f"{row['detected_engines']}/{row['engine_count']}"
    return value


def generate_tables(evidence: Evidence, rows: list[dict[str, Any]], lit_rows: list[dict[str, Any]]) -> list[Path]:
    root = evidence.root
    outputs: list[Path] = []

    data_rows = dataset_rows(evidence)
    data_fields = [
        "partition",
        "manifest_name",
        "engines",
        "cycle_rows",
        "length_30_windows",
        "role",
        "fitting_allowed",
        "evidence_status",
    ]
    data_headers = [
        "Partition",
        "Manifest name",
        "Engines",
        "Cycle rows",
        "Length-30 windows",
        "Role",
        "Fitting allowed",
        "Evidence status",
    ]
    base = root / TABLES_DIR / "table_01_dataset_protocol_summary"
    write_csv_table(base.with_suffix(".csv"), data_rows, data_fields)
    write_markdown_table(
        base.with_suffix(".md"),
        "Table 1. Dataset and experimental-protocol summary",
        "Counts are committed split/protocol facts. The manifest name `test` is reported in the manuscript as internal held-out; the separate official NASA test was not accessed.",
        data_rows,
        data_fields,
        data_headers,
    )
    write_latex_table(
        base.with_suffix(".tex"),
        "Dataset and experimental-protocol summary.",
        "tab:dataset-protocol",
        "The manifest label test denotes the internal held-out partition. Official NASA-test evaluation is outside the completed study.",
        data_rows,
        data_fields,
        data_headers,
        "p{0.11\\textwidth}p{0.08\\textwidth}r r r p{0.20\\textwidth}p{0.18\\textwidth}p{0.13\\textwidth}",
    )
    outputs.extend([base.with_suffix(ext) for ext in (".csv", ".md", ".tex")])

    frozen_rows = policy_rows(evidence)
    frozen_fields = ["component", "verified_setting", "fit_or_derivation_boundary", "source_selector"]
    frozen_headers = ["Component", "Frozen setting", "Fit/derivation boundary", "Authority"]
    base = root / TABLES_DIR / "table_02_frozen_primary_policy"
    write_csv_table(base.with_suffix(".csv"), frozen_rows, frozen_fields)
    policy_note = (
        "Machine-readable CSV retains exact registered threshold precision. The manuscript displays component settings without upgrading operating modes to physical regimes or attribution to physical localization."
    )
    write_markdown_table(
        base.with_suffix(".md"),
        "Table 2. Frozen primary policy and verified settings",
        policy_note,
        frozen_rows,
        frozen_fields,
        frozen_headers,
    )
    write_latex_table(
        base.with_suffix(".tex"),
        "Frozen primary policy and verified settings.",
        "tab:frozen-policy",
        policy_note,
        frozen_rows,
        frozen_fields,
        frozen_headers,
        "p{0.13\\textwidth}p{0.34\\textwidth}p{0.27\\textwidth}p{0.20\\textwidth}",
    )
    outputs.extend([base.with_suffix(ext) for ext in (".csv", ".md", ".tex")])

    result_rows = []
    for row in rows:
        result_rows.append(
            {
                **row,
                "fp_over_healthy": f"{row['false_positive_endpoints']}/{row['healthy_endpoints']}",
                "detected_over_engines": f"{row['detected_engines']}/{row['engine_count']}",
            }
        )
    result_fields = [
        "policy_id",
        "proxy",
        "false_positive_endpoints",
        "healthy_endpoints",
        "fp_over_healthy",
        "far_per_1000",
        "far_percent",
        "detected_engines",
        "engine_count",
        "detected_over_engines",
        "coverage_percent",
        "median_delay_cycles",
        "pr_auc",
        "roc_auc",
        "delay_population",
    ]
    display_fields = [
        "proxy",
        "fp_over_healthy",
        "far_per_1000",
        "far_percent",
        "detected_over_engines",
        "coverage_percent",
        "median_delay_cycles",
        "pr_auc",
        "roc_auc",
    ]
    display_headers = [
        "Endpoint proxy",
        "FP/healthy endpoints",
        "FAR/1,000",
        "FAR (%)",
        "Detected/engines",
        "Coverage (%)",
        "Median delay (cycles)",
        "PR-AUC",
        "ROC-AUC",
    ]
    base = root / TABLES_DIR / "table_03_confirmatory_results"
    write_csv_table(base.with_suffix(".csv"), result_rows, result_fields)
    result_note = (
        "Display rounding: FAR/1,000 to 3 decimals, FAR percentage to 4 decimals, coverage to 2 decimals, delay to 0–1 decimals, and AUCs to 5 decimals; CSV retains source precision. Delay medians include detected engines only; missed engines remain in coverage. Aggregate delay is the median of the three proxy-specific medians (25 cycles), not a pooled engine-delay median."
    )
    write_markdown_table(
        base.with_suffix(".md"),
        "Table 3. Frozen internal held-out primary result",
        result_note,
        result_rows,
        display_fields,
        display_headers,
        result_display,
    )
    write_latex_table(
        base.with_suffix(".tex"),
        "Frozen PCA internal held-out results under three normalized-life endpoint proxies.",
        "tab:confirmatory-results",
        result_note + " These are proxy-labelled internal held-out results, not official NASA-test or physical fault-onset performance.",
        result_rows,
        display_fields,
        display_headers,
        "l r r r r r r r r",
        result_display,
    )
    outputs.extend([base.with_suffix(ext) for ext in (".csv", ".md", ".tex")])

    project_rows = []
    for row in rows:
        project_rows.append(
            {
                "panel": "this_study",
                "study": f"This study—{row['proxy']}",
                "citation_key": "project authority",
                "category": "Internal held-out; no Category A literature comparator",
                "dataset_task": "NASA C-MAPSS FD002; anomaly-alert evaluation",
                "split_and_labels": f"52 engine-disjoint internal held-out engines; {row['proxy']} endpoint proxy",
                "learning_and_model": "Healthy-only P1/K=6 PCA; frozen per-mode q=0.995/EWMA 0.20/persistence 8",
                "reported_native_metrics": (
                    f"FAR {row['far_per_1000']:.15g}/1,000 ({row['far_percent']:.15g}%); "
                    f"coverage {row['coverage_percent']:.15g}%; delay {row['median_delay_cycles']:.15g} cycles; "
                    f"PR-AUC {row['pr_auc']:.17g}; ROC-AUC {row['roc_auc']:.17g}"
                ),
                "project_compatible_far": f"{row['far_per_1000']:.15g}/1,000; {row['far_percent']:.15g}%",
                "project_compatible_other_metrics": (
                    f"coverage {row['coverage_percent']:.15g}%; delay {row['median_delay_cycles']:.15g} cycles; "
                    f"PR-AUC {row['pr_auc']:.17g}; ROC-AUC {row['roc_auc']:.17g}"
                ),
                "evidence_location": f"configs/evaluation/fd002-confirmatory-results-v1.json: primary_endpoint_results[{row['policy_id']}]",
                "comparability_caveat": "Proxy-labelled internal held-out result; not official NASA-test or observed physical onset.",
            }
        )
    comparison_rows = lit_rows + project_rows
    comparison_fields = [
        "panel",
        "study",
        "citation_key",
        "category",
        "dataset_task",
        "split_and_labels",
        "learning_and_model",
        "reported_native_metrics",
        "project_compatible_far",
        "project_compatible_other_metrics",
        "evidence_location",
        "comparability_caveat",
    ]
    base = root / TABLES_DIR / "table_04_literature_comparison"
    write_csv_table(base.with_suffix(".csv"), comparison_rows, comparison_fields)
    lit_note = (
        "Selection rule: include both Category B partial comparators and Category C studies that cover engine-disjoint anomaly detection, change points, FD002/official-test RUL context, or reconstruction precedent. Selection is relevance-based, not result-favoring. NR means not reported. ‘Not comparable’ means dataset/task, split, onset labels, metric denominator, or alert semantics differ. Specificity is not converted to FAR. No Category A comparator was identified."
    )
    lit_md_fields = [
        "study",
        "citation_key",
        "category",
        "dataset_task",
        "split_and_labels",
        "reported_native_metrics",
        "project_compatible_far",
        "evidence_location",
        "comparability_caveat",
    ]
    lit_md_headers = [
        "Study",
        "Citation",
        "Category",
        "Dataset/task",
        "Split and labels",
        "Reported native metrics",
        "Project-compatible FAR",
        "Exact evidence",
        "Decisive caveat",
    ]
    write_markdown_table(
        base.with_suffix(".md"),
        "Table 4. Focused literature comparison",
        lit_note,
        comparison_rows,
        lit_md_fields,
        lit_md_headers,
    )
    write_latex_table(
        base.with_suffix(".tex"),
        "Focused literature comparison and this study's frozen internal held-out results.",
        "tab:literature-comparison",
        lit_note,
        comparison_rows,
        lit_md_fields,
        lit_md_headers,
        "p{0.08\\textwidth}p{0.06\\textwidth}p{0.07\\textwidth}p{0.15\\textwidth}p{0.16\\textwidth}p{0.16\\textwidth}p{0.10\\textwidth}p{0.12\\textwidth}p{0.14\\textwidth}",
    )
    outputs.extend([base.with_suffix(ext) for ext in (".csv", ".md", ".tex")])
    return outputs


def primitive(kind: str, **kwargs: Any) -> dict[str, Any]:
    return {"type": kind, **kwargs}


def add_text(
    items: list[dict[str, Any]],
    x: float,
    y: float,
    text: str,
    *,
    size: int = 28,
    weight: int = 400,
    anchor: str = "start",
    color: str = "black",
) -> None:
    items.append(primitive("text", x=x, y=y, text=text, size=size, weight=weight, anchor=anchor, color=PALETTE[color]))


def add_wrapped_text(
    items: list[dict[str, Any]],
    x: float,
    y: float,
    text: str,
    *,
    chars: int,
    size: int = 26,
    weight: int = 400,
    anchor: str = "middle",
    color: str = "black",
    line_height: int | None = None,
) -> None:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=chars, break_long_words=False) or [""])
    step = line_height or int(size * 1.25)
    for index, line in enumerate(lines):
        add_text(items, x, y + index * step, line, size=size, weight=weight, anchor=anchor, color=color)


def add_box(
    items: list[dict[str, Any]],
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    *,
    fill: str = "white",
    stroke: str = "gray",
    title_color: str = "black",
    body_color: str = "black",
    title_size: int = 28,
    body_size: int = 23,
    chars: int = 30,
    dashed: bool = False,
) -> None:
    items.append(
        primitive(
            "rect",
            x=x,
            y=y,
            width=w,
            height=h,
            fill=PALETTE[fill],
            stroke=PALETTE[stroke],
            stroke_width=3,
            radius=12,
            dash=dashed,
        )
    )
    add_text(items, x + w / 2, y + 38, title, size=title_size, weight=600, anchor="middle", color=title_color)
    if body:
        add_wrapped_text(
            items,
            x + w / 2,
            y + 75,
            body,
            chars=chars,
            size=body_size,
            anchor="middle",
            color=body_color,
        )


def add_arrow(
    items: list[dict[str, Any]],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: str = "gray",
    width: int = 4,
    dashed: bool = False,
) -> None:
    items.append(
        primitive(
            "arrow",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            stroke=PALETTE[color],
            stroke_width=width,
            dash=dashed,
        )
    )


def add_line(
    items: list[dict[str, Any]],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: str = "light_gray",
    width: int = 2,
    dashed: bool = False,
) -> None:
    items.append(
        primitive(
            "line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            stroke=PALETTE[color],
            stroke_width=width,
            dash=dashed,
        )
    )


def build_operational_figure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    width, height = 2400, 980
    items: list[dict[str, Any]] = [primitive("rect", x=0, y=0, width=width, height=height, fill=PALETTE["white"], stroke=PALETTE["white"], stroke_width=0)]
    add_text(items, width / 2, 55, "Frozen PCA internal held-out operational results", size=38, weight=600, anchor="middle")
    add_text(items, width / 2, 95, "Normalized-life endpoint proxies; 52 engines", size=25, anchor="middle", color="gray")
    panels = [
        ("Endpoint FAR (%)", "far_percent", 0.0, 6.5, "blue", 6.0, "FAR objective: 6%", lambda value: f"{value:.4f}%"),
        ("Engine coverage (%)", "coverage_percent", 0.0, 100.0, "green", None, "", lambda value: f"{value:.2f}%"),
        ("Median detection delay (cycles)", "median_delay_cycles", 0.0, 50.0, "orange", 12.0, "Aggregate aspiration: ≤12 cycles\n(not proxy-wise pass/fail)", format_delay),
    ]
    panel_w, gap = 690, 80
    start_x, top, plot_h = 100, 220, 530
    for panel_index, (title, key, ymin, ymax, color, reference, reference_label, formatter) in enumerate(panels):
        px = start_x + panel_index * (panel_w + gap)
        add_text(items, px + panel_w / 2, 150, title, size=29, weight=600, anchor="middle")
        left, right, bottom = px + 100, px + panel_w - 35, top + plot_h
        add_line(items, left, top, left, bottom, color="black", width=3)
        add_line(items, left, bottom, right, bottom, color="black", width=3)
        ticks = 4 if ymax <= 10 else 5
        for tick in range(ticks + 1):
            value = ymin + (ymax - ymin) * tick / ticks
            y = bottom - plot_h * (value - ymin) / (ymax - ymin)
            add_line(items, left, y, right, y, color="light_gray", width=2)
            label = f"{value:.1f}" if ymax <= 10 else f"{value:.0f}"
            add_text(items, left - 15, y + 8, label, size=21, anchor="end", color="gray")
        if reference is not None:
            ry = bottom - plot_h * (reference - ymin) / (ymax - ymin)
            add_line(items, left, ry, right, ry, color="vermillion", width=3, dashed=True)
            if key == "median_delay_cycles":
                for line_index, line in enumerate(reference_label.split("\n")):
                    add_text(items, px + panel_w / 2, 180 + 23 * line_index, line, size=18, weight=600, anchor="middle", color="vermillion")
            else:
                for line_index, line in enumerate(reference_label.split("\n")):
                    add_text(items, right - 5, ry - 12 - 26 * (len(reference_label.split("\n")) - line_index - 1), line, size=19, weight=600, anchor="end", color="vermillion")
        bar_w = 110
        spacing = (right - left) / len(rows)
        for index, row in enumerate(rows):
            value = float(row[key])
            center = left + spacing * (index + 0.5)
            y = bottom - plot_h * (value - ymin) / (ymax - ymin)
            items.append(primitive("rect", x=center - bar_w / 2, y=y, width=bar_w, height=bottom - y, fill=PALETTE[color], stroke=PALETTE[color], stroke_width=0, radius=0, dash=False))
            add_text(items, center, y - 14, formatter(value), size=23, weight=600, anchor="middle")
            add_text(items, center, bottom + 38, row["proxy"].replace(" ", "\n"), size=21, anchor="middle")
        add_text(items, px + panel_w / 2, bottom + 90, "Onset proxy", size=23, weight=600, anchor="middle")
    add_text(items, width / 2, 900, "Delay medians condition on detected engines; missed engines remain in coverage.", size=24, anchor="middle", color="gray")
    add_text(items, width / 2, 938, "Registered aggregate delay = median of proxy medians (12, 25, 42.5) = 25 cycles.", size=24, weight=600, anchor="middle")
    return {
        "filename": "figure_03_operational_results",
        "title": "Frozen PCA internal held-out operational results",
        "description": "Three panels show endpoint FAR percentage, engine coverage percentage, and median delay cycles for final-10%, final-20%, and final-30% endpoint proxies.",
        "width": width,
        "height": height,
        "width_mm": 190,
        "height_mm": 78,
        "data": rows,
        "primitives": items,
    }


def build_ranking_figure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    width, height = 1800, 920
    items: list[dict[str, Any]] = [primitive("rect", x=0, y=0, width=width, height=height, fill=PALETTE["white"], stroke=PALETTE["white"], stroke_width=0)]
    add_text(items, width / 2, 55, "Frozen PCA threshold-free ranking by onset proxy", size=38, weight=600, anchor="middle")
    add_text(items, width / 2, 95, "Internal held-out window endpoints; metrics are not accuracy", size=25, anchor="middle", color="gray")
    panels = [("PR-AUC", "pr_auc", "blue"), ("ROC-AUC", "roc_auc", "purple")]
    panel_w, gap = 720, 120
    start_x, top, plot_h = 110, 180, 560
    for panel_index, (title, key, color) in enumerate(panels):
        px = start_x + panel_index * (panel_w + gap)
        add_text(items, px + panel_w / 2, 145, title, size=31, weight=600, anchor="middle")
        left, right, bottom = px + 100, px + panel_w - 35, top + plot_h
        add_line(items, left, top, left, bottom, color="black", width=3)
        add_line(items, left, bottom, right, bottom, color="black", width=3)
        for tick in range(6):
            value = tick / 5
            y = bottom - plot_h * value
            add_line(items, left, y, right, y, color="light_gray", width=2)
            add_text(items, left - 15, y + 8, f"{value:.1f}", size=21, anchor="end", color="gray")
        spacing = (right - left) / len(rows)
        for index, row in enumerate(rows):
            value = float(row[key])
            center = left + spacing * (index + 0.5)
            y = bottom - plot_h * value
            items.append(primitive("circle", cx=center, cy=y, radius=16, fill=PALETTE[color], stroke=PALETTE["black"], stroke_width=2))
            add_text(items, center, y - 24, f"{value:.5f}", size=22, weight=600, anchor="middle")
            add_text(items, center, bottom + 40, row["proxy"].replace(" ", "\n"), size=21, anchor="middle")
        add_text(items, px + panel_w / 2, bottom + 92, "Onset proxy", size=23, weight=600, anchor="middle")
    add_text(items, width / 2, 860, "PR-AUC and ROC-AUC are pooled-window ranking metrics under explicit proxy labels; no curves or uncertainty intervals are inferred.", size=22, anchor="middle", color="gray")
    return {
        "filename": "figure_04_ranking_results",
        "title": "Frozen PCA ranking results",
        "description": "Two panels show PR-AUC and ROC-AUC for the same three normalized-life endpoint proxies.",
        "width": width,
        "height": height,
        "width_mm": 180,
        "height_mm": 92,
        "data": rows,
        "primitives": items,
    }


def build_validation_figure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    width, height = 1900, 1080
    items: list[dict[str, Any]] = [primitive("rect", x=0, y=0, width=width, height=height, fill=PALETTE["white"], stroke=PALETTE["white"], stroke_width=0)]
    add_text(items, width / 2, 55, "Validation/model-selection ranking evidence", size=38, weight=600, anchor="middle")
    add_text(items, width / 2, 95, "Same 52-engine validation split; mean over final-10/20/30% endpoint proxies", size=25, anchor="middle", color="gray")
    panels = [("Mean validation PR-AUC", "mean_pr_auc", "blue"), ("Mean validation ROC-AUC", "mean_roc_auc", "purple")]
    panel_w, gap = 780, 100
    start_x, top, plot_h = 100, 180, 690
    min_value, max_value = 0.70, 1.00
    for panel_index, (title, key, color) in enumerate(panels):
        px = start_x + panel_index * (panel_w + gap)
        add_text(items, px + panel_w / 2, 145, title, size=30, weight=600, anchor="middle")
        left, right = px + 250, px + panel_w - 50
        for tick in range(4):
            value = min_value + tick * 0.10
            x = left + (right - left) * (value - min_value) / (max_value - min_value)
            add_line(items, x, top, x, top + plot_h, color="light_gray", width=2)
            add_text(items, x, top + plot_h + 35, f"{value:.2f}", size=21, anchor="middle", color="gray")
        add_line(items, left, top + plot_h, right, top + plot_h, color="black", width=3)
        row_step = plot_h / len(rows)
        for index, row in enumerate(rows):
            y = top + row_step * (index + 0.5)
            value = float(row[key])
            x = left + (right - left) * (value - min_value) / (max_value - min_value)
            add_text(items, left - 18, y + 8, row["label"], size=23, anchor="end")
            add_line(items, left, y, x, y, color=color, width=6)
            items.append(primitive("circle", cx=x, cy=y, radius=15, fill=PALETTE[color], stroke=PALETTE["black"], stroke_width=2))
            add_text(items, min(x + 18, right - 5), y - 18, f"{value:.5f}", size=21, weight=600, anchor="start")
        add_text(items, (left + right) / 2, top + plot_h + 78, "Mean AUC across three endpoint proxies", size=23, weight=600, anchor="middle")
    add_text(items, width / 2, 1000, "Validation-only selection evidence—not internal held-out performance. PCA was frozen later under the registered operational alert objective.", size=23, anchor="middle", color="gray")
    return {
        "filename": "figure_05_validation_model_comparison",
        "title": "Validation model comparison",
        "description": "Two horizontal dot plots compare mean validation PR-AUC and ROC-AUC for five registered P1/K=6 score sources.",
        "width": width,
        "height": height,
        "width_mm": 190,
        "height_mm": 108,
        "data": rows,
        "primitives": items,
    }


def build_architecture_figure() -> dict[str, Any]:
    width, height = 2400, 1580
    items: list[dict[str, Any]] = [primitive("rect", x=0, y=0, width=width, height=height, fill=PALETTE["white"], stroke=PALETTE["white"], stroke_width=0)]
    add_text(items, width / 2, 52, "Implemented FD002 condition-aware anomaly-alert architecture", size=38, weight=600, anchor="middle")
    add_text(items, 55, 112, "A. Training-only fitting and validation selection (completed before held-out access)", size=28, weight=600, anchor="start", color="blue")
    add_box(items, 55, 145, 300, 145, "Training engines", "156 engines\nregistered split", fill="lighter_gray", stroke="blue", chars=22)
    add_box(items, 415, 130, 420, 175, "Fit P1/K=6", "Operating scaler + K-Means: all training rows\nPer-mode sensor scalers: early-life rows", fill="white", stroke="blue", chars=34)
    add_box(items, 900, 130, 330, 175, "Training windows", "30 cycles × 21 sensors\nstride 1", fill="white", stroke="blue", chars=25)
    add_box(items, 1290, 85, 360, 145, "PCA branch", "63 summaries: means, population SDs, endpoint−start", fill="white", stroke="blue", chars=31)
    add_box(items, 1290, 255, 360, 145, "LSTM branch", "Full 30 × 21 sequence input\nseeds 43–45", fill="white", stroke="purple", chars=29)
    add_box(items, 1720, 70, 410, 175, "Fit PCA state", "Feature scaler + PCA (90% variance) + training empirical CDF + six q=0.995 thresholds", fill="white", stroke="blue", chars=37)
    add_box(items, 1720, 250, 410, 165, "Fit comparator", "Three fixed-epoch LSTMs; aligned calibrated-score arithmetic mean", fill="white", stroke="purple", chars=37)
    add_arrow(items, 355, 217, 415, 217, color="blue")
    add_arrow(items, 835, 217, 900, 217, color="blue")
    add_arrow(items, 1230, 195, 1290, 155, color="blue")
    add_arrow(items, 1230, 240, 1290, 325, color="purple")
    add_arrow(items, 1650, 155, 1720, 155, color="blue")
    add_arrow(items, 1650, 325, 1720, 325, color="purple")
    add_box(items, 55, 455, 300, 135, "Validation engines", "52 unseen engines\nproxy labels only", fill="lighter_gray", stroke="green", chars=23)
    add_box(items, 460, 430, 760, 185, "Registered validation comparison", "Select K/model candidates; compare five score sources; evaluate 1,280 alert candidates under five proxies and a predeclared lexicographic objective", fill="white", stroke="green", chars=68)
    add_box(items, 1305, 435, 340, 175, "Pre-held-out policy freeze", "Project governance Gate 4\nComplete policy locked before held-out access", fill="lighter_gray", stroke="vermillion", title_size=24, body_size=21, chars=30)
    add_box(items, 1730, 430, 410, 185, "Frozen roles", "Primary: PCA per-mode q=0.995 / EWMA 0.20 / persistence 8\nComparator: LSTM ensemble; no fusion", fill="white", stroke="vermillion", chars=38)
    add_arrow(items, 355, 522, 460, 522, color="green")
    add_line(items, 1720, 155, 1688, 155, color="blue", width=4)
    add_line(items, 1688, 155, 1688, 420, color="blue", width=4)
    add_line(items, 1688, 420, 1100, 420, color="blue", width=4)
    add_arrow(items, 1100, 420, 1100, 430, color="blue")
    add_line(items, 1720, 325, 1665, 325, color="purple", width=4)
    add_line(items, 1665, 325, 1665, 440, color="purple", width=4)
    add_arrow(items, 1665, 440, 1220, 440, color="purple")
    add_arrow(items, 1220, 522, 1305, 522, color="vermillion")
    add_arrow(items, 1645, 522, 1730, 522, color="vermillion")
    add_text(items, 1930, 650, "No PCA–LSTM score or decision fusion was implemented.", size=24, weight=600, anchor="middle", color="vermillion")
    add_line(items, 40, 700, 2360, 700, color="gray", width=3)
    add_text(items, 55, 750, "B. Frozen primary transformation and alert path", size=28, weight=600, anchor="start", color="blue")
    add_box(items, 40, 790, 280, 140, "Cycle rows", "engine, cycle, 3 settings, 21 sensors", fill="lighter_gray", stroke="blue", chars=25)
    add_box(items, 370, 770, 390, 180, "Frozen P1/K=6 transform", "Assign row modes; scale sensors by mode; window mode = mode at endpoint cycle", fill="white", stroke="blue", chars=35)
    add_box(items, 810, 790, 300, 140, "Engine-local windows", "30 × 21, stride 1", fill="white", stroke="blue", chars=25)
    add_box(items, 1160, 790, 300, 140, "PCA input", "63 ordered summary features", fill="white", stroke="blue", chars=24)
    add_box(items, 1510, 790, 300, 140, "Raw PCA score", "Mean squared residual in standardized feature space", fill="white", stroke="blue", chars=28)
    add_box(items, 1860, 790, 420, 140, "Frozen calibration", "Training empirical-CDF percentile", fill="white", stroke="blue", chars=34)
    add_arrow(items, 320, 860, 370, 860, color="blue")
    add_arrow(items, 760, 860, 810, 860, color="blue")
    add_arrow(items, 1110, 860, 1160, 860, color="blue")
    add_arrow(items, 1460, 860, 1510, 860, color="blue")
    add_arrow(items, 1810, 860, 1860, 860, color="blue")
    add_box(items, 1860, 1060, 420, 135, "EWMA", "α=0.20 on calibrated scores", fill="white", stroke="orange", chars=31)
    add_box(items, 1360, 1040, 430, 175, "Strict threshold comparison", "Compare smoothed score to frozen q=0.995 threshold for current endpoint mode", fill="white", stroke="orange", chars=38)
    add_box(items, 970, 1060, 320, 135, "Persistence", "Eight consecutive violations; no backdating", fill="white", stroke="orange", chars=28)
    add_box(items, 570, 1060, 330, 135, "Alert events", "Contiguous active endpoints within engine", fill="white", stroke="orange", chars=29)
    add_box(items, 1360, 1270, 430, 155, "Frozen threshold reference", "Six per-mode training thresholds; no online recalibration", fill="lighter_gray", stroke="vermillion", chars=38)
    add_box(items, 55, 1215, 430, 190, "PCA attribution", "Per-sensor mean/std/slope residual contribution ÷ 63; local model fidelity only—not physical fault localization", fill="white", stroke="green", chars=42)
    add_arrow(items, 2070, 930, 2070, 1060, color="orange")
    add_arrow(items, 1860, 1128, 1790, 1128, color="orange")
    add_arrow(items, 1360, 1128, 1290, 1128, color="orange")
    add_arrow(items, 970, 1128, 900, 1128, color="orange")
    add_arrow(items, 1575, 1270, 1575, 1215, color="vermillion")
    add_line(items, 1660, 930, 1660, 1000, color="green", width=4, dashed=True)
    add_line(items, 1660, 1000, 510, 1000, color="green", width=4, dashed=True)
    add_line(items, 510, 1000, 510, 1320, color="green", width=4, dashed=True)
    add_arrow(items, 510, 1320, 485, 1320, color="green", dashed=True)
    add_text(items, width / 2, 1515, "State resets at engine boundaries or endpoint gaps, not at mode changes. Official NASA-test evaluation is not part of this completed path.", size=24, anchor="middle", color="gray")
    return {
        "filename": "figure_01_system_architecture",
        "title": "Implemented system architecture",
        "description": "Two-lane diagram distinguishes training/validation fitting and selection from the frozen PCA transformation, calibration, EWMA, threshold comparison, persistence, event, and attribution path.",
        "width": width,
        "height": height,
        "width_mm": 190,
        "height_mm": 125,
        "data": {"primary": "PCA", "comparator": "LSTM calibrated ensemble", "fusion": False},
        "primitives": items,
    }


def build_protocol_figure() -> dict[str, Any]:
    width, height = 2200, 1450
    items: list[dict[str, Any]] = [primitive("rect", x=0, y=0, width=width, height=height, fill=PALETTE["white"], stroke=PALETTE["white"], stroke_width=0)]
    add_text(items, width / 2, 55, "Experimental protocol and evaluation boundaries", size=38, weight=600, anchor="middle")
    add_box(items, 790, 105, 620, 135, "FD002 run-to-failure source", "260 engines; deterministic whole-engine split", fill="lighter_gray", stroke="blue", chars=46)
    add_text(items, width / 2, 275, "Engine-disjoint: zero engine overlap", size=25, weight=600, anchor="middle", color="blue")
    add_box(items, 90, 340, 480, 170, "Training partition", "156 engines · 32,107 cycle rows · 27,583 windows", fill="white", stroke="blue", chars=38)
    add_box(items, 720, 340, 480, 170, "Validation partition", "52 engines · 10,873 cycle rows · 9,365 windows", fill="white", stroke="green", chars=38)
    add_box(items, 1350, 340, 480, 170, "Internal held-out partition", "52 engines · 10,779 cycle rows · 9,271 windows", fill="white", stroke="vermillion", chars=38)
    add_arrow(items, 900, 240, 330, 340, color="blue")
    add_arrow(items, 1100, 240, 960, 340, color="green")
    add_arrow(items, 1300, 240, 1590, 340, color="vermillion")
    add_box(items, 90, 610, 480, 240, "Training-only fitting", "Fit operating scaler/K-Means, sensor scalers, detectors, empirical CDFs, and threshold references. Healthy eligibility ends at first 30% of life.", fill="lighter_gray", stroke="blue", chars=42)
    add_box(items, 720, 610, 480, 240, "Validation selection", "Select K and candidates; compare score sources; evaluate 1,280 policies under registered proxies. No learned-state fitting.", fill="lighter_gray", stroke="green", chars=42)
    add_box(items, 1350, 610, 480, 240, "Held-out boundary", "Unavailable to fitting/selection. Access only after complete policy freeze; first valid run accepted regardless of values.", fill="lighter_gray", stroke="vermillion", chars=42)
    add_arrow(items, 330, 510, 330, 610, color="blue")
    add_arrow(items, 960, 510, 960, 610, color="green")
    add_arrow(items, 1590, 510, 1590, 610, color="vermillion")
    add_box(items, 520, 935, 520, 205, "Pre-held-out policy freeze", "Project governance Gate 4\nP1/K=6 + PCA + calibration + six per-mode q=0.995 thresholds + EWMA 0.20 + persistence 8", fill="white", stroke="vermillion", title_size=27, body_size=21, chars=46)
    add_arrow(items, 330, 850, 640, 935, color="blue")
    add_arrow(items, 960, 850, 900, 935, color="green")
    add_box(items, 1230, 950, 600, 175, "Completed internal held-out evaluation", "First valid frozen run; no refit, recalibration, reselection, online update, or fusion", fill="white", stroke="vermillion", chars=48)
    add_arrow(items, 1040, 1038, 1230, 1038, color="vermillion")
    add_arrow(items, 1590, 850, 1530, 950, color="vermillion")
    add_box(items, 520, 1220, 520, 135, "Validation evidence", "Model/policy selection only—not held-out performance", fill="white", stroke="green", chars=44)
    add_box(items, 1230, 1220, 600, 135, "Confirmatory evidence", "Proxy-labelled internal held-out results—not physical onset", fill="white", stroke="vermillion", chars=48)
    add_arrow(items, 780, 1140, 780, 1220, color="green")
    add_arrow(items, 1530, 1125, 1530, 1220, color="vermillion")
    add_box(items, 1870, 340, 260, 340, "Official NASA test", "Separate truncated-trajectory external protocol\n\nNot accessed\nNot completed\nFuture preregistration required", fill="white", stroke="gray", chars=24, dashed=True)
    add_box(items, 1870, 820, 260, 220, "Outside study", "Outside the completed study: no official-test, production, or real-aircraft result", fill="lighter_gray", stroke="gray", chars=24, dashed=True)
    add_arrow(items, 2000, 680, 2000, 820, color="gray", dashed=True)
    add_text(items, width / 2, 1410, "Proxy onsets are normalized-life evaluation rules, not observed physical fault-onset annotations.", size=24, weight=600, anchor="middle", color="gray")
    return {
        "filename": "figure_02_experimental_protocol",
        "title": "Experimental protocol and evaluation boundaries",
        "description": "Diagram shows the engine-disjoint train, validation, and internal held-out partitions; training-only fitting, validation selection, policy freeze, completed held-out evaluation, and deferred official NASA test.",
        "width": width,
        "height": height,
        "width_mm": 190,
        "height_mm": 125,
        "data": {"train_engines": 156, "validation_engines": 52, "held_out_engines": 52, "official_test_completed": False},
        "primitives": items,
    }


def svg_for_figure(figure: dict[str, Any]) -> str:
    width = figure["width"]
    height = figure["height"]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{figure["width_mm"]}mm" height="{figure["height_mm"]}mm" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(figure["title"])}</title>',
        f'<desc id="desc">{html.escape(figure["description"])}</desc>',
        '<style>text{font-family:Arial,Helvetica,sans-serif} .dash{stroke-dasharray:12 9}</style>',
    ]
    for item in figure["primitives"]:
        kind = item["type"]
        if kind == "rect":
            dash = ' class="dash"' if item.get("dash") else ""
            parts.append(
                f'<rect x="{item["x"]}" y="{item["y"]}" width="{item["width"]}" height="{item["height"]}" rx="{item.get("radius", 0)}" fill="{item["fill"]}" stroke="{item["stroke"]}" stroke-width="{item.get("stroke_width", 0)}"{dash}/>'
            )
        elif kind == "line":
            dash = ' class="dash"' if item.get("dash") else ""
            parts.append(
                f'<line x1="{item["x1"]}" y1="{item["y1"]}" x2="{item["x2"]}" y2="{item["y2"]}" stroke="{item["stroke"]}" stroke-width="{item["stroke_width"]}"{dash}/>'
            )
        elif kind == "arrow":
            x1, y1, x2, y2 = (float(item[key]) for key in ("x1", "y1", "x2", "y2"))
            angle = math.atan2(y2 - y1, x2 - x1)
            head = 18 + float(item["stroke_width"])
            wing = 0.48
            p1 = (x2 - head * math.cos(angle - wing), y2 - head * math.sin(angle - wing))
            p2 = (x2 - head * math.cos(angle + wing), y2 - head * math.sin(angle + wing))
            dash = ' class="dash"' if item.get("dash") else ""
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{item["stroke"]}" stroke-width="{item["stroke_width"]}"{dash}/>' )
            parts.append(f'<polygon points="{x2},{y2} {p1[0]},{p1[1]} {p2[0]},{p2[1]}" fill="{item["stroke"]}"/>')
        elif kind == "circle":
            parts.append(
                f'<circle cx="{item["cx"]}" cy="{item["cy"]}" r="{item["radius"]}" fill="{item["fill"]}" stroke="{item["stroke"]}" stroke-width="{item["stroke_width"]}"/>'
            )
        elif kind == "text":
            anchor = {"start": "start", "middle": "middle", "end": "end"}[item["anchor"]]
            text_value = html.escape(str(item["text"]))
            if "\n" in str(item["text"]):
                lines = str(item["text"]).split("\n")
                tspans = []
                for index, line in enumerate(lines):
                    dy = 0 if index == 0 else int(item["size"] * 1.25)
                    tspans.append(f'<tspan x="{item["x"]}" dy="{dy}">{html.escape(line)}</tspan>')
                text_value = "".join(tspans)
            parts.append(
                f'<text x="{item["x"]}" y="{item["y"]}" font-size="{item["size"]}" font-weight="{item["weight"]}" text-anchor="{anchor}" fill="{item["color"]}">{text_value}</text>'
            )
        else:
            raise ValueError(f"Unknown primitive: {kind}")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def architecture_dot() -> str:
    return r'''digraph SystemArchitecture {
  graph [rankdir=LR, splines=ortho, nodesep=0.35, ranksep=0.6, fontname="Arial", label="Implemented FD002 condition-aware anomaly-alert architecture", labelloc=t];
  node [shape=box, style="rounded", fontname="Arial"];
  edge [fontname="Arial"];
  subgraph cluster_fit {
    label="Training-only fitting and validation selection";
    train [label="156 training engines"];
    p1fit [label="Fit P1/K=6\nop scaler/K-Means: all train rows\nsensor scalers: early-life rows"];
    windows [label="30×21 training windows"];
    pca63 [label="PCA: 63 summaries"];
    lstmseq [label="LSTM: full 30×21 sequences"];
    pcastate [label="Fit feature scaler, PCA, empirical CDF,\nsix q=0.995 thresholds"];
    lstmstate [label="Three fixed-epoch LSTMs;\naligned calibrated-score mean"];
    validation [label="52 validation engines"];
    selection [label="Registered model and alert-policy selection"];
    freeze [label="Pre-held-out policy freeze\n(project governance Gate 4)\ncomplete policy locked before held-out access"];
    train -> p1fit -> windows;
    windows -> pca63 -> pcastate;
    windows -> lstmseq -> lstmstate;
    pcastate -> selection;
    lstmstate -> selection;
    validation -> selection -> freeze;
  }
  subgraph cluster_frozen {
    label="Frozen primary transformation and alert path";
    input [label="Cycle rows"];
    transform [label="Frozen P1/K=6 transform\nendpoint-cycle mode assignment"];
    window [label="30×21 windows"];
    summary [label="63 ordered summaries"];
    score [label="Raw PCA MSE"];
    calibration [label="Frozen empirical-CDF calibration"];
    ewma [label="EWMA α=0.20"];
    compare [label="Strict comparison with current-mode\nfrozen q=0.995 threshold"];
    persistence [label="Persistence 8"];
    events [label="Alert events"];
    attribution [label="PCA reconstruction-error contribution\nnon-causal; not physical localization"];
    input -> transform -> window -> summary -> score -> calibration -> ewma -> compare -> persistence -> events;
    score -> attribution [style=dashed];
  }
  freeze -> input;
  nofusion [shape=note, label="PCA–LSTM fusion not implemented"];
  lstmstate -> nofusion [style=dashed, arrowhead=none];
}
'''


def protocol_dot() -> str:
    return r'''digraph ExperimentalProtocol {
  graph [rankdir=TB, splines=ortho, nodesep=0.45, ranksep=0.65, fontname="Arial", label="Experimental protocol and evaluation boundaries", labelloc=t];
  node [shape=box, style="rounded", fontname="Arial"];
  edge [fontname="Arial"];
  source [label="FD002 run-to-failure source\n260 engines"];
  train [label="Training\n156 engines\n32,107 rows / 27,583 windows"];
  validation [label="Validation\n52 engines\n10,873 rows / 9,365 windows"];
  heldout [label="Internal held-out\n52 engines\n10,779 rows / 9,271 windows"];
  source -> train;
  source -> validation;
  source -> heldout;
  fit [label="Training-only fitting\npreprocessing, detectors, calibration, thresholds"];
  select [label="Validation selection\nK, model candidates, alert policy"];
  boundary [label="Held-out unavailable before freeze"];
  train -> fit;
  validation -> select;
  heldout -> boundary;
  freeze [label="Pre-held-out policy freeze\n(project governance Gate 4)\nP1/K=6 + PCA + calibration + q=0.995 per mode + EWMA 0.20 + persistence 8"];
  fit -> freeze;
  select -> freeze;
  confirm [label="Completed first valid internal held-out evaluation\nno refit/recalibration/reselection/fusion"];
  freeze -> confirm;
  boundary -> confirm;
  official [label="Official NASA test\nnot accessed; outside completed study", style="rounded,dashed"];
  future [label="Future separate preregistration required", style="rounded,dashed"];
  official -> future [style=dashed];
}
'''


def generate_figures(evidence: Evidence, rows: list[dict[str, Any]], validation_rows: list[dict[str, Any]]) -> tuple[list[Path], dict[str, Any]]:
    root = evidence.root
    figures = [
        build_architecture_figure(),
        build_protocol_figure(),
        build_operational_figure(rows),
        build_ranking_figure(rows),
        build_validation_figure(validation_rows),
    ]
    specs = {
        "schema_version": "1.0.0",
        "evidence_base_commit": EVIDENCE_BASE_COMMIT,
        "renderer": "dependency-free SVG primitives; matching System.Drawing PNG previews",
        "png_dpi": 300,
        "palette": PALETTE,
        "figures": figures,
    }
    specs_path = root / SOURCES_DIR / "figure_specs.json"
    write_json(specs_path, specs)
    dot_arch = root / SOURCES_DIR / "system_architecture.dot"
    dot_protocol = root / SOURCES_DIR / "experimental_protocol.dot"
    write_text(dot_arch, architecture_dot())
    write_text(dot_protocol, protocol_dot())
    outputs = [specs_path, dot_arch, dot_protocol]
    for figure in figures:
        svg_path = root / FIGURES_DIR / f"{figure['filename']}.svg"
        write_text(svg_path, svg_for_figure(figure))
        outputs.append(svg_path)
    return outputs, specs


def render_png_previews(root: Path) -> str:
    script = root / "scripts/manuscript/render_manuscript_v1_previews.ps1"
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-RepoRoot",
        str(root),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def captions_text() -> str:
    return """# Manuscript V1 captions

## Figure 1. Implemented FD002 condition-aware anomaly-alert architecture

Training-only fitting and validation selection are separated from the frozen primary path. P1/K=6 fits its operating-setting scaler and K-Means using training-engine rows and its per-mode sensor scalers using early-life training rows. Engine-local 30-cycle × 21-sensor windows feed 63 ordered mean, population-standard-deviation, and endpoint-minus-start features to PCA; the LSTM comparator instead consumes the full sequence. In the frozen primary path, raw PCA reconstruction MSE is mapped through the training empirical CDF, smoothed with EWMA α=0.20, compared strictly with the frozen q=0.995 threshold for the endpoint mode, and passed through persistence 8 before event extraction. PCA sensor attribution is an additive reconstruction-error contribution in normalized summary-feature space, not SHAP, causality, or physical fault localization. The LSTM ensemble is an unfused comparator; PCA–LSTM fusion was not implemented.

## Figure 2. Experimental protocol and evaluation boundaries

The deterministic FD002 split assigns complete engines to 156 training, 52 validation, and 52 internal held-out engines with zero overlap. Learned preprocessing, detector, calibration, and threshold state uses registered training populations only; validation selects K, model candidates, and the alert policy. At the pre-held-out policy freeze (project governance Gate 4), the complete configuration was locked before internal held-out access: P1/K=6 preprocessing, 30-cycle windows and 63 PCA summaries, PCA scoring, training-only empirical-CDF calibration, endpoint-mode assignment, six per-mode q=0.995 thresholds, EWMA 0.20, persistence 8, reset rules, proxy definitions, event/metric semantics, and the unfused LSTM comparator. The completed first valid held-out run allowed no refit, recalibration, reselection, online update, or fusion. NASA’s separate official test protocol was not accessed and remains outside the completed study.

## Figure 3. Frozen PCA internal held-out operational results

Endpoint false-alert rate (FAR), engine detection coverage, and median detection delay for final-10%, final-20%, and final-30% normalized-life endpoint proxies on 52 internal held-out engines. FAR is false-positive active endpoints divided by proxy-healthy endpoints; the dashed 6% line is the registered endpoint-FAR objective. Coverage is detected engines divided by 52. Delay is measured from proxy onset to the first valid post-onset event and is summarized among detected engines; missed engines remain represented in coverage. The dashed 12-cycle line is the aggregate delay aspiration, not a separately registered per-proxy pass/fail rule. The registered aggregate delay is the median of the three proxy-specific medians (12, 25, and 42.5 cycles), equal to 25 cycles. No confidence intervals or error bars were registered. These are proxy-labelled internal held-out results, not official NASA-test or physical fault-onset performance.

## Figure 4. Frozen PCA threshold-free ranking by onset proxy

PR-AUC and ROC-AUC of frozen PCA calibrated scores under final-10%, final-20%, and final-30% normalized-life endpoint proxies in the internal held-out partition (9,271 window endpoints from 52 engines). Metrics pool included window endpoints within each proxy and are threshold-free ranking measures, not accuracy. No ROC/PR curves, confidence intervals, or error bars are inferred.

## Figure 5. Validation/model-selection ranking evidence

Mean validation PR-AUC and ROC-AUC across the three registered endpoint proxies for five P1/K=6 score sources on the same 52-engine validation split. Values are validation/model-selection evidence, not internal held-out performance. LOF and One-Class SVM lead the registered ranking comparison; PCA was frozen later because it won the separately preregistered operational alert-policy objective. The LSTM value is the arithmetic mean of window-ID-aligned calibrated scores from three fixed-epoch seeds. No PCA–LSTM fusion or uncertainty interval was evaluated.

## Table 1. Dataset and experimental-protocol summary

Engine, cycle-row, and length-30-window counts and the permitted role of each partition. The split manifest’s `test` label denotes the internal held-out partition; it is not NASA’s separate official test set. Official-test evaluation was not accessed and remains deferred.

## Table 2. Frozen primary policy and verified settings

Registered split, P1/K=6 preprocessing, window/feature construction, PCA scoring, empirical-CDF calibration, per-mode thresholds, EWMA, persistence, state-reset, event, attribution, and comparator/fusion boundaries. Operating modes are context clusters rather than causal physical regimes, and PCA contributions are local normalized-feature-space reconstruction-error decompositions rather than physical localization.

## Table 3. Frozen internal held-out primary result

Frozen PCA results under three normalized-life endpoint proxies. FAR/1,000 and FAR percentage use proxy-healthy endpoints as the denominator; coverage uses all 52 engines. Delay medians use detected engines only, with misses exposed through coverage. Display values are rounded as declared while the CSV preserves source precision. All three FAR values met the registered objective; the 25-cycle aggregate median-of-proxy-medians delay missed the 12-cycle aspiration. Results are not official NASA-test or observed physical-onset performance.

## Table 4. Focused literature comparison

Relevance-selected Category B partial comparators and Category C contextual studies, followed by this study’s three frozen proxy rows. Native literature metrics retain their original task and units. `NR` means not reported; “not comparable” means the dataset/task, split, onset definition, denominator, aggregation, or alert semantics do not align. Specificity is not converted into project-compatible FAR. No Category A comparator was identified, so the table does not support a numerical ranking or superiority claim.
"""


def build_text() -> str:
    return f"""# Build manuscript V1 assets

## Scope and safety

The generator reads only the explicit aggregate/config/source allowlist in `scripts/manuscript/generate_manuscript_v1_assets.py`. It refuses dataset, model, per-engine-result, validation-score, and score-trace paths. It does not import the project package or run any scientific workflow.

## Regenerate all assets

From the repository root on Windows with the recorded Python 3.12 environment:

```powershell
{GENERATION_COMMAND}
```

This command generates editable figure specifications/DOT sources, SVG figures, 300-dpi PNG previews, Markdown/CSV/LaTeX tables, captions, build notes, and provenance.

## Render the venue-neutral LaTeX manuscript

`MANUSCRIPT_V1.md` is the editorial source of truth. After editing it, regenerate `manuscript_v1.tex` with:

```powershell
python scripts/manuscript/render_manuscript_v1_latex.py
```

The renderer supports the controlled Markdown constructs used by this manuscript, inserts the generated LaTeX table fragments, and references the PNG figure previews. It does not read scientific data or model artifacts.

## Build the alternative guide-review rendering

No TeX engine is installed in the review environment. The guide PDF is therefore explicitly an alternative HTML/MathML rendering, not a LaTeX compilation. Build its complete local HTML source with:

```powershell
python scripts/manuscript/build_guide_review_html.py --repo-root . --output C:\tmp\fd002_manuscript_v1_guide_review.html
```

Print that HTML with installed Microsoft Edge (`--headless --no-pdf-header-footer --allow-file-access-from-files --print-to-pdf=...`). Microsoft Word can open the same HTML and save it as Word Document format 16 to create the editable DOCX. The accepted PDF and the Word-rendered DOCX are each 19 pages. Both were rasterized with the Windows native PDF API and every page was visually inspected. The DOCX contains five figures, five rendered tables (Table 4 is split into its reader-facing comparison and evidence-locator display), and ten native editable Word equations.

The portable ZIP beside those files contains `manuscript_v1.tex`, `references_v1.bib`, all five required PNG figures, all four required LaTeX table fragments, and `README_BUILD.md`. It was extracted to a fresh temporary directory; all ten transitive LaTeX references resolved.

## Verify generated assets

```powershell
python scripts/manuscript/verify_manuscript_v1_assets.py --repo-root .
python scripts/manuscript/verify_manuscript_v1.py --repo-root .
```

The asset verifier checks allowlisted source hashes, exact registered values, citation keys, CSV-to-Markdown/LaTeX canonical digests, SVG well-formedness, PNG dimensions and 300-dpi metadata, and all generated-artifact hashes recorded in provenance. The manuscript verifier checks structure, citations, major numerical claims, cross-format consistency, figure/table paths, terminology, and LaTeX structure. Neither verifier accesses scientific data or models.

## Render PNG previews only

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manuscript/render_manuscript_v1_previews.ps1 -RepoRoot .
```

## Rendering tools and limitations

- SVG: dependency-free Python standard-library renderer from `figure_sources/figure_specs.json`.
- PNG: Windows `System.Drawing`, saved with 300-dpi metadata from the same primitive specifications.
- Editable diagrams: DOT sources plus the shared JSON primitive specification.
- Graphviz `dot` was unavailable, so DOT was not used for rendering. The committed SVGs are produced by the local deterministic renderer and remain editable vector files.
- Matplotlib, an SVG converter, and a LaTeX engine were unavailable. No dependency was installed. LaTeX table fragments and the complete manuscript source were generated but not compiled in this task.
- The venue-neutral manuscript LaTeX source was statically checked and packaged because no `pdflatex`, `xelatex`, `lualatex`, `latexmk`, `bibtex`, or `biber` executable was installed.
- `review_package/MANUSCRIPT_V1_GUIDE_REVIEW.pdf` is the 19-page Microsoft Edge HTML/MathML review rendering; it is not represented as LaTeX output.
- `review_package/MANUSCRIPT_V1_GUIDE_REVIEW.docx` is the editable Microsoft Word conversion; its 19-page Word PDF rendering was separately inspected.

## Display rounding

- FAR/1,000: 3 decimals.
- FAR percentage: 4 decimals.
- Coverage: 2 decimals.
- Delay: integer unless a half-cycle median is present.
- PR-AUC and ROC-AUC: 5 decimals.
- Machine-readable CSV and figure specifications retain source precision.

These conversions are display-only and do not replace the registered values.
"""


def selector_sources(evidence: Evidence) -> dict[str, list[dict[str, str]]]:
    def refs(items: Iterable[tuple[str, str]]) -> list[dict[str, str]]:
        return [
            {"path": path, "sha256": evidence.source_hashes[path], "selector": selector}
            for path, selector in items
        ]

    return {
        "architecture": refs(
            [
                ("configs/evaluation/fd002-confirmatory-execution-protocol-v1.json", "preprocessing, primary, comparator, evaluation"),
                ("configs/inference/fd002-frozen-inference-protocol-v1.json", "windowing, pca_score_and_attribution, frozen_policy"),
                ("src/turbofan_anomaly/data/preprocessing.py", "RegimeSensorPreprocessor.fit/transform"),
                ("src/turbofan_anomaly/data/metadata.py", "assign_endpoint_operating_modes"),
                ("src/turbofan_anomaly/data/windows.py", "summary_features"),
                ("src/turbofan_anomaly/models/classical.py", "ClassicalAnomalyModel.fit/_raw_scores_scaled/score"),
                ("src/turbofan_anomaly/alerting/calibration.py", "EmpiricalCDFCalibrator"),
                ("src/turbofan_anomaly/alerting/persistence.py", "apply_alert_policy"),
                ("src/turbofan_anomaly/explainability/pca_attribution.py", "attribute_pca_reconstruction"),
                ("src/turbofan_anomaly/models/lstm_training.py", "aligned_calibrated_score_ensemble"),
            ]
        ),
        "protocol": refs(
            [
                ("configs/splits/fd002-primary-v1.json", "split and engines"),
                ("configs/alerting/fd002-alert-policy-study-protocol-v2.json", "selection_objective, state_contract, metric_contract"),
                ("configs/evaluation/fd002-confirmatory-execution-protocol-v1.json", "partition, access_boundary, primary"),
                ("configs/evaluation/fd002-confirmatory-results-v1.json", "status, population, boundary booleans"),
            ]
        ),
        "operational": refs(
            [
                ("configs/evaluation/fd002-confirmatory-results-v1.json", "primary_endpoint_results, target_attainment"),
                ("reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/detector_policy_metrics.csv", "pca_reconstruction endpoint rows"),
            ]
        ),
        "ranking": refs(
            [
                ("configs/evaluation/fd002-confirmatory-results-v1.json", "primary_endpoint_results.pr_auc/roc_auc"),
                ("reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/ranking_metrics.csv", "pca_reconstruction endpoint rows"),
                ("src/turbofan_anomaly/evaluation/ranking.py", "proxy_ranking_metrics"),
            ]
        ),
        "validation": refs(
            [
                ("configs/alerting/fd002-alert-policy-study-results-v1.json", "score_reproduction"),
                ("configs/alerting/fd002-alert-policy-study-protocol-v2.json", "score_sources, selection_objective"),
            ]
        ),
        "dataset_table": refs(
            [
                ("configs/splits/fd002-primary-v1.json", "split.counts, engines[].cycle_count"),
                ("configs/baselines/fd002-classical-baselines-v1.json", "sequence_shapes.p1_k6"),
                ("configs/evaluation/fd002-confirmatory-results-v1.json", "population"),
            ]
        ),
        "policy_table": refs(
            [
                ("configs/evaluation/fd002-confirmatory-execution-protocol-v1.json", "preprocessing, primary, comparator"),
                ("configs/inference/fd002-frozen-inference-protocol-v1.json", "windowing, pca_score_and_attribution, frozen_policy"),
                ("src/turbofan_anomaly/alerting/persistence.py", "apply_alert_policy"),
            ]
        ),
        "literature_table": refs(
            [
                ("docs/research/core_literature_comparability_v1.json", "rows for LIT-010,013,007,008,009,012,018,006"),
                ("docs/research/CORE_MANUSCRIPT_EVIDENCE_V1.json", "papers and numerical_values for selected rows"),
                ("docs/research/MANUSCRIPT_CORE_CITATIONS_V1.bib", "core010, core013, core007, core008, core009, core012, core018, core006"),
                ("configs/evaluation/fd002-confirmatory-results-v1.json", "primary_endpoint_results"),
            ]
        ),
    }


def output_group(relative: str) -> str:
    name = Path(relative).name
    if name.startswith("figure_01") or name == "system_architecture.dot":
        return "architecture"
    if name.startswith("figure_02") or name == "experimental_protocol.dot":
        return "protocol"
    if name.startswith("figure_03"):
        return "operational"
    if name.startswith("figure_04"):
        return "ranking"
    if name.startswith("figure_05"):
        return "validation"
    if name.startswith("table_01"):
        return "dataset_table"
    if name.startswith("table_02"):
        return "policy_table"
    if name.startswith("table_03"):
        return "operational"
    if name.startswith("table_04"):
        return "literature_table"
    return "protocol"


def output_sources(
    relative: str,
    groups: dict[str, list[dict[str, str]]],
    evidence: Evidence,
) -> list[dict[str, str]]:
    """Return artifact-specific provenance, expanding shared narrative/spec outputs."""
    name = Path(relative).name
    if name == "BUILD.md":
        return [
            {
                "path": path,
                "sha256": evidence.source_hashes[path],
                "selector": "manuscript artifact requirements and evidence routing",
            }
            for path in (
                "docs/manuscript/v1/EVIDENCE_MAP.md",
                "docs/manuscript/v1/FIGURE_TABLE_PLAN.md",
            )
        ]
    if name in {"figure_specs.json", "CAPTIONS.md"}:
        ordered: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for group_name in (
            "architecture",
            "protocol",
            "operational",
            "ranking",
            "validation",
            "dataset_table",
            "policy_table",
            "literature_table",
        ):
            for source in groups[group_name]:
                identity = (source["path"], source["selector"])
                if identity not in seen:
                    ordered.append(source)
                    seen.add(identity)
        return ordered
    return groups[output_group(relative)]


def software_version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip() or result.stderr.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def write_provenance(evidence: Evidence, artifact_paths: list[Path], png_log: str) -> Path:
    root = evidence.root
    groups = selector_sources(evidence)
    artifacts = []
    for path in sorted(set(artifact_paths)):
        relative = path.relative_to(root).as_posix()
        artifacts.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "sources": output_sources(relative, groups, evidence),
            }
        )
    generator_files = []
    for relative in (
        "scripts/manuscript/generate_manuscript_v1_assets.py",
        "scripts/manuscript/render_manuscript_v1_previews.ps1",
        "scripts/manuscript/render_manuscript_v1_latex.py",
        "scripts/manuscript/build_guide_review_html.py",
        "scripts/manuscript/verify_manuscript_v1_assets.py",
        "scripts/manuscript/verify_manuscript_v1.py",
    ):
        path = root / relative
        generator_files.append({"path": relative, "sha256": sha256_file(path)})
    payload = {
        "schema_version": "1.0.0",
        "scope": "manuscript artifact generation from committed aggregate authorities only",
        "evidence_base_commit": EVIDENCE_BASE_COMMIT,
        "generation_command": GENERATION_COMMAND,
        "scientific_boundary": {
            "datasets_opened": False,
            "model_artifacts_opened": False,
            "inference_or_training_run": False,
            "metrics_recomputed_from_observations_or_score_traces": False,
            "dependencies_changed": False,
            "remote_refs_changed": False,
        },
        "software": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "powershell": software_version(["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
            "system_drawing": software_version(["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Drawing; [System.Drawing.Bitmap].Assembly.GetName().Version.ToString()"]),
            "svg_renderer": "Python standard library primitive renderer",
            "png_renderer": "System.Drawing at 300 dpi",
            "graphviz": "unavailable; DOT sources retained but not used for rendering",
            "matplotlib": "unavailable; not installed",
            "latex_engine": "unavailable; table fragments not compiled",
            "guide_pdf_renderer": "Microsoft Edge HTML/MathML print-to-PDF; 19 pages; visually inspected",
            "guide_docx_renderer": "Microsoft Word HTML conversion; 19 pages; visually inspected",
        },
        "display_rounding": {
            "far_per_1000_decimals": 3,
            "far_percent_decimals": 4,
            "coverage_percent_decimals": 2,
            "delay_cycles": "integer unless half-cycle median",
            "pr_auc_decimals": 5,
            "roc_auc_decimals": 5,
        },
        "allowlisted_inputs": [
            {"path": path, "sha256": evidence.source_hashes[path]} for path in ALLOWED_INPUTS
        ],
        "generator_files": generator_files,
        "manuscript_documents": [
            {
                "path": relative,
                "sha256": sha256_file(root / relative),
                "bytes": (root / relative).stat().st_size,
            }
            for relative in MANUSCRIPT_DOCUMENTS
        ],
        "review_documents": [
            {
                "path": relative,
                "sha256": sha256_file(root / relative),
                "bytes": (root / relative).stat().st_size,
            }
            for relative in REVIEW_DOCUMENTS
        ],
        "png_renderer_log": png_log,
        "artifacts": artifacts,
        "self_record": {
            "path": "docs/manuscript/v1/ARTIFACT_PROVENANCE.json",
            "sha256": None,
            "reason": "Self-hash omitted to avoid recursive content; verify this file through Git and git diff --check.",
        },
    }
    path = root / OUTPUT_ROOT / "ARTIFACT_PROVENANCE.json"
    write_json(path, payload)
    return path


def main() -> None:
    args = parse_args()
    evidence = load_evidence(args.repo_root)
    root = evidence.root
    require(evidence.confirm_results["status"] == "complete_first_valid_run", "Confirmatory result is not complete")
    require(evidence.confirm_results["official_nasa_test_accessed"] is False, "Official NASA-test boundary changed")
    require(evidence.confirm_results["score_or_decision_fusion"] is False, "Confirmatory fusion boundary changed")
    rows = confirmatory_rows(evidence)
    validation_rows = validation_model_rows(evidence)
    lit_rows = literature_rows(evidence)

    figure_outputs, specs = generate_figures(evidence, rows, validation_rows)
    table_outputs = generate_tables(evidence, rows, lit_rows)
    captions = root / OUTPUT_ROOT / "CAPTIONS.md"
    build = root / OUTPUT_ROOT / "BUILD.md"
    write_text(captions, captions_text())
    write_text(build, build_text())

    png_log = "PNG rendering skipped by --skip-png"
    png_outputs: list[Path] = []
    if not args.skip_png:
        png_log = render_png_previews(root)
        png_outputs = [root / FIGURES_DIR / f"{figure['filename']}.png" for figure in specs["figures"]]
        for path in png_outputs:
            require(path.is_file() and path.stat().st_size > 0, f"PNG preview missing: {path}")

    artifact_paths = figure_outputs + png_outputs + table_outputs + [captions, build]
    provenance = write_provenance(evidence, artifact_paths, png_log)
    print(f"Generated {len(artifact_paths) + 1} manuscript artifacts including provenance.")
    print(f"Provenance: {provenance.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
