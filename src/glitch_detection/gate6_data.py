from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def read_rows_by_source(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return {row["source"]: row for row in csv.DictReader(handle)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_tempglitch_rows(
    metadata: dict[str, dict[str, str]],
    split: dict[str, dict[str, str]],
    *,
    partition: str,
    label_filter: str | None,
    max_episodes: int | None,
    seed: int = 42,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in metadata:
        row = split.get(source)
        if row is None:
            raise ValueError(f"Missing frozen TempGlitch split row for source {source!r}.")
        if row["split"] != partition or row["materialize"].lower() != "true":
            continue
        if label_filter is not None and row["label"] != label_filter:
            continue
        rows.append(row)
    rows.sort(key=lambda row: hashlib.sha256(f"{seed}:{row['source']}".encode()).hexdigest())
    return rows if max_episodes is None else rows[:max_episodes]


def audit_gate6_source(
    metadata_path: Path,
    split_path: Path,
    video_root: Path,
    *,
    seed: int = 42,
    train_count: int = 20,
    validation_count: int = 10,
    buggy_probe_count: int = 1,
) -> dict[str, Any]:
    metadata = read_rows_by_source(metadata_path)
    split = read_rows_by_source(split_path)
    selections = {
        "train_normal": select_tempglitch_rows(
            metadata,
            split,
            partition="train",
            label_filter="Normal",
            max_episodes=train_count,
            seed=seed,
        ),
        "validation_normal": select_tempglitch_rows(
            metadata,
            split,
            partition="validation",
            label_filter="Normal",
            max_episodes=validation_count,
            seed=seed,
        ),
        "validation_buggy_probe": select_tempglitch_rows(
            metadata,
            split,
            partition="validation",
            label_filter="Buggy",
            max_episodes=buggy_probe_count,
            seed=seed,
        ),
    }
    required = {
        "train_normal": train_count,
        "validation_normal": validation_count,
        "validation_buggy_probe": buggy_probe_count,
    }
    missing_videos: list[str] = []
    for rows in selections.values():
        for row in rows:
            metadata_row = metadata[row["source"]]
            path = video_root / metadata_row["local_video_path"]
            if not path.is_file():
                missing_videos.append(str(path))
    if missing_videos:
        raise FileNotFoundError(f"Missing TempGlitch videos: {', '.join(missing_videos)}")
    insufficient = {
        name: {"required": required[name], "found": len(rows)}
        for name, rows in selections.items()
        if len(rows) < required[name]
    }
    if insufficient:
        raise ValueError(f"BLOCKED_NO_LOCAL_TEMPGLITCH_DATA: {insufficient}")

    train_sources = {row["source"] for row in selections["train_normal"]}
    validation_sources = {
        row["source"]
        for key in ("validation_normal", "validation_buggy_probe")
        for row in selections[key]
    }
    train_pairs = {row["pair_id"] for row in selections["train_normal"]}
    validation_pairs = {
        row["pair_id"]
        for key in ("validation_normal", "validation_buggy_probe")
        for row in selections[key]
    }
    source_overlap = sorted(train_sources & validation_sources)
    pair_overlap = sorted(train_pairs & validation_pairs)
    if source_overlap or pair_overlap:
        raise ValueError(
            f"Gate 6 train/validation leakage: sources={source_overlap}, pairs={pair_overlap}"
        )
    return {
        "status": "ready",
        "dataset": "TempGlitch",
        "metadata_path": str(metadata_path),
        "metadata_sha256": sha256_file(metadata_path),
        "split_path": str(split_path),
        "split_sha256": sha256_file(split_path),
        "video_root": str(video_root),
        "seed": seed,
        "counts": {name: len(rows) for name, rows in selections.items()},
        "selected_sources": {
            name: [row["source"] for row in rows] for name, rows in selections.items()
        },
        "source_overlap": source_overlap,
        "pair_overlap": pair_overlap,
        "action_mode": "zero_action",
        "normal_only_training": True,
        "normal_only_validation": True,
        "buggy_probe_use": "encoding_proof_only",
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def write_audit(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path
