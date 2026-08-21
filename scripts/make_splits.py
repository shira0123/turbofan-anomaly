"""Create deterministic, engine-disjoint FD002 train/validation/test splits."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.data.split_manifest import (
    build_split_manifest,
    load_fd002,
    write_manifest,
    write_split_csvs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/train_FD002.txt"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/splits"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("configs/splits/fd002-primary-v1.json"),
    )
    parser.add_argument("--manifest-id", default="fd002-primary-v1")
    parser.add_argument("--train-ratio", type=float, default=0.60)
    parser.add_argument("--validation-ratio", type=float, default=0.20)
    parser.add_argument("--test-ratio", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--strata", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = load_fd002(args.raw)
    manifest = build_split_manifest(
        frame=frame,
        source_path=args.raw,
        manifest_id=args.manifest_id,
        ratios={
            "train": args.train_ratio,
            "validation": args.validation_ratio,
            "test": args.test_ratio,
        },
        seed=args.seed,
        n_strata=args.strata,
    )
    write_manifest(manifest, args.manifest)
    outputs = write_split_csvs(frame, manifest, args.output_dir)

    engines_by_split = {
        name: {
            int(record["engine"])
            for record in manifest["engines"]
            if record["split"] == name
        }
        for name in outputs
    }
    summary = {
        name: {
            "engines": manifest["split"]["counts"][name],
            "rows": int(frame["engine"].isin(engines_by_split[name]).sum()),
            "path": str(path),
        }
        for name, path in outputs.items()
    }
    print(
        {
            "manifest": str(args.manifest),
            "source_sha256": manifest["dataset"]["sha256"],
            "splits": summary,
        }
    )

if __name__ == "__main__":
    main()
