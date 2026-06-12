from __future__ import annotations

import subprocess
import sys

import pytest

from scripts.run_gate9_ablations import (
    aggregate_lewm_rows,
    evaluate_gate9_rows,
    validate_gate9_alignment,
)


def _manifest(window_id: str, label: str, role: str, episode: str) -> dict[str, str]:
    return {
        "window_id": window_id,
        "label": label,
        "evaluation_role": role,
        "source_episode_id": episode,
    }


def _lewm(window_id: str, values: list[float]) -> dict[str, str]:
    return {
        "window_id": window_id,
        **{
            field: str(value)
            for field, value in zip(
                ("mse_t1", "mse_t2", "mse_t3", "l2_t1", "l2_t2", "l2_t3"),
                values,
            )
        },
    }


def test_aggregate_lewm_rows_builds_six_predeclared_variants():
    aggregated = aggregate_lewm_rows([_lewm("w", [1.0, 2.0, 9.0, 3.0, 4.0, 10.0])])

    assert aggregated["lewm_mse_mean"] == pytest.approx([4.0])
    assert aggregated["lewm_mse_max"] == pytest.approx([9.0])
    assert aggregated["lewm_mse_top2_mean"] == pytest.approx([5.5])
    assert aggregated["lewm_l2_mean"] == pytest.approx([17.0 / 3.0])
    assert aggregated["lewm_l2_max"] == pytest.approx([10.0])
    assert aggregated["lewm_l2_top2_mean"] == pytest.approx([7.0])


def test_gate9_metrics_use_calibration_normal_p95_and_evaluation_rows_only():
    manifest = [
        _manifest("c1", "Normal", "calibration_normal", "normal-cal-1"),
        _manifest("c2", "Normal", "calibration_normal", "normal-cal-2"),
        _manifest("n1", "Normal", "evaluation", "normal-eval"),
        _manifest("b1", "Buggy", "evaluation", "buggy-eval"),
    ]
    lewm = [
        _lewm("c1", [0.1] * 6),
        _lewm("c2", [0.3] * 6),
        _lewm("n1", [0.2] * 6),
        _lewm("b1", [0.9] * 6),
    ]
    baselines = [
        {"window_id": "c1", "frame_diff": "0.1", "feature_distance": "0.1"},
        {"window_id": "c2", "frame_diff": "0.3", "feature_distance": "0.3"},
        {"window_id": "n1", "frame_diff": "0.2", "feature_distance": "0.2"},
        {"window_id": "b1", "frame_diff": "0.9", "feature_distance": "0.9"},
    ]

    result = evaluate_gate9_rows(manifest, lewm, baselines)
    metric = result["metrics"]["lewm_mse_mean"]

    assert metric["threshold"] == pytest.approx(0.29)
    assert metric["threshold_source"] == "calibration_normal_p95"
    assert metric["calibration_episode_ids"] == ["normal-cal-1", "normal-cal-2"]
    assert metric["evaluation_window_count"] == 2
    assert metric["auroc"] == 1.0
    assert metric["auprc"] == 1.0
    assert metric["pr_auc"] == metric["auprc"]
    assert metric["f1"] == 1.0
    assert result["class_prevalence"]["positive_fraction"] == 0.5


def test_gate9_alignment_rejects_any_window_order_difference():
    manifest = [
        _manifest("a", "Normal", "calibration_normal", "n1"),
        _manifest("b", "Normal", "calibration_normal", "n2"),
    ]
    lewm = [_lewm("a", [0.1] * 6), _lewm("b", [0.2] * 6)]
    baselines = [
        {"window_id": "a", "frame_diff": "0.1", "feature_distance": "0.1"},
        {"window_id": "b", "frame_diff": "0.2", "feature_distance": "0.2"},
    ]

    validate_gate9_alignment(manifest, lewm, baselines)
    with pytest.raises(ValueError, match="ordered"):
        validate_gate9_alignment(manifest, list(reversed(lewm)), baselines)


def test_gate9_cli_runs_as_a_standalone_script():
    result = subprocess.run(
        [sys.executable, "scripts/run_gate9_ablations.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
