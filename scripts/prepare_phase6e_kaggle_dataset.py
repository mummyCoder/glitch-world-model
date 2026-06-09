from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from glitch_detection.manifest import read_manifest

ROOT = Path(__file__).resolve().parents[1]
DATASET_METADATA_TEMPLATE = {
    "title": "glitch-world-model-phase6e",
    "id": "YOUR_KAGGLE_USERNAME/glitch-world-model-phase6e",
    "licenses": [{"name": "other"}],
}


def _require_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}: {path}")
    return path


def _estimate_directory(path: Path) -> tuple[int, int]:
    files = [item for item in path.rglob("*") if item.is_file()]
    return len(files), sum(item.stat().st_size for item in files)


def _upload_readme(processed_root: Path, split_path: Path) -> str:
    return f"""# Phase 6E Kaggle Upload Package

This generated folder is for a private Kaggle Dataset used by the Conv3D video autoencoder
learned baseline. It is not LeWorldModel or JEPA.

- Processed source: `{processed_root}`
- Grouped split source: `{split_path}`
- Keep this dataset private.
- Review the upstream TempGlitch license before editing `dataset-metadata.template.json`.
- Do not commit this generated folder, processed clips, scores, or checkpoints.
- Kaggle training must fit train-normal clips and score validation only.
- Locked test must remain untouched.
"""


def prepare_phase6e_kaggle_dataset(
    processed_root: Path,
    split_path: Path,
    output_root: Path,
    dry_run: bool,
    mode: str = "copy",
) -> dict[str, Any]:
    if not processed_root.is_dir():
        raise FileNotFoundError(f"Missing processed root: {processed_root}")
    manifest_path = _require_file(processed_root / "manifest.csv", "processed manifest")
    _require_file(split_path, "grouped split")
    if mode not in {"copy", "symlink"}:
        raise ValueError("mode must be 'copy' or 'symlink'.")

    records = read_manifest(manifest_path)
    missing_clip_dirs = [
        record.clip_dir for record in records if not Path(record.clip_dir).is_dir()
    ]
    if missing_clip_dirs:
        preview = ", ".join(missing_clip_dirs[:3])
        raise FileNotFoundError(
            f"{len(missing_clip_dirs)} manifest clip directories do not resolve. First: {preview}"
        )
    file_count, total_bytes = _estimate_directory(processed_root)
    summary: dict[str, Any] = {
        "status": "dry-run only" if dry_run else "dataset package complete",
        "mode": mode,
        "processed_root": str(processed_root),
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "output_root": str(output_root),
        "manifest_clip_count": len(records),
        "missing_clip_dir_count": len(missing_clip_dirs),
        "estimated_file_count": file_count,
        "estimated_total_bytes": total_bytes,
        "estimated_total_gib": total_bytes / (1024**3),
        "test_scored": False,
    }
    if dry_run:
        return summary

    if output_root.exists():
        raise FileExistsError(
            f"Output root already exists; remove or choose another path explicitly: {output_root}"
        )
    output_root.mkdir(parents=True)
    target_processed_root = output_root / "tempglitch_phase3b"
    if mode == "copy":
        shutil.copytree(processed_root, target_processed_root)
    else:
        target_processed_root.symlink_to(processed_root.resolve(), target_is_directory=True)
    shutil.copy2(split_path, output_root / "split.csv")
    (output_root / "dataset-metadata.template.json").write_text(
        json.dumps(DATASET_METADATA_TEMPLATE, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_root / "UPLOAD_README.md").write_text(
        _upload_readme(processed_root, split_path),
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the private Phase 6E Kaggle dataset.")
    parser.add_argument(
        "--processed-root",
        type=Path,
        default=ROOT / "data" / "processed" / "tempglitch_phase3b",
    )
    parser.add_argument(
        "--split",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6d" / "seed_42" / "split.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "kaggle_phase6e_dataset",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--copy", action="store_true", help="Copy files into the upload package.")
    mode.add_argument(
        "--symlink",
        action="store_true",
        help="Create a local symlink package; copy is safer for Kaggle upload.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = prepare_phase6e_kaggle_dataset(
        processed_root=args.processed_root,
        split_path=args.split,
        output_root=args.output_root,
        dry_run=args.dry_run,
        mode="symlink" if args.symlink else "copy",
    )
    print(f"Phase 6E Kaggle dataset status: {summary['status']}")
    print(f"Manifest clips: {summary['manifest_clip_count']}")
    print(f"Missing clip directories: {summary['missing_clip_dir_count']}")
    print(f"Estimated files: {summary['estimated_file_count']}")
    print(f"Estimated size: {summary['estimated_total_gib']:.3f} GiB")
    print(f"Test scored: {summary['test_scored']}")


if __name__ == "__main__":
    main()
