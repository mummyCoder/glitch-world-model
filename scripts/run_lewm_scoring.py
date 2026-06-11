from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from glitch_detection.lewm_adapter import sha256_file
from glitch_detection.lewm_surprise import score_manifest
from glitch_detection.manifest import read_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score a manifest with LeWM latent surprise.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--action-mode", choices=["zero_action", "real"], default="zero_action")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--aggregation", choices=["mean", "max", "topk_mean"], default="mean")
    parser.add_argument("--expected-sha256", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = args.config or args.checkpoint.with_name("config.json")
    if not args.manifest.is_file():
        raise FileNotFoundError(f"Missing scoring manifest: {args.manifest}")
    if not args.checkpoint.is_file():
        raise FileNotFoundError(f"Missing LeWM checkpoint: {args.checkpoint}")
    if not config.is_file():
        raise FileNotFoundError(f"Missing LeWM config: {config}")
    records = read_manifest(args.manifest)
    checkpoint_hash = sha256_file(args.checkpoint)
    if args.expected_sha256 and checkpoint_hash != args.expected_sha256:
        raise ValueError("LeWM checkpoint SHA-256 does not match --expected-sha256.")
    plan = {
        "status": "dry-run" if args.dry_run else "scored",
        "manifest": str(args.manifest),
        "checkpoint": str(args.checkpoint),
        "config": str(config),
        "aggregation": args.aggregation,
        "action_mode": args.action_mode,
        "device": args.device,
        "clip_count": len(records),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return
    score_manifest(
        args.manifest,
        None,
        args.output,
        checkpoint=args.checkpoint,
        config=config,
        action_mode=args.action_mode,
        device=args.device,
        aggregation=args.aggregation,
        expected_sha256=args.expected_sha256,
    )
    metadata = {
        "scorer": "lewm_surprise",
        "aggregation": args.aggregation,
        "checkpoint_sha256": checkpoint_hash,
        "config_sha256": sha256_file(config),
        "manifest_sha256": sha256_file(args.manifest),
        "scores_sha256": sha256_file(args.output),
        "action_mode": args.action_mode,
        "device": args.device,
        "clip_count": len(records),
        "finite_score_count": len(records),
        "locked_test_scored": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
    }
    metadata_path = args.output.with_name("scoring_metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**plan, "metadata": str(metadata_path)}, indent=2))


if __name__ == "__main__":
    main()
