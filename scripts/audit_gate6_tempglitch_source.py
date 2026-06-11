from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.gate6_data import audit_gate6_source, write_audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit local TempGlitch inputs for Gate 6.")
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--video-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-count", type=int, default=20)
    parser.add_argument("--validation-count", type=int, default=10)
    parser.add_argument("--buggy-probe-count", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    payload = audit_gate6_source(
        args.metadata,
        args.split,
        args.video_root,
        seed=args.seed,
        train_count=args.train_count,
        validation_count=args.validation_count,
        buggy_probe_count=args.buggy_probe_count,
    )
    write_audit(payload, args.output)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
