from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from glitch_detection.dataset_protocols import freeze_wob_split, write_frozen_split
from glitch_detection.wob_protocol import inspect_wob_episode_tar, parse_wob_inventory

ROOT = Path(__file__).resolve().parents[1]
NORMAL_SLUG = "benedictwilkinsai/world-of-bugs-normal"
TEST_SLUG = "benedictwilkinsai/world-of-bugs-test"


def _kaggle_csv(arguments: list[str]) -> list[dict[str, str]]:
    result = subprocess.run(
        [sys.executable, "-m", "kaggle", *arguments, "-v"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return list(csv.DictReader(io.StringIO(result.stdout)))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freeze metadata-only World of Bugs splits.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "gate3" / "world_of_bugs",
    )
    parser.add_argument("--normal-sample-tar", type=Path)
    parser.add_argument("--bug-sample-tar", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    normal_listing = _kaggle_csv(["datasets", "files", NORMAL_SLUG, "--page-size", "200"])
    test_listing = _kaggle_csv(["datasets", "files", TEST_SLUG, "--page-size", "200"])
    normal, _, normal_audit = parse_wob_inventory(normal_listing)
    _, bugs, test_audit = parse_wob_inventory(test_listing)
    if normal_audit["unknown_file_count"] or test_audit["unknown_file_count"]:
        raise RuntimeError("World of Bugs inventory contains unknown file paths.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = args.output_dir / "inventory.csv"
    with inventory_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source", "episode_id", "category", "label", "size_bytes"],
        )
        writer.writeheader()
        writer.writerows([*normal, *bugs])

    schema_audit = {
        "normal_inventory": normal_audit,
        "test_inventory": test_audit,
        "normal_sample": (
            inspect_wob_episode_tar(args.normal_sample_tar) if args.normal_sample_tar else None
        ),
        "bug_sample": inspect_wob_episode_tar(args.bug_sample_tar) if args.bug_sample_tar else None,
        "semantic_action_synchronization_verified": False,
        "locked_test_materialized": False,
    }
    schema_audit_path = args.output_dir / "protocol_audit.json"
    schema_audit_path.write_text(
        json.dumps(schema_audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    records = freeze_wob_split(normal, bugs, seed=args.seed)
    split_path, audit_path, provenance_path = write_frozen_split(
        args.output_dir / "split.csv",
        records,
        seed=args.seed,
        provenance={
            "access_date": date.today().isoformat(),
            "normal_dataset": NORMAL_SLUG,
            "test_dataset": TEST_SLUG,
            "normal_last_updated": "2022-02-22 15:07:30.350000",
            "test_last_updated": "2022-02-22 15:07:33.573000",
            "license": "ODC Attribution License (ODC-By)",
            "inventory_sha256": _sha256(inventory_path),
            "protocol_audit_sha256": _sha256(schema_audit_path),
            "raw_full_dataset_materialized_locally": False,
        },
    )
    print(
        json.dumps(
            {
                "inventory": str(inventory_path),
                "protocol_audit": str(schema_audit_path),
                "split": str(split_path),
                "audit": str(audit_path),
                "provenance": str(provenance_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
