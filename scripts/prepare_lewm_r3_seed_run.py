from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from glitch_detection.kaggle_automation import FingerprintBuilder

EXPECTED_HASHES = {
    "train": "e6c48a35eef32edf43a6c78db37c52adcbbe656f47b2e453e1917365355f3aa1",
    "validation_normal": "bb89e66c6afa5d3af7728be8efd0bacbf49cfedca6704fd27cc6178f27e556e6",
}


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def git_sha(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout.strip()


def prepare_seed_run(
    *,
    repo_root: Path,
    config_path: Path,
    lance_root: Path,
    output_root: Path,
    seed: int,
) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    training = config["training"]
    main_run = training["main_run"]
    seed_order = list(main_run["seed_order"])
    if seed != seed_order[0]:
        raise ValueError("R3 must run seed 42 first before preparing later seeds.")
    train = lance_root / "tempglitch_train_normal_all_local.lance"
    validation = lance_root / "tempglitch_validation_normal_all_local.lance"
    if not train.is_dir() or not validation.is_dir():
        raise FileNotFoundError(
            "R3 seed run requires train-normal and validation-normal Lance dirs."
        )
    dataset_hashes = {
        "train": FingerprintBuilder.inventory_sha256(train),
        "validation_normal": FingerprintBuilder.inventory_sha256(validation),
    }
    if dataset_hashes != EXPECTED_HASHES:
        raise ValueError("R3 Lance hashes do not match the frozen research MVP config.")
    payload = {
        "git_sha": git_sha(repo_root),
        "config_sha256": FingerprintBuilder.sha256_file(config_path),
        "dataset_hashes": dataset_hashes,
        "seed": seed,
        "batch_size": training["batch_size"],
        "amp": training["amp"],
        "num_workers": training["num_workers"],
        "target_optimizer_updates": main_run["target_optimizer_updates"],
        "evaluation_interval_updates": main_run["evaluation_interval_updates"],
        "checkpoint_interval_updates": main_run["checkpoint_interval_updates"],
    }
    fingerprint = canonical_sha256(payload)
    plan = {
        "status": "r3_seed_run_prepared",
        "evidence_class": "training-preflight-only",
        "fingerprint": fingerprint,
        "seed": seed,
        "payload": payload,
        "train_dataset": str(train),
        "validation_dataset": str(validation),
        "validation_buggy_used_for_fit_or_selection": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "next_required_runtime": "update_based_lewm_main_trainer",
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "r3_seed_run_plan.json").write_text(
        json.dumps(plan, indent=2) + "\n",
        encoding="utf-8",
    )
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare an R3 LeWM seed run preflight.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path("configs/lewm_research_mvp.yaml"))
    parser.add_argument("--lance-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(
        json.dumps(
            prepare_seed_run(
                repo_root=args.repo_root,
                config_path=args.config,
                lance_root=args.lance_root,
                output_root=args.output_root,
                seed=args.seed,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
