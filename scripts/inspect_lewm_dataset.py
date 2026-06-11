from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_data import inspect_lance_dataset, write_dataset_inspection


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a stable-worldmodel Lance dataset.")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--num-steps", type=int, default=4)
    parser.add_argument("--frameskip", type=int, default=1)
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = inspect_lance_dataset(
        args.dataset,
        num_steps=args.num_steps,
        frameskip=args.frameskip,
    )
    if args.output:
        write_dataset_inspection(summary, args.output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
