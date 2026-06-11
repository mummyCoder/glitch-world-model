from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_gate6 import validate_gate6_artifacts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Strictly validate Gate 6 LeWM artifacts.")
    parser.add_argument("--artifacts-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = validate_gate6_artifacts(args.artifacts_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
