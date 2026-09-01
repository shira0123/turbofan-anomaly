"""Command-line adapter for the frozen FD002 PCA inference service."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from turbofan_anomaly.evaluation.provenance import find_repository_root
from turbofan_anomaly.inference.loader import PROTOCOL_PATH
from turbofan_anomaly.inference.pipeline import FrozenFD002InferencePipeline
from turbofan_anomaly.inference.visualization import render_timeline_svg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run only the registered frozen FD002 PCA policy.")
    parser.add_argument("--input", required=True, type=Path, help="FD002 cycle CSV with exact registered columns")
    parser.add_argument("--output", required=True, type=Path, help="JSON timeline destination")
    parser.add_argument("--csv-output", type=Path, help="Optional CSV timeline destination")
    parser.add_argument("--visualization", type=Path, help="Optional SVG timeline destination")
    parser.add_argument("--protocol", default=PROTOCOL_PATH, help="Must remain the one registered inference protocol")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing requested outputs")
    args = parser.parse_args(argv)
    if args.protocol.replace("\\", "/") != PROTOCOL_PATH:
        parser.error("only the registered frozen inference protocol is permitted")
    outputs = [args.output, *([args.csv_output] if args.csv_output else []), *([args.visualization] if args.visualization else [])]
    if not args.overwrite and any(path.exists() for path in outputs):
        parser.error("output exists; pass --overwrite to replace it")
    try:
        pipeline = FrozenFD002InferencePipeline.from_repository(find_repository_root(Path.cwd()))
        result = pipeline.infer(pd.read_csv(args.input))
        args.output.write_text(json.dumps(result.json_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.csv_output:
            csv = result.timeline.copy()
            csv["top_three_sensor_contributions"] = csv["top_three_sensor_contributions"].map(lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")))
            csv.to_csv(args.csv_output, index=False, lineterminator="\n")
        if args.visualization:
            render_timeline_svg(result.timeline, args.visualization)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, f"error: {error}\n")
    print(f"windows={len(result.timeline)} events={len(result.events)} policy=frozen_pca_per_mode_q0.995_ewma0.20_persistence8")
    return 0


if __name__ == "__main__":
    main()
