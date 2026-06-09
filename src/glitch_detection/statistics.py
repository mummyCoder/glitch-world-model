from __future__ import annotations

import random
from collections import defaultdict
from statistics import mean
from typing import Any, Iterable

from .evaluate import auroc, binary_metrics


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _metric(rows: list[dict[str, Any]], metric_name: str, threshold: float | None) -> float | None:
    labels = [int(row["label"]) for row in rows]
    scores = [float(row["score"]) for row in rows]
    if metric_name == "auroc":
        return auroc(labels, scores)
    if metric_name == "f1":
        if threshold is None:
            raise ValueError("F1 bootstrap requires a fixed threshold.")
        predictions = [int(score >= threshold) for score in scores]
        return binary_metrics(labels, predictions)["f1"]
    raise ValueError("metric_name must be 'auroc' or 'f1'.")


def bootstrap_metric_ci(
    rows: Iterable[dict[str, Any]],
    metric_name: str,
    n_bootstrap: int = 1000,
    seed: int = 42,
    group_key: str = "source",
    confidence_level: float = 0.95,
    threshold: float | None = None,
) -> dict[str, Any]:
    source_rows = list(rows)
    if not source_rows:
        raise ValueError("Bootstrap requires at least one row.")
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be at least 1.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        if group_key not in row:
            raise KeyError(f"Missing bootstrap group key {group_key!r}.")
        groups[str(row[group_key])].append(row)

    group_ids = sorted(groups)
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(n_bootstrap):
        sampled_rows = [
            row for group_id in rng.choices(group_ids, k=len(group_ids)) for row in groups[group_id]
        ]
        value = _metric(sampled_rows, metric_name, threshold)
        if value is not None:
            values.append(float(value))

    alpha = (1.0 - confidence_level) / 2.0
    point = _metric(source_rows, metric_name, threshold)
    return {
        "metric_name": metric_name,
        "point": point,
        "lower": _percentile(values, alpha) if values else None,
        "mean": mean(values) if values else None,
        "upper": _percentile(values, 1.0 - alpha) if values else None,
        "n_bootstrap": n_bootstrap,
        "valid_bootstrap_count": len(values),
        "seed": seed,
        "group_key": group_key,
        "confidence_level": confidence_level,
    }
