from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ACTIVE_SPLITS = {"train", "validation", "test"}


@dataclass(frozen=True)
class FrozenSplitRecord:
    dataset_id: str
    source: str
    episode_id: str
    pair_id: str
    category: str
    label: str
    split: str
    action_mode: str
    use_for_training: bool
    materialize: bool


def _hash_fraction(seed: int, stratum: str, group_id: str) -> float:
    payload = f"{seed}\0{stratum}\0{group_id}".encode()
    return int(hashlib.sha256(payload).hexdigest(), 16) / float(2**256)


def _group_rows(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        category = row.get("category", "unknown")
        group_id = row.get("pair_id") or row["episode_id"]
        grouped[(category, group_id)].append(row)
    return grouped


def _stratified_assignments(
    group_ids: list[str],
    *,
    seed: int,
    stratum: str,
    validation_ratio: float,
    test_ratio: float,
    exposed_groups: set[str] | None = None,
) -> dict[str, str]:
    exposed = exposed_groups or set()
    ordered = sorted(group_ids, key=lambda group_id: _hash_fraction(seed, stratum, group_id))
    test_count = round(len(ordered) * test_ratio)
    validation_count = round(len(ordered) * validation_ratio)
    test_groups = set([group_id for group_id in ordered if group_id not in exposed][:test_count])
    remaining = [group_id for group_id in ordered if group_id not in test_groups]
    validation_groups = set(remaining[:validation_count])
    return {
        group_id: (
            "test"
            if group_id in test_groups
            else "validation"
            if group_id in validation_groups
            else "train"
        )
        for group_id in ordered
    }


def freeze_tempglitch_split(
    rows: list[dict[str, str]],
    *,
    exposed_groups: set[str] | None = None,
    seed: int = 42,
    validation_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> list[FrozenSplitRecord]:
    """Freeze TempGlitch groups while allowing only normal videos into training."""
    if validation_ratio <= 0 or test_ratio <= 0 or validation_ratio + test_ratio >= 1:
        raise ValueError("validation_ratio and test_ratio must be positive and sum to less than 1.")

    exposed = exposed_groups or set()
    grouped = _group_rows(rows)
    group_ids_by_category: dict[str, list[str]] = defaultdict(list)
    for category, pair_id in grouped:
        group_ids_by_category[category].append(pair_id)
    assignments = {
        (category, pair_id): split
        for category, pair_ids in group_ids_by_category.items()
        for pair_id, split in _stratified_assignments(
            pair_ids,
            seed=seed,
            stratum=category,
            validation_ratio=validation_ratio,
            test_ratio=test_ratio,
            exposed_groups=exposed,
        ).items()
    }

    records: list[FrozenSplitRecord] = []
    for (category, pair_id), group_rows in sorted(grouped.items()):
        group_split = assignments[(category, pair_id)]
        for row in group_rows:
            label = row["label"].strip()
            split = "excluded" if group_split == "train" and label != "Normal" else group_split
            records.append(
                FrozenSplitRecord(
                    dataset_id="asgaardlab/TempGlitch",
                    source=row["source"],
                    episode_id=row.get("episode_id", row["source"]),
                    pair_id=pair_id,
                    category=category,
                    label=label,
                    split=split,
                    action_mode="zero_action",
                    use_for_training=split == "train",
                    materialize=split in {"train", "validation"},
                )
            )
    _raise_on_invalid(records, exposed_groups=exposed)
    return sorted(records, key=lambda record: (record.category, record.pair_id, record.source))


def freeze_wob_split(
    normal_rows: list[dict[str, str]],
    bug_rows: list[dict[str, str]],
    *,
    seed: int = 42,
    normal_validation_ratio: float = 0.2,
    bug_test_ratio: float = 0.5,
) -> list[FrozenSplitRecord]:
    """Freeze WOB normal train/validation and bug validation/locked-test episodes."""
    if not 0 < normal_validation_ratio < 1 or not 0 < bug_test_ratio < 1:
        raise ValueError("WOB split ratios must be between zero and one.")

    normal_assignments = _stratified_assignments(
        [row["episode_id"] for row in normal_rows],
        seed=seed,
        stratum="Normal",
        validation_ratio=normal_validation_ratio,
        test_ratio=0,
    )
    records: list[FrozenSplitRecord] = []
    for row in normal_rows:
        episode_id = row["episode_id"]
        split = normal_assignments[episode_id]
        records.append(
            FrozenSplitRecord(
                dataset_id="benedictwilkinsai/world-of-bugs-normal",
                source=row["source"],
                episode_id=episode_id,
                pair_id=episode_id,
                category="Normal",
                label="Normal",
                split=split,
                action_mode="real",
                use_for_training=split == "train",
                materialize=True,
            )
        )
    bug_rows_by_category: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bug_rows:
        bug_rows_by_category[row["category"]].append(row)
    bug_assignments = {
        (category, episode_id): "validation" if split == "train" else split
        for category, category_rows in bug_rows_by_category.items()
        for episode_id, split in _stratified_assignments(
            [row["episode_id"] for row in category_rows],
            seed=seed,
            stratum=category,
            validation_ratio=1 - bug_test_ratio,
            test_ratio=bug_test_ratio,
        ).items()
    }
    for row in bug_rows:
        episode_id = row["episode_id"]
        category = row["category"]
        split = bug_assignments[(category, episode_id)]
        records.append(
            FrozenSplitRecord(
                dataset_id="benedictwilkinsai/world-of-bugs-test",
                source=row["source"],
                episode_id=episode_id,
                pair_id=episode_id,
                category=category,
                label="Buggy",
                split=split,
                action_mode="real",
                use_for_training=False,
                materialize=split == "validation",
            )
        )
    _raise_on_invalid(records)
    return sorted(
        records, key=lambda record: (record.dataset_id, record.category, record.episode_id)
    )


def audit_frozen_split(
    records: list[FrozenSplitRecord],
    *,
    exposed_groups: set[str] | None = None,
) -> dict[str, Any]:
    exposed = exposed_groups or set()
    active_group_splits: dict[str, set[str]] = defaultdict(set)
    split_counts: Counter[str] = Counter()
    category_split_counts: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    episodes: Counter[tuple[str, str]] = Counter()
    for record in records:
        split_counts[record.split] += 1
        category_split_counts[f"{record.category}/{record.split}"] += 1
        sources[record.source] += 1
        episodes[(record.dataset_id, record.episode_id)] += 1
        if record.split in ACTIVE_SPLITS:
            active_group_splits[record.pair_id].add(record.split)

    cross_split = sorted(
        group_id for group_id, splits in active_group_splits.items() if len(splits) > 1
    )
    exposed_test = sorted(
        {
            record.pair_id
            for record in records
            if record.pair_id in exposed and record.split == "test"
        }
    )
    duplicate_sources = sorted(source for source, count in sources.items() if count > 1)
    duplicate_episodes = sorted(
        f"{dataset_id}/{episode_id}"
        for (dataset_id, episode_id), count in episodes.items()
        if count > 1
    )
    non_normal_train = [
        record.source for record in records if record.split == "train" and record.label != "Normal"
    ]
    materialized_test = [
        record.source for record in records if record.split == "test" and record.materialize
    ]
    return {
        "record_count": len(records),
        "group_count": len(active_group_splits),
        "split_counts": dict(sorted(split_counts.items())),
        "category_split_counts": dict(sorted(category_split_counts.items())),
        "cross_split_group_count": len(cross_split),
        "cross_split_groups": cross_split,
        "exposed_test_group_count": len(exposed_test),
        "exposed_test_groups": exposed_test,
        "duplicate_source_count": len(duplicate_sources),
        "duplicate_sources": duplicate_sources,
        "duplicate_episode_count": len(duplicate_episodes),
        "duplicate_episodes": duplicate_episodes,
        "non_normal_train_count": len(non_normal_train),
        "non_normal_train_sources": sorted(non_normal_train),
        "materialized_test_count": len(materialized_test),
        "materialized_test_sources": sorted(materialized_test),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def _raise_on_invalid(
    records: list[FrozenSplitRecord],
    *,
    exposed_groups: set[str] | None = None,
) -> None:
    audit = audit_frozen_split(records, exposed_groups=exposed_groups)
    failures = [
        key
        for key in [
            "cross_split_group_count",
            "exposed_test_group_count",
            "duplicate_source_count",
            "duplicate_episode_count",
            "non_normal_train_count",
            "materialized_test_count",
        ]
        if audit[key]
    ]
    if failures:
        raise ValueError(f"Frozen split failed audit: {', '.join(failures)}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_frozen_split(
    path: Path,
    records: list[FrozenSplitRecord],
    *,
    seed: int,
    provenance: dict[str, Any],
    exposed_groups: set[str] | None = None,
) -> tuple[Path, Path, Path]:
    _raise_on_invalid(records, exposed_groups=exposed_groups)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(FrozenSplitRecord.__annotations__)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)

    split_sha256 = _sha256(path)
    audit_path = path.with_suffix(".audit.json")
    audit_path.write_text(
        json.dumps(
            {
                "seed": seed,
                "split_sha256": split_sha256,
                **audit_frozen_split(records, exposed_groups=exposed_groups),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    provenance_path = path.with_suffix(".provenance.json")
    provenance_path.write_text(
        json.dumps(
            {"seed": seed, "split_sha256": split_sha256, **provenance},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path, audit_path, provenance_path
