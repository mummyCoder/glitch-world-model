from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from .evaluate import auroc, binary_metrics, read_scores
from .manifest import clip_has_glitch, read_labels
from .splits import read_split_csv


def _split_metadata(split_csv: Path | None) -> dict[str, dict[str, str]]:
    if split_csv is None:
        return {}
    return {
        record.source: {
            "category": record.category,
            "source_label": record.label,
            "split": record.split,
        }
        for record in read_split_csv(split_csv)
    }


def load_scores_with_labels(
    scores_path: Path,
    labels_path: Path,
    split_csv: Path | None = None,
) -> list[dict[str, Any]]:
    intervals = read_labels(labels_path)
    metadata = _split_metadata(split_csv)
    rows: list[dict[str, Any]] = []
    for row in read_scores(scores_path):
        label = int(
            clip_has_glitch(
                source=row["source"],
                start_frame=int(row["start_frame"]),
                end_frame=int(row["end_frame"]),
                labels=intervals,
            )
        )
        enriched: dict[str, Any] = {
            "clip_id": row["clip_id"],
            "source": row["source"],
            "clip_dir": row["clip_dir"],
            "start_frame": int(row["start_frame"]),
            "end_frame": int(row["end_frame"]),
            "score": float(row["score"]),
            "label": label,
        }
        enriched.update(metadata.get(row["source"], {}))
        rows.append(enriched)
    return rows


def prediction_rows(
    scores_path: Path,
    labels_path: Path,
    threshold: float,
    split_csv: Path | None = None,
) -> list[dict[str, Any]]:
    rows = load_scores_with_labels(scores_path, labels_path, split_csv)
    for row in rows:
        prediction = int(row["score"] >= threshold)
        row["prediction"] = prediction
        if row["label"] == 1 and prediction == 1:
            row["outcome"] = "tp"
        elif row["label"] == 0 and prediction == 1:
            row["outcome"] = "fp"
        elif row["label"] == 1 and prediction == 0:
            row["outcome"] = "fn"
        else:
            row["outcome"] = "tn"
    return rows


def _group_rows(rows: list[dict[str, Any]], group_key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_key, "unknown"))].append(row)
    return dict(grouped)


def binary_metrics_by_group(
    rows: list[dict[str, Any]],
    group_key: str,
) -> dict[str, dict[str, Any]]:
    grouped = _group_rows(rows, group_key)
    result: dict[str, dict[str, Any]] = {}
    for group, group_rows in grouped.items():
        labels = [int(row["label"]) for row in group_rows]
        predictions = [int(row["prediction"]) for row in group_rows]
        scores = [float(row["score"]) for row in group_rows]
        metrics: dict[str, Any] = binary_metrics(labels, predictions)
        metrics["auroc"] = auroc(labels, scores)
        metrics["clip_count"] = len(group_rows)
        metrics["positive_clip_count"] = sum(labels)
        result[group] = metrics
    return dict(sorted(result.items()))


def top_errors(rows: list[dict[str, Any]], kind: str, limit: int) -> list[dict[str, Any]]:
    if kind == "false_positive":
        matches = [row for row in rows if row["outcome"] == "fp"]
        return sorted(matches, key=lambda row: float(row["score"]), reverse=True)[:limit]
    if kind == "false_negative":
        matches = [row for row in rows if row["outcome"] == "fn"]
        return sorted(matches, key=lambda row: float(row["score"]))[:limit]
    raise ValueError(f"Unknown error kind: {kind}")


def _percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return 0.0
    index = round((len(sorted_values) - 1) * fraction)
    return sorted_values[index]


def score_distribution_summary(
    rows: list[dict[str, Any]],
    group_key: str,
) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for group, group_rows in _group_rows(rows, group_key).items():
        scores = sorted(float(row["score"]) for row in group_rows)
        result[group] = {
            "count": len(scores),
            "min": min(scores) if scores else 0.0,
            "max": max(scores) if scores else 0.0,
            "mean": mean(scores) if scores else 0.0,
            "median": median(scores) if scores else 0.0,
            "p25": _percentile(scores, 0.25),
            "p75": _percentile(scores, 0.75),
        }
    return dict(sorted(result.items()))


def write_json(payload: Any, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def write_rows_csv(rows: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "clip_id",
        "source",
        "category",
        "split",
        "start_frame",
        "end_frame",
        "score",
        "label",
        "prediction",
        "outcome",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def write_markdown_table(
    rows_by_key: dict[str, dict[str, Any]],
    output_path: Path,
    title: str,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metric_keys = sorted({key for row in rows_by_key.values() for key in row})
    lines = [
        f"# {title}",
        "",
        "| Group | " + " | ".join(metric_keys) + " |",
        "| --- | " + " | ".join("---:" for _ in metric_keys) + " |",
    ]
    for group, row in rows_by_key.items():
        values = [row.get(key) for key in metric_keys]
        lines.append(
            "| " + " | ".join([group] + [_format_markdown_value(value) for value in values]) + " |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _format_markdown_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)
