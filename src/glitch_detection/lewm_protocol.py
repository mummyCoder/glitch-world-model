from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class LeWMSplitRecord:
    dataset_id: str
    source: str
    episode_id: str
    category: str
    label: str
    split: str
    pair_id: str
    action_mode: str


def _hash_fraction(seed: int, stratum: str, group_id: str) -> float:
    payload = f"{seed}\0{stratum}\0{group_id}".encode()
    return int(hashlib.sha256(payload).hexdigest(), 16) / float(2**256)


def assign_hashed_group_splits(
    rows: list[dict[str, str]],
    *,
    dataset_id: str,
    seed: int = 42,
    validation_ratio: float = 0.2,
    test_ratio: float = 0.2,
    exposed_groups: set[str] | None = None,
) -> list[LeWMSplitRecord]:
    if validation_ratio <= 0 or test_ratio <= 0 or validation_ratio + test_ratio >= 1:
        raise ValueError("validation_ratio and test_ratio must be positive and sum to less than 1.")

    exposed = exposed_groups or set()
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        group_id = row.get("pair_id") or row["episode_id"]
        stratum = row.get("category", "unknown")
        grouped[(stratum, group_id)].append(row)

    records: list[LeWMSplitRecord] = []
    for (stratum, group_id), group_rows in sorted(grouped.items()):
        fraction = _hash_fraction(seed, stratum, group_id)
        if group_id in exposed:
            split = "validation" if fraction < 0.5 else "train"
        elif fraction < test_ratio:
            split = "test"
        elif fraction < test_ratio + validation_ratio:
            split = "validation"
        else:
            split = "train"
        for row in group_rows:
            records.append(
                LeWMSplitRecord(
                    dataset_id=dataset_id,
                    source=row["source"],
                    episode_id=row["episode_id"],
                    category=stratum,
                    label=row.get("label", "unknown"),
                    split=split,
                    pair_id=group_id,
                    action_mode=row["action_mode"],
                )
            )
    audit = audit_lewm_splits(records, exposed_groups=exposed)
    if audit["cross_split_group_count"]:
        raise ValueError("LeWM split assignment produced cross-split groups.")
    if audit["exposed_test_group_count"]:
        raise ValueError("Previously exposed groups cannot enter locked test.")
    return sorted(records, key=lambda record: (record.dataset_id, record.source, record.episode_id))


def audit_lewm_splits(
    records: list[LeWMSplitRecord],
    *,
    exposed_groups: set[str] | None = None,
) -> dict[str, Any]:
    exposed = exposed_groups or set()
    groups: dict[str, set[str]] = defaultdict(set)
    split_counts: dict[str, int] = {split: 0 for split in SPLITS}
    for record in records:
        groups[record.pair_id].add(record.split)
        split_counts[record.split] = split_counts.get(record.split, 0) + 1
    cross_split = sorted(group_id for group_id, splits in groups.items() if len(splits) > 1)
    exposed_test = sorted(
        record.pair_id for record in records if record.pair_id in exposed and record.split == "test"
    )
    return {
        "record_count": len(records),
        "group_count": len(groups),
        "split_counts": split_counts,
        "cross_split_group_count": len(cross_split),
        "cross_split_groups": cross_split,
        "exposed_test_group_count": len(set(exposed_test)),
        "exposed_test_groups": sorted(set(exposed_test)),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def write_lewm_split(
    path: Path,
    records: list[LeWMSplitRecord],
    *,
    seed: int,
    exposed_groups: set[str] | None = None,
) -> tuple[Path, Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(records[0]).keys()) if records else list(LeWMSplitRecord.__annotations__)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    audit = {"seed": seed, **audit_lewm_splits(records, exposed_groups=exposed_groups)}
    audit_path = path.with_suffix(".audit.json")
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return path, audit_path
