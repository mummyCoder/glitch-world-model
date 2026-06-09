from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

PAIR_INDEX_PATTERN = re.compile(r"_(\d+)$")


def _row_value(row: Any, key: str, default: str = "") -> str:
    if isinstance(row, dict):
        return str(row.get(key, default))
    return str(getattr(row, key, default))


def infer_tempglitch_pair_id(source: str) -> str:
    """Return a conservative suspected pair ID, not an official TempGlitch ID."""
    stem = Path(source).stem
    match = PAIR_INDEX_PATTERN.search(stem)
    if match:
        return f"pair-index:{int(match.group(1))}"
    return f"source:{stem}"


def group_sources_by_pair(metadata_rows: Iterable[Any]) -> dict[str, list[str]]:
    groups: dict[str, set[str]] = defaultdict(set)
    for row in metadata_rows:
        source = _row_value(row, "source")
        category = _row_value(row, "category", "unknown")
        groups[f"{category}/{infer_tempglitch_pair_id(source)}"].add(source)
    return {key: sorted(sources) for key, sources in sorted(groups.items())}


def pair_leakage_report(split_rows: Iterable[Any]) -> dict[str, Any]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for row in split_rows:
        source = _row_value(row, "source")
        category = _row_value(row, "category", "unknown")
        pair_id = _row_value(row, "pair_id_heuristic")
        if not pair_id:
            pair_id = f"{category}/{infer_tempglitch_pair_id(source)}"
        grouped[pair_id].append(row)

    cross_split_pairs: list[dict[str, Any]] = []
    suspected_pair_count = 0
    for pair_id, rows in sorted(grouped.items()):
        sources = sorted({_row_value(row, "source") for row in rows})
        if len(sources) > 1:
            suspected_pair_count += 1
        splits = sorted({_row_value(row, "split") for row in rows})
        if len(splits) > 1:
            cross_split_pairs.append(
                {
                    "pair_id_heuristic": pair_id,
                    "splits": splits,
                    "sources": sources,
                }
            )
    return {
        "grouping_mode": "pair_id_heuristic",
        "group_count": len(grouped),
        "suspected_pair_count": suspected_pair_count,
        "cross_split_pair_count": len(cross_split_pairs),
        "cross_split_pairs": cross_split_pairs,
    }
