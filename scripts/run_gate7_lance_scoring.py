from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from glitch_detection.lewm_adapter import sha256_file
from glitch_detection.lewm_lance_eval import run_gate7_scoring

DEFAULT_CHECKPOINT_SHA256 = "3feefb1d1001f53ec659b45e7f47cfbc6418f56ea763513f970ec5b333119dbe"


def _validate_inputs(args: argparse.Namespace) -> None:
    for path, description in (
        (args.checkpoint, "checkpoint"),
        (args.config, "config"),
        (args.normal_lance, "normal Lance dataset"),
        (args.buggy_lance, "buggy Lance dataset"),
    ):
        if not path.exists():
            raise FileNotFoundError(f"Missing Gate 7 {description}: {path}")
    actual_hash = sha256_file(args.checkpoint)
    if actual_hash != args.expected_sha256:
        raise ValueError(
            "Gate 7 checkpoint SHA-256 mismatch: "
            f"expected {args.expected_sha256}, found {actual_hash}."
        )
    for path in (args.normal_lance, args.buggy_lance):
        if re.search(r"(?:^|[_-])locked(?:[_-]|$)", path.name.lower()):
            raise ValueError("Gate 7 refuses locked-test Lance paths.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score the non-locked Gate 6 Lance windows with the frozen LeWM checkpoint."
    )
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--normal-lance", required=True, type=Path)
    parser.add_argument("--buggy-lance", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-sha256", default=DEFAULT_CHECKPOINT_SHA256)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    _validate_inputs(args)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run",
                    "checkpoint_sha256": sha256_file(args.checkpoint),
                    "normal_lance": str(args.normal_lance),
                    "buggy_lance": str(args.buggy_lance),
                    "output_dir": str(args.output_dir),
                    "device": args.device,
                    "batch_size": args.batch_size,
                    "seed": args.seed,
                    "locked_test_materialized": False,
                    "locked_test_scored": False,
                },
                indent=2,
            )
        )
        return
    result = run_gate7_scoring(
        checkpoint=args.checkpoint,
        config=args.config,
        normal_lance=args.normal_lance,
        buggy_lance=args.buggy_lance,
        output_dir=args.output_dir,
        expected_sha256=args.expected_sha256,
        device=args.device,
        batch_size=args.batch_size,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
