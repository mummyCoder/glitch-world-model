from __future__ import annotations

import argparse
from pathlib import Path

from glitch_detection.tempglitch import (
    DATASET_PAGE_URL,
    DEFAULT_CATEGORIES,
    download_tempglitch_subset,
)

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download a tiny public TempGlitch subset.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "raw" / "tempglitch_smoke",
        help="Root directory for downloaded videos and metadata.",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=[DEFAULT_CATEGORIES[0]],
        help="TempGlitch categories to sample from.",
    )
    parser.add_argument(
        "--limit-per-group",
        type=int,
        default=1,
        help="Number of videos to download per category and label group.",
    )
    parser.add_argument(
        "--sample-mode",
        choices=["sequential", "random-stratified"],
        default="sequential",
        help="Sequential smoke sampling or seeded random sampling within category/label groups.",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    samples, metadata_path, readme_path = download_tempglitch_subset(
        output_dir=args.output_dir,
        categories=args.categories,
        limit_per_group=args.limit_per_group,
        sample_mode=args.sample_mode,
        seed=args.seed,
    )
    print(f"Dataset page: {DATASET_PAGE_URL}")
    print(f"Videos:       {len(samples)}")
    print(f"Metadata:     {metadata_path}")
    print(f"Source notes: {readme_path}")
    for sample in samples:
        print(f"- {sample.category} / {sample.public_label}: {sample.local_video_path}")


if __name__ == "__main__":
    main()
