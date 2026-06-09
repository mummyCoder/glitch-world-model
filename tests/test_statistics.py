from glitch_detection.statistics import bootstrap_metric_ci
from scripts.evaluate_tempglitch_locked_test import write_locked_metrics_markdown

ROWS = [
    {"source": "n1", "pair_id_heuristic": "p1", "label": 0, "score": 0.1},
    {"source": "p1", "pair_id_heuristic": "p1", "label": 1, "score": 0.9},
    {"source": "n2", "pair_id_heuristic": "p2", "label": 0, "score": 0.2},
    {"source": "p2", "pair_id_heuristic": "p2", "label": 1, "score": 0.8},
]


def test_bootstrap_auroc_ci_is_deterministic_and_reports_metadata():
    first = bootstrap_metric_ci(ROWS, "auroc", n_bootstrap=100, seed=42, group_key="source")
    second = bootstrap_metric_ci(ROWS, "auroc", n_bootstrap=100, seed=42, group_key="source")

    assert first == second
    assert first["point"] == 1.0
    assert first["lower"] <= first["mean"] <= first["upper"]
    assert first["valid_bootstrap_count"] < 100
    assert first["n_bootstrap"] == 100
    assert first["seed"] == 42
    assert first["group_key"] == "source"
    assert first["confidence_level"] == 0.95


def test_bootstrap_f1_ci_supports_pair_level_resampling():
    result = bootstrap_metric_ci(
        ROWS,
        "f1",
        n_bootstrap=50,
        seed=7,
        group_key="pair_id_heuristic",
        threshold=0.5,
    )

    assert result["point"] == 1.0
    assert result["valid_bootstrap_count"] == 50
    assert result["group_key"] == "pair_id_heuristic"


def test_locked_metrics_markdown_handles_undefined_auroc_ci(tmp_path):
    payload = {
        "selection_split": "validation",
        "scorer": "demo",
        "aggregation": "mean",
        "threshold": 0.5,
        "evaluated_config_count": 1,
        "test_metrics": {"auroc": None, "f1": 0.0},
        "confidence_intervals": {
            "auroc": {
                "point": None,
                "lower": None,
                "upper": None,
                "valid_bootstrap_count": 0,
                "n_bootstrap": 10,
                "group_key": "source",
            }
        },
    }

    path = write_locked_metrics_markdown(payload, tmp_path / "metrics.md")

    assert "n/a" in path.read_text(encoding="utf-8")
