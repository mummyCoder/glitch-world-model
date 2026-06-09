from __future__ import annotations

from typing import Any, Iterable, Mapping

from .video_eval import compute_video_level_metrics


def select_validation_config(
    candidates: Iterable[dict[str, Any]],
    selection_metric: str = "auroc",
    seed: int = 42,
) -> dict[str, Any]:
    rows = list(candidates)
    if not rows:
        raise ValueError("At least one validation candidate is required.")
    if selection_metric not in {"auroc", "f1"}:
        raise ValueError("selection_metric must be 'auroc' or 'f1'.")

    usable = [
        row for row in rows if row.get("validation_metrics", {}).get(selection_metric) is not None
    ]
    actual_metric = selection_metric
    if not usable and selection_metric == "auroc":
        actual_metric = "f1"
        usable = [row for row in rows if row.get("validation_metrics", {}).get("f1") is not None]
    if not usable:
        raise ValueError("No candidate has a usable validation selection metric.")

    selected = sorted(
        usable,
        key=lambda row: (
            -float(row["validation_metrics"][actual_metric]),
            str(row["scorer"]),
            str(row["aggregation"]),
        ),
    )[0]
    return {
        "scorer": str(selected["scorer"]),
        "aggregation": str(selected["aggregation"]),
        "threshold": float(selected["threshold"]),
        "selection_split": "validation",
        "selection_metric": actual_metric,
        "selection_value": float(selected["validation_metrics"][actual_metric]),
        "validation_metrics": dict(selected["validation_metrics"]),
        "seed": seed,
    }


def evaluate_locked_test(
    selected_config: Mapping[str, Any],
    rows_by_config: Mapping[tuple[str, str], Iterable[dict[str, Any]]],
) -> dict[str, Any]:
    scorer = str(selected_config["scorer"])
    aggregation = str(selected_config["aggregation"])
    key = (scorer, aggregation)
    if key not in rows_by_config:
        raise KeyError(f"Missing locked test rows for {scorer}/{aggregation}.")
    rows = list(rows_by_config[key])
    threshold = float(selected_config["threshold"])
    return {
        "scorer": scorer,
        "aggregation": aggregation,
        "threshold": threshold,
        "selection_split": selected_config.get("selection_split", "validation"),
        "evaluated_config_count": 1,
        "test_metrics": compute_video_level_metrics(rows, threshold),
    }
