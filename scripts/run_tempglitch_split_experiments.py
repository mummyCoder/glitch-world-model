from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from glitch_detection import feature_distance, frame_diff, mini_latent
from glitch_detection.analysis import (
    binary_metrics_by_group,
    prediction_rows,
    score_distribution_summary,
    top_errors,
    write_json,
    write_markdown_table,
    write_rows_csv,
)
from glitch_detection.calibration import calibrate_threshold, evaluate_with_fixed_threshold
from glitch_detection.manifest import ClipRecord, clip_has_glitch, read_labels, read_manifest
from glitch_detection.preprocess import extract_video_frames, preprocess_frames
from glitch_detection.splits import (
    SplitRecord,
    assign_grouped_video_splits,
    assign_video_splits,
    filter_labels_by_sources,
    filter_manifest_by_sources,
    read_split_csv,
    sources_for_split,
    split_counts_by_group,
    write_grouped_split_csv,
    write_split_csv,
)
from glitch_detection.tempglitch import (
    DATASET_PAGE_URL,
    DEFAULT_CATEGORIES,
    combine_manifests,
    download_tempglitch_subset,
    read_tempglitch_metadata,
    write_tempglitch_full_video_labels,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCORERS = ["frame_diff", "feature_distance", "mini_latent"]


def write_scores_csv(
    records: list[ClipRecord], scores: dict[str, float], output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "source": record.source,
                    "clip_dir": record.clip_dir,
                    "start_frame": record.start_frame,
                    "end_frame": record.end_frame,
                    "score": f"{scores[record.clip_id]:.8f}",
                }
            )
    return output_path


def preprocess_tempglitch_videos(
    raw_dir: Path,
    processed_dir: Path,
    metadata_path: Path,
    clip_length: int,
    stride: int,
    size: int,
) -> Path:
    manifest_paths: list[Path] = []
    for row in read_tempglitch_metadata(metadata_path):
        source = row["source"]
        video_path = raw_dir / Path(row["local_video_path"])
        source_dir = processed_dir / source
        frames_dir, fps = extract_video_frames(
            video_path, source_dir / "frames" / source, size=size
        )
        manifest_paths.append(
            preprocess_frames(
                input_path=frames_dir,
                output_dir=source_dir,
                clip_length=clip_length,
                stride=stride,
                size=size,
                fps=fps,
            )
        )
    return combine_manifests(manifest_paths, processed_dir / "manifest.csv")


def normal_train_records(manifest_path: Path, split_records: list[SplitRecord]) -> list[ClipRecord]:
    normal_sources = {
        record.source
        for record in split_records
        if record.split == "train" and record.label == "Normal"
    }
    return [record for record in read_manifest(manifest_path) if record.source in normal_sources]


def score_validation_and_test(
    scorer_name: str,
    train_manifest_path: Path,
    validation_manifest_path: Path,
    test_manifest_path: Path,
    split_records: list[SplitRecord],
    outputs_dir: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    validation_scores_path = outputs_dir / f"{scorer_name}_val_scores.csv"
    test_scores_path = outputs_dir / f"{scorer_name}_test_scores.csv"
    validation_records = read_manifest(validation_manifest_path)
    test_records = read_manifest(test_manifest_path)

    fit_metadata: dict[str, Any] = {"fit_split": "none", "fit_normal_clip_count": 0}
    if scorer_name == "frame_diff":
        frame_diff.score_manifest(validation_manifest_path, validation_scores_path)
        frame_diff.score_manifest(test_manifest_path, test_scores_path)
    elif scorer_name == "feature_distance":
        train_records = normal_train_records(train_manifest_path, split_records)
        centroid = feature_distance.fit_centroid(train_records)
        write_scores_csv(
            validation_records,
            feature_distance.score_records_with_centroid(validation_records, centroid),
            validation_scores_path,
        )
        write_scores_csv(
            test_records,
            feature_distance.score_records_with_centroid(test_records, centroid),
            test_scores_path,
        )
        fit_metadata = {"fit_split": "train", "fit_normal_clip_count": len(train_records)}
    elif scorer_name == "mini_latent":
        train_records = normal_train_records(train_manifest_path, split_records)
        model = mini_latent.fit_model(train_records)
        write_scores_csv(
            validation_records,
            mini_latent.score_records_with_model(validation_records, model),
            validation_scores_path,
        )
        write_scores_csv(
            test_records,
            mini_latent.score_records_with_model(test_records, model),
            test_scores_path,
        )
        fit_metadata = {"fit_split": "train", "fit_normal_clip_count": len(train_records)}
    else:
        raise ValueError(f"Unsupported split-aware scorer: {scorer_name}")

    return validation_scores_path, test_scores_path, fit_metadata


def write_comparison(results: list[dict[str, Any]], output_path: Path) -> Path:
    lines = [
        "# TempGlitch Split Experiment Comparison",
        "",
        "| Scorer | Val threshold | Test precision | Test recall | Test F1 | Test AUROC |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            f"| {result['scorer']} | {result['validation_threshold']:.6g} | "
            f"{result['test_metrics']['precision']:.6g} | "
            f"{result['test_metrics']['recall']:.6g} | "
            f"{result['test_metrics']['f1']:.6g} | "
            f"{result['test_metrics']['auroc']:.6g} |"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def best_and_worst_categories(category_metrics: dict[str, dict[str, Any]]) -> tuple[str, str]:
    def ranking_value(item: tuple[str, dict[str, Any]]) -> tuple[float, float]:
        metrics = item[1]
        auroc = metrics.get("auroc")
        return (float(auroc) if auroc is not None else -1.0, float(metrics.get("f1", 0.0)))

    ranked = sorted(category_metrics.items(), key=ranking_value, reverse=True)
    if not ranked:
        return "n/a", "n/a"
    return ranked[0][0], ranked[-1][0]


def positive_clip_counts(
    manifest_path: Path,
    labels_path: Path,
    split_records: list[SplitRecord],
) -> dict[str, int]:
    labels = read_labels(labels_path)
    records = read_manifest(manifest_path)
    return {
        split: sum(
            int(clip_has_glitch(record.source, record.start_frame, record.end_frame, labels))
            for record in records
            if record.source in sources_for_split(split_records, split)
        )
        for split in ["train", "validation", "test"]
    }


def clip_counts_by_split(manifest_path: Path, split_records: list[SplitRecord]) -> dict[str, int]:
    records = read_manifest(manifest_path)
    return {
        split: sum(
            1 for record in records if record.source in sources_for_split(split_records, split)
        )
        for split in ["train", "validation", "test"]
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run leakage-aware TempGlitch split experiments.")
    parser.add_argument("--experiment-name", default="tempglitch_phase3b")
    parser.add_argument("--raw-dir", type=Path, default=None)
    parser.add_argument("--processed-dir", type=Path, default=None)
    parser.add_argument("--outputs-dir", type=Path, default=None)
    parser.add_argument("--categories", nargs="+", default=list(DEFAULT_CATEGORIES))
    parser.add_argument("--limit-per-group", type=int, default=10)
    parser.add_argument("--clip-length", type=int, default=16)
    parser.add_argument("--stride", type=int, default=16)
    parser.add_argument("--size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--sample-mode",
        choices=["sequential", "random-stratified"],
        default="random-stratified",
    )
    parser.add_argument(
        "--grouping-mode",
        choices=["source", "pair_id_heuristic"],
        default="pair_id_heuristic",
    )
    parser.add_argument("--train-ratio", type=float, default=0.6)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--train-count", type=int, default=None)
    parser.add_argument("--validation-count", type=int, default=None)
    parser.add_argument("--test-count", type=int, default=None)
    parser.add_argument("--scorer", action="append", dest="scorers", default=None)
    parser.add_argument("--analysis", action="store_true", default=True)
    parser.add_argument("--no-analysis", action="store_false", dest="analysis")
    parser.add_argument("--top-errors", type=int, default=20)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.raw_dir = args.raw_dir or ROOT / "data" / "raw" / args.experiment_name
    args.processed_dir = args.processed_dir or ROOT / "data" / "processed" / args.experiment_name
    args.outputs_dir = args.outputs_dir or ROOT / "outputs" / args.experiment_name
    scorers = args.scorers or list(DEFAULT_SCORERS)
    if args.limit_per_group < 3:
        raise SystemExit(
            "Leakage-aware validation calibration requires at least 3 videos per category/label."
        )
    if args.grouping_mode == "pair_id_heuristic" and any(
        count is not None for count in [args.train_count, args.validation_count, args.test_count]
    ):
        raise SystemExit(
            "Explicit per-label split counts are incompatible with whole pair-suspect groups. "
            "Use split ratios or --grouping-mode source."
        )

    samples, metadata_path, _ = download_tempglitch_subset(
        output_dir=args.raw_dir,
        categories=args.categories,
        limit_per_group=args.limit_per_group,
        sample_mode=args.sample_mode,
        seed=args.seed,
    )
    manifest_path = preprocess_tempglitch_videos(
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
        metadata_path=metadata_path,
        clip_length=args.clip_length,
        stride=args.stride,
        size=args.size,
    )
    labels_path = write_tempglitch_full_video_labels(
        metadata_path=metadata_path,
        manifest_path=manifest_path,
        output_path=args.processed_dir / "labels.csv",
    )
    if args.grouping_mode == "pair_id_heuristic":
        split_path, _ = write_grouped_split_csv(
            args.processed_dir / "split.csv",
            assign_grouped_video_splits(
                read_tempglitch_metadata(metadata_path),
                seed=args.seed,
                train_ratio=args.train_ratio,
                validation_ratio=args.validation_ratio,
                test_ratio=args.test_ratio,
            ),
            seed=args.seed,
        )
    else:
        split_path = write_split_csv(
            args.processed_dir / "split.csv",
            assign_video_splits(
                read_tempglitch_metadata(metadata_path),
                seed=args.seed,
                train_count=args.train_count,
                validation_count=args.validation_count,
                test_count=args.test_count,
                train_ratio=args.train_ratio,
                validation_ratio=args.validation_ratio,
                test_ratio=args.test_ratio,
            ),
        )
    split_records = read_split_csv(split_path)

    split_manifest_paths: dict[str, Path] = {}
    split_label_paths: dict[str, Path] = {}
    for split in ["train", "validation", "test"]:
        sources = sources_for_split(split_records, split)
        split_manifest_paths[split] = filter_manifest_by_sources(
            manifest_path,
            sources,
            args.processed_dir / f"{split}_manifest.csv",
        )
        split_label_paths[split] = filter_labels_by_sources(
            labels_path,
            sources,
            args.processed_dir / f"{split}_labels.csv",
        )

    results: list[dict[str, Any]] = []
    for scorer_name in scorers:
        validation_scores_path, test_scores_path, fit_metadata = score_validation_and_test(
            scorer_name=scorer_name,
            train_manifest_path=split_manifest_paths["train"],
            validation_manifest_path=split_manifest_paths["validation"],
            test_manifest_path=split_manifest_paths["test"],
            split_records=split_records,
            outputs_dir=args.outputs_dir,
        )
        calibration_path = args.outputs_dir / f"{scorer_name}_calibration.json"
        calibration = calibrate_threshold(
            validation_scores_path,
            split_label_paths["validation"],
            calibration_path,
        )
        test_metrics_path = args.outputs_dir / f"{scorer_name}_test_metrics.json"
        test_metrics = evaluate_with_fixed_threshold(
            test_scores_path,
            split_label_paths["test"],
            calibration_path,
            test_metrics_path,
        )
        analysis_payload: dict[str, Any] = {}
        if args.analysis:
            rows = prediction_rows(
                test_scores_path,
                split_label_paths["test"],
                threshold=float(calibration["threshold"]),
                split_csv=split_path,
            )
            category_metrics = binary_metrics_by_group(rows, "category")
            source_metrics = binary_metrics_by_group(rows, "source")
            distribution = score_distribution_summary(rows, "category")
            false_positives = top_errors(rows, "false_positive", args.top_errors)
            false_negatives = top_errors(rows, "false_negative", args.top_errors)
            best_category, worst_category = best_and_worst_categories(category_metrics)
            write_rows_csv(rows, args.outputs_dir / f"{scorer_name}_test_predictions.csv")
            write_json(category_metrics, args.outputs_dir / f"{scorer_name}_category_metrics.json")
            write_markdown_table(
                category_metrics,
                args.outputs_dir / f"{scorer_name}_category_metrics.md",
                title=f"{scorer_name} Category Metrics",
            )
            write_json(source_metrics, args.outputs_dir / f"{scorer_name}_source_metrics.json")
            write_rows_csv(false_positives, args.outputs_dir / f"{scorer_name}_false_positives.csv")
            write_rows_csv(false_negatives, args.outputs_dir / f"{scorer_name}_false_negatives.csv")
            write_json(distribution, args.outputs_dir / f"{scorer_name}_score_distribution.json")
            analysis_payload = {
                "category_metrics_path": str(
                    args.outputs_dir / f"{scorer_name}_category_metrics.json"
                ),
                "source_metrics_path": str(args.outputs_dir / f"{scorer_name}_source_metrics.json"),
                "false_positives_path": str(
                    args.outputs_dir / f"{scorer_name}_false_positives.csv"
                ),
                "false_negatives_path": str(
                    args.outputs_dir / f"{scorer_name}_false_negatives.csv"
                ),
                "score_distribution_path": str(
                    args.outputs_dir / f"{scorer_name}_score_distribution.json"
                ),
                "best_category": best_category,
                "worst_category": worst_category,
                "category_metrics": category_metrics,
            }
        results.append(
            {
                "scorer": scorer_name,
                "validation_threshold": calibration["threshold"],
                "calibration_path": str(calibration_path),
                "test_metrics_path": str(test_metrics_path),
                "fit": fit_metadata,
                "test_metrics": test_metrics,
                "analysis": analysis_payload,
            }
        )

    split_counts = Counter(record.split for record in split_records)
    clip_counts = clip_counts_by_split(manifest_path, split_records)
    positives = positive_clip_counts(manifest_path, labels_path, split_records)
    negatives = {split: clip_counts[split] - positives[split] for split in clip_counts}
    split_summary = {
        "split_counts": dict(split_counts),
        "group_split_counts": split_counts_by_group(split_records),
        "clip_counts": clip_counts,
        "positive_clip_counts": positives,
        "negative_clip_counts": negatives,
    }
    write_json(split_summary, args.outputs_dir / "split_summary.json")
    summary = {
        "experiment_name": args.experiment_name,
        "dataset_url": DATASET_PAGE_URL,
        "dataset_revision": samples[0].dataset_revision if samples else None,
        "categories": args.categories,
        "limit_per_group": args.limit_per_group,
        "video_count": len(samples),
        "clip_count": len(read_manifest(manifest_path)),
        "split_counts": dict(split_counts),
        "group_split_counts": split_counts_by_group(split_records),
        "positive_clip_counts": positives,
        "negative_clip_counts": negatives,
        "clip_length": args.clip_length,
        "stride": args.stride,
        "size": args.size,
        "seed": args.seed,
        "sample_mode": args.sample_mode,
        "grouping_mode": args.grouping_mode,
        "label_limitation": "binary per-video labels; no temporal span claims",
        "results": results,
    }
    args.outputs_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.outputs_dir / "phase3b_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    comparison_path = write_comparison(results, args.outputs_dir / "phase3b_comparison.md")

    print(f"Dataset revision: {summary['dataset_revision']}")
    print(f"Videos: {summary['video_count']}")
    print(f"Clips: {summary['clip_count']}")
    print(f"Split counts: {summary['split_counts']}")
    print(f"Group split counts: {summary['group_split_counts']}")
    print(f"Positive clips by split: {summary['positive_clip_counts']}")
    print(f"Negative clips by split: {summary['negative_clip_counts']}")
    for result in results:
        metrics = result["test_metrics"]
        analysis = result.get("analysis", {})
        print(
            f"{result['scorer']}: validation threshold={result['validation_threshold']:.6g}, "
            f"test AUROC={metrics['auroc']:.3f}, F1={metrics['f1']:.3f}, "
            f"precision={metrics['precision']:.3f}, recall={metrics['recall']:.3f}"
        )
        if analysis:
            print(
                f"{result['scorer']}: best category={analysis['best_category']}, "
                f"worst category={analysis['worst_category']}"
            )
    print(f"Comparison: {comparison_path}")
    print(f"Summary: {summary_path}")
    print("Warning: binary per-video labels only; no temporal span claims.")


if __name__ == "__main__":
    main()
