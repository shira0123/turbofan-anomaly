#!/usr/bin/env python3
"""Verify manuscript V1 assets without opening scientific data or model artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
from typing import Any


PROHIBITED_ROOT_PREFIXES = (
    "/data/raw/",
    "/data/processed/",
    "/data/splits/",
    "/models/",
)

PROHIBITED_PARTS = (
    "score_alert_trace",
    "validation_scores",
    "per_engine_metrics",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_generator(root: Path) -> Any:
    path = root / "scripts/manuscript/generate_manuscript_v1_assets.py"
    spec = importlib.util.spec_from_file_location("manuscript_asset_generator", path)
    require(spec is not None and spec.loader is not None, f"Cannot import generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_string_rows(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, str]]:
    return [{field: str(row.get(field, "")) for field in fields} for row in rows]


def embedded_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"canonical-sha256:\s*([0-9a-f]{64})", text)
    require(match is not None, f"Missing canonical digest: {path}")
    return match.group(1)


def table_04_rows(generator: Any, evidence: Any, result_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = list(generator.literature_rows(evidence))
    for row in result_rows:
        rows.append(
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
                "evidence_location": (
                    "configs/evaluation/fd002-confirmatory-results-v1.json: "
                    f"primary_endpoint_results[{row['policy_id']}]"
                ),
                "comparability_caveat": (
                    "Proxy-labelled internal held-out result; not official NASA-test or observed physical onset."
                ),
            }
        )
    return rows


def expected_tables(generator: Any, evidence: Any) -> dict[str, tuple[list[dict[str, Any]], list[str], list[str]]]:
    result_rows = generator.confirmatory_rows(evidence)
    result_csv_rows = [
        {
            **row,
            "fp_over_healthy": f"{row['false_positive_endpoints']}/{row['healthy_endpoints']}",
            "detected_over_engines": f"{row['detected_engines']}/{row['engine_count']}",
        }
        for row in result_rows
    ]
    return {
        "table_01_dataset_protocol_summary": (
            generator.dataset_rows(evidence),
            [
                "partition", "manifest_name", "engines", "cycle_rows", "length_30_windows",
                "role", "fitting_allowed", "evidence_status",
            ],
            [
                "partition", "manifest_name", "engines", "cycle_rows", "length_30_windows",
                "role", "fitting_allowed", "evidence_status",
            ],
        ),
        "table_02_frozen_primary_policy": (
            generator.policy_rows(evidence),
            ["component", "verified_setting", "fit_or_derivation_boundary", "source_selector"],
            ["component", "verified_setting", "fit_or_derivation_boundary", "source_selector"],
        ),
        "table_03_confirmatory_results": (
            result_csv_rows,
            [
                "policy_id", "proxy", "false_positive_endpoints", "healthy_endpoints",
                "fp_over_healthy", "far_per_1000", "far_percent", "detected_engines",
                "engine_count", "detected_over_engines", "coverage_percent",
                "median_delay_cycles", "pr_auc", "roc_auc", "delay_population",
            ],
            [
                "proxy", "fp_over_healthy", "far_per_1000", "far_percent",
                "detected_over_engines", "coverage_percent", "median_delay_cycles",
                "pr_auc", "roc_auc",
            ],
        ),
        "table_04_literature_comparison": (
            table_04_rows(generator, evidence, result_rows),
            [
                "panel", "study", "citation_key", "category", "dataset_task", "split_and_labels",
                "learning_and_model", "reported_native_metrics", "project_compatible_far",
                "project_compatible_other_metrics", "evidence_location", "comparability_caveat",
            ],
            [
                "study", "citation_key", "category", "dataset_task", "split_and_labels",
                "reported_native_metrics", "project_compatible_far", "evidence_location",
                "comparability_caveat",
            ],
        ),
    }


def verify_tables(root: Path, generator: Any, evidence: Any) -> None:
    table_root = root / "docs/manuscript/v1/tables"
    for name, (rows, fields, display_fields) in expected_tables(generator, evidence).items():
        csv_path = table_root / f"{name}.csv"
        md_path = table_root / f"{name}.md"
        tex_path = table_root / f"{name}.tex"
        require(read_csv(csv_path) == csv_string_rows(rows, fields), f"CSV content mismatch: {csv_path}")
        expected_digest = generator.canonical_digest(rows, display_fields)
        require(embedded_digest(md_path) == expected_digest, f"Markdown table mismatch: {md_path}")
        require(embedded_digest(tex_path) == expected_digest, f"LaTeX table mismatch: {tex_path}")


def png_metadata(path: Path) -> tuple[int, int, int | None, int | None, int | None]:
    data = path.read_bytes()
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), f"Invalid PNG signature: {path}")
    offset = 8
    width = height = None
    x_ppm = y_ppm = unit = None
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        if chunk_type == b"IHDR":
            width, height = struct.unpack(">II", chunk_data[:8])
        elif chunk_type == b"pHYs":
            x_ppm, y_ppm, unit = struct.unpack(">IIB", chunk_data)
        offset += 12 + length
        if chunk_type == b"IEND":
            break
    require(width is not None and height is not None, f"PNG lacks IHDR: {path}")
    return width, height, x_ppm, y_ppm, unit


def verify_figures(root: Path) -> None:
    specs_path = root / "docs/manuscript/v1/figure_sources/figure_specs.json"
    specs = json.loads(specs_path.read_text(encoding="utf-8"))
    require(specs["png_dpi"] == 300, "Figure specification DPI changed")
    require(len(specs["figures"]) == 5, "Expected five figure specifications")
    for figure in specs["figures"]:
        svg_path = root / "docs/manuscript/v1/figures" / f"{figure['filename']}.svg"
        png_path = root / "docs/manuscript/v1/figures" / f"{figure['filename']}.png"
        svg_root = ET.parse(svg_path).getroot()
        require(svg_root.attrib.get("viewBox") == f"0 0 {figure['width']} {figure['height']}", f"SVG viewBox mismatch: {svg_path}")
        width, height, x_ppm, y_ppm, unit = png_metadata(png_path)
        expected_width = round(float(figure["width_mm"]) / 25.4 * 300)
        expected_height = round(float(figure["height_mm"]) / 25.4 * 300)
        require((width, height) == (expected_width, expected_height), f"PNG size mismatch: {png_path}")
        require(unit == 1 and x_ppm is not None and y_ppm is not None, f"PNG physical resolution missing: {png_path}")
        x_dpi = x_ppm * 0.0254
        y_dpi = y_ppm * 0.0254
        require(abs(x_dpi - 300) < 0.1 and abs(y_dpi - 300) < 0.1, f"PNG is not 300 dpi: {png_path}")
    for name in ("system_architecture.dot", "experimental_protocol.dot"):
        text = (root / "docs/manuscript/v1/figure_sources" / name).read_text(encoding="utf-8")
        require(text.lstrip().startswith("digraph "), f"Invalid DOT source: {name}")


def verify_provenance(root: Path, generator: Any, evidence: Any) -> tuple[int, int]:
    path = root / "docs/manuscript/v1/ARTIFACT_PROVENANCE.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(payload["evidence_base_commit"] == generator.EVIDENCE_BASE_COMMIT, "Evidence base commit mismatch")
    boundary = payload["scientific_boundary"]
    require(all(value is False for value in boundary.values()), "Scientific boundary flags must all be false")
    for item in payload["allowlisted_inputs"]:
        normalized = "/" + item["path"].replace("\\", "/").lower()
        require(
            not normalized.startswith(PROHIBITED_ROOT_PREFIXES)
            and not any(part in normalized for part in PROHIBITED_PARTS),
            f"Prohibited provenance input: {item['path']}",
        )
        require(evidence.source_hashes[item["path"]] == item["sha256"], f"Source hash mismatch: {item['path']}")
    for item in payload["generator_files"]:
        require(sha256_file(root / item["path"]) == item["sha256"], f"Generator hash mismatch: {item['path']}")
    for item in payload["artifacts"]:
        artifact = root / item["path"]
        require(artifact.is_file(), f"Missing artifact: {item['path']}")
        require(artifact.stat().st_size == item["bytes"], f"Artifact byte count mismatch: {item['path']}")
        require(sha256_file(artifact) == item["sha256"], f"Artifact hash mismatch: {item['path']}")
        require(item["sources"], f"Artifact lacks source provenance: {item['path']}")
        for source in item["sources"]:
            require(evidence.source_hashes[source["path"]] == source["sha256"], f"Artifact source hash mismatch: {source['path']}")
    return len(payload["allowlisted_inputs"]), len(payload["artifacts"])


def verify_registered_values(generator: Any, evidence: Any) -> None:
    rows = generator.confirmatory_rows(evidence)
    expected = [
        (32.43971110295018, 3.2439711102950177, 51.92307692307692, 12.0, 0.6026705075624872, 0.9476205805711868),
        (9.443269908386187, 0.9443269908386187, 78.84615384615384, 25.0, 0.8097437092694553, 0.926731911712888),
        (5.152925531914893, 0.5152925531914894, 84.61538461538461, 42.5, 0.8274519039746946, 0.8675761206164003),
    ]
    actual = [
        (row["far_per_1000"], row["far_percent"], row["coverage_percent"], row["median_delay_cycles"], row["pr_auc"], row["roc_auc"])
        for row in rows
    ]
    require(actual == expected, "Registered confirmatory values changed")
    validation = generator.validation_model_rows(evidence)
    require(len(validation) == 5, "Validation comparison set changed")
    literature = generator.literature_rows(evidence)
    require([row["citation_key"] for row in literature] == ["core010", "core013", "core007", "core008", "core009", "core012", "core018", "core006"], "Literature citation-key set changed")
    require("No Category A comparator was identified" in (root := evidence.root / "docs/manuscript/v1/tables/table_04_literature_comparison.md").read_text(encoding="utf-8"), f"Missing Category A caveat: {root}")


def main() -> None:
    root = args_root = parse_args().repo_root.resolve()
    generator = load_generator(root)
    evidence = generator.load_evidence(args_root)
    verify_registered_values(generator, evidence)
    verify_tables(root, generator, evidence)
    verify_figures(root)
    source_count, artifact_count = verify_provenance(root, generator, evidence)
    print(
        "Verified exact registered values, four tables across CSV/Markdown/LaTeX, "
        f"five SVG/PNG figure pairs at 300 dpi, eight literature citation keys, "
        f"{source_count} allowlisted source hashes, and {artifact_count} artifact hashes."
    )
    print("No scientific data, model artifact, score trace, or per-engine result path was accessed.")


if __name__ == "__main__":
    main()
