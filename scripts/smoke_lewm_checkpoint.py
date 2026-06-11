from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Strict-load an official LeWM checkpoint.")
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--expected-sha256", default=None)
    parser.add_argument(
        "--action-mode", choices=[mode.value for mode in ActionMode], default="real"
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--run-inference-smoke", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    adapter = LeWMAdapter(
        LeWMCheckpointSpec(
            weights_path=args.weights,
            config_path=args.config,
            action_mode=ActionMode(args.action_mode),
            expected_sha256=args.expected_sha256,
            device=args.device,
        )
    ).load()
    audit = adapter.audit()
    if args.run_inference_smoke:
        audit.update(adapter.inference_smoke())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
