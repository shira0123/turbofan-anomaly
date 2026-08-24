"""Create safe, traceable metadata for training and validation windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from turbofan_anomaly.data.metadata import create_window_metadata


MANIFEST_SPLITS = ("train", "validation", "test")
SAFE_METADATA_SPLITS = ("train", "validation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("configs/splits/fd002-primary-v1.json"),
    )
    parser.add_argument("--splits-dir", type=Path, default=Path("data/splits"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--window-size", type=int, default=30)
    parser.add_argument(
        "--include-internal-test",
        action="store_true",
        help=(
            "also open test.csv and create internal-test metadata; requires an "
            "explicit post-freeze authorization"
        ),
    )
    return parser.parse_args()


def selected_metadata_splits(*, include_internal_test: bool) -> tuple[str, ...]:
    """Return safe default splits, adding internal test only by explicit opt-in."""
    if include_internal_test:
        return (*SAFE_METADATA_SPLITS, "test")
    return SAFE_METADATA_SPLITS


def _manifest_engine_sets(manifest: dict) -> dict[str, set[int]]:
    return {
        split: {
            int(record["engine"])
            for record in manifest["engines"]
            if record["split"] == split
        }
        for split in MANIFEST_SPLITS
    }


def main() -> None:
    args = parse_args()
    if not args.manifest.exists():
        raise FileNotFoundError(
            f"Split manifest not found: {args.manifest}. Run scripts.make_splits first."
        )

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    engine_sets = _manifest_engine_sets(manifest)
    manifest_id = str(manifest["manifest_id"])
    source_hash = str(manifest["dataset"]["sha256"])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, dict[str, int | str]] = {}
    selected_splits = selected_metadata_splits(
        include_internal_test=args.include_internal_test
    )
    for split in selected_splits:
        split_path = args.splits_dir / f"{split}.csv"
        if not split_path.exists():
            raise FileNotFoundError(f"Missing split CSV: {split_path}")
        split_frame = pd.read_csv(split_path)
        actual_engines = set(split_frame["engine"].astype(int).unique())
        if actual_engines != engine_sets[split]:
            raise RuntimeError(
                f"{split_path} engine IDs do not match manifest {manifest_id}"
            )

        metadata = create_window_metadata(
            split_frame,
            split=split,
            manifest_id=manifest_id,
            source_dataset_sha256=source_hash,
            window_size=args.window_size,
        )
        output_path = args.output_dir / f"window_metadata_{split}.csv"
        metadata.to_csv(output_path, index=False)
        outputs[split] = {
            "engines": len(actual_engines),
            "windows": len(metadata),
            "path": output_path.as_posix(),
        }

    print({"manifest_id": manifest_id, "outputs": outputs})


if __name__ == "__main__":
    main()
