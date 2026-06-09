from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from glitch_detection.model_selection import select_validation_config
from glitch_detection.video_eval import write_json

ROOT = Path(__file__).resolve().parents[1]


def load_validation_candidates(input_dir: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("*_video_calibration.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates.append(
            {
                "scorer": payload["scorer"],
                "aggregation": payload["aggregation"],
                "threshold": payload["threshold"],
                "validation_metrics": payload["validation_metrics"],
                "calibration_path": str(path),
            }
        )
    if not candidates:
        raise FileNotFoundError(f"No video calibration JSON files found in {input_dir}.")
    return candidates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select one TempGlitch protocol config using validation metrics only."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase3b_video_level",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--selection-metric", choices=["auroc", "f1"], default="auroc")
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_path = args.output or args.input_dir / "selected_protocol_config.json"
    selected = select_validation_config(
        load_validation_candidates(args.input_dir),
        selection_metric=args.selection_metric,
        seed=args.seed,
    )
    write_json(selected, output_path)
    print(f"Selected from validation only: {selected['scorer']}/{selected['aggregation']}")
    print(f"Selection metric: {selected['selection_metric']}={selected['selection_value']:.6g}")
    print(f"Selected config: {output_path}")


if __name__ == "__main__":
    main()
