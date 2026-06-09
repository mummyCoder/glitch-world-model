from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from glitch_detection.model_selection import evaluate_locked_test
from glitch_detection.pairs import infer_tempglitch_pair_id
from glitch_detection.statistics import bootstrap_metric_ci
from glitch_detection.video_eval import write_json

ROOT = Path(__file__).resolve().parents[1]


def format_metric(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.6g}"


def read_video_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["label"] = int(row["label"])
        row["score"] = float(row["score"])
        row["pair_id_heuristic"] = (
            f"{row.get('category', 'unknown')}/{infer_tempglitch_pair_id(row['source'])}"
        )
    return rows


def write_locked_metrics_markdown(payload: dict[str, Any], output_path: Path) -> Path:
    metrics = payload["test_metrics"]
    lines = [
        "# TempGlitch Locked Test Result",
        "",
        f"- Selected on: `{payload['selection_split']}`",
        f"- Configuration: `{payload['scorer']}` / `{payload['aggregation']}`",
        f"- Fixed threshold: `{payload['threshold']:.6g}`",
        f"- Evaluated test configurations: `{payload['evaluated_config_count']}`",
        f"- Test AUROC: `{format_metric(metrics['auroc'])}`",
        f"- Test F1: `{format_metric(metrics['f1'])}`",
        "",
        "| Metric | Point | 95% lower | 95% upper | Valid bootstrap / requested | Group |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for metric_name, ci in payload["confidence_intervals"].items():
        lines.append(
            f"| {metric_name} | {format_metric(ci['point'])} | {format_metric(ci['lower'])} | "
            f"{format_metric(ci['upper'])} | "
            f"{ci['valid_bootstrap_count']} / {ci['n_bootstrap']} | {ci['group_key']} |"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate exactly one validation-selected config.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase3b_video_level",
    )
    parser.add_argument("--selected-config", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-markdown", type=Path, default=None)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--group-key",
        choices=["source", "pair_id_heuristic"],
        default="pair_id_heuristic",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    selected_path = args.selected_config or args.input_dir / "selected_protocol_config.json"
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    scorer = str(selected["scorer"])
    aggregation = str(selected["aggregation"])
    test_rows_path = args.input_dir / f"{scorer}_{aggregation}_test_video_scores.csv"
    test_rows = read_video_rows(test_rows_path)
    result = evaluate_locked_test(selected, {(scorer, aggregation): test_rows})
    threshold = float(selected["threshold"])
    result["confidence_intervals"] = {
        "auroc": bootstrap_metric_ci(
            test_rows,
            "auroc",
            n_bootstrap=args.n_bootstrap,
            seed=args.seed,
            group_key=args.group_key,
        ),
        "f1": bootstrap_metric_ci(
            test_rows,
            "f1",
            n_bootstrap=args.n_bootstrap,
            seed=args.seed,
            group_key=args.group_key,
            threshold=threshold,
        ),
    }
    result["test_rows_path"] = str(test_rows_path)
    output_json = args.output_json or args.input_dir / "final_test_metrics_with_ci.json"
    output_markdown = args.output_markdown or args.input_dir / "final_test_metrics_with_ci.md"
    write_json(result, output_json)
    write_locked_metrics_markdown(result, output_markdown)
    print(f"Locked test config: {scorer}/{aggregation}")
    print(f"Evaluated configurations: {result['evaluated_config_count']}")
    print(f"Metrics with CI: {output_json}")
    print(f"Markdown report: {output_markdown}")


if __name__ == "__main__":
    main()
