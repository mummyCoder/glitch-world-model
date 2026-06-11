from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_gate6 import Gate6KaggleConfig, prepare_gate6_kaggle_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the Gate 6 LeWM Kaggle package.")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--dataset-slug", required=True)
    parser.add_argument("--kernel-slug", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--train-dataset-name", required=True)
    parser.add_argument("--validation-dataset-name", required=True)
    parser.add_argument("--buggy-probe-dataset-name", required=True)
    parser.add_argument("--image-size", type=int, default=112)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--max-train-steps", type=int, default=16)
    parser.add_argument("--max-validation-steps", type=int, default=8)
    parser.add_argument("--sigreg-projections", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--package-version", default="v1")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = Gate6KaggleConfig(
        dataset_slug=args.dataset_slug,
        kernel_slug=args.kernel_slug,
        dataset_id=args.dataset_id,
        train_dataset_name=args.train_dataset_name,
        validation_dataset_name=args.validation_dataset_name,
        buggy_probe_dataset_name=args.buggy_probe_dataset_name,
        image_size=args.image_size,
        batch_size=args.batch_size,
        max_epochs=args.max_epochs,
        max_train_steps=args.max_train_steps,
        max_validation_steps=args.max_validation_steps,
        sigreg_projections=args.sigreg_projections,
        seed=args.seed,
        package_version=args.package_version,
    )
    print(
        json.dumps(
            prepare_gate6_kaggle_package(
                args.source_root,
                args.output_root,
                config,
                dry_run=args.dry_run,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
