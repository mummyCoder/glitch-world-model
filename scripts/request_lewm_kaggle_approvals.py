from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_kaggle import request_package_approvals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create separate fingerprint-bound LeWM Kaggle approval requests."
    )
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--approvals-root", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(json.dumps(request_package_approvals(args.package_root, args.approvals_root), indent=2))


if __name__ == "__main__":
    main()
