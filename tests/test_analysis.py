import csv
import json
from pathlib import Path

from glitch_detection.analysis import (
    binary_metrics_by_group,
    load_scores_with_labels,
    prediction_rows,
    score_distribution_summary,
    top_errors,
    write_json,
    write_markdown_table,
)


def _write_scores(path: Path) -> None:
    path.write_text(
        "clip_id,source,clip_dir,start_frame,end_frame,score\n"
        "buggy_easy_0,buggy_easy,buggy_easy/0,0,3,0.9\n"
        "buggy_hard_0,buggy_hard,buggy_hard/0,0,3,0.1\n"
        "normal_easy_0,normal_easy,normal_easy/0,0,3,0.2\n"
        "normal_hard_0,normal_hard,normal_hard/0,0,3,0.8\n",
        encoding="utf-8",
    )


def _write_labels(path: Path) -> None:
    path.write_text(
        "source,start_frame,end_frame,label\nbuggy_easy,0,3,1\nbuggy_hard,0,3,1\n",
        encoding="utf-8",
    )


def _write_split(path: Path) -> None:
    path.write_text(
        "source,category,label,split\n"
        "buggy_easy,Blinking,Buggy,test\n"
        "buggy_hard,Frozen Animation,Buggy,test\n"
        "normal_easy,Blinking,Normal,test\n"
        "normal_hard,Frozen Animation,Normal,test\n",
        encoding="utf-8",
    )


def test_load_scores_with_labels_adds_labels_and_split_metadata(tmp_path: Path):
    scores_path = tmp_path / "scores.csv"
    labels_path = tmp_path / "labels.csv"
    split_path = tmp_path / "split.csv"
    _write_scores(scores_path)
    _write_labels(labels_path)
    _write_split(split_path)

    rows = load_scores_with_labels(scores_path, labels_path, split_path)

    assert rows[0]["category"] == "Blinking"
    assert rows[0]["split"] == "test"
    assert [row["label"] for row in rows] == [1, 1, 0, 0]


def test_prediction_rows_and_top_errors(tmp_path: Path):
    scores_path = tmp_path / "scores.csv"
    labels_path = tmp_path / "labels.csv"
    split_path = tmp_path / "split.csv"
    _write_scores(scores_path)
    _write_labels(labels_path)
    _write_split(split_path)

    rows = prediction_rows(scores_path, labels_path, threshold=0.5, split_csv=split_path)

    assert [row["outcome"] for row in rows] == ["tp", "fn", "tn", "fp"]
    assert top_errors(rows, "false_positive", 1)[0]["source"] == "normal_hard"
    assert top_errors(rows, "false_negative", 1)[0]["source"] == "buggy_hard"


def test_binary_metrics_by_group_handles_missing_auroc(tmp_path: Path):
    scores_path = tmp_path / "scores.csv"
    labels_path = tmp_path / "labels.csv"
    split_path = tmp_path / "split.csv"
    _write_scores(scores_path)
    _write_labels(labels_path)
    _write_split(split_path)
    rows = prediction_rows(scores_path, labels_path, threshold=0.5, split_csv=split_path)

    metrics = binary_metrics_by_group(rows, "category")

    assert metrics["Blinking"]["auroc"] == 1.0
    assert metrics["Frozen Animation"]["f1"] == 0.0
    all_positive = binary_metrics_by_group([row for row in rows if row["label"] == 1], "split")
    assert all_positive["test"]["auroc"] is None


def test_score_distribution_and_writers(tmp_path: Path):
    scores_path = tmp_path / "scores.csv"
    labels_path = tmp_path / "labels.csv"
    split_path = tmp_path / "split.csv"
    _write_scores(scores_path)
    _write_labels(labels_path)
    _write_split(split_path)
    rows = load_scores_with_labels(scores_path, labels_path, split_path)

    summary = score_distribution_summary(rows, "category")
    assert summary["Blinking"]["median"] == 0.55

    json_path = write_json(summary, tmp_path / "summary.json")
    md_path = write_markdown_table(summary, tmp_path / "summary.md", title="Summary")
    assert json.loads(json_path.read_text(encoding="utf-8"))["Blinking"]["count"] == 2
    with md_path.open("r", newline="", encoding="utf-8") as handle:
        lines = list(csv.reader(handle))
    assert lines[0][0] == "# Summary"
