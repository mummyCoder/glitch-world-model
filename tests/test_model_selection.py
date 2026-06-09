from glitch_detection.model_selection import evaluate_locked_test, select_validation_config


def test_select_validation_config_ignores_test_metrics():
    candidates = [
        {
            "scorer": "safe",
            "aggregation": "mean",
            "threshold": 0.4,
            "validation_metrics": {"auroc": 0.8, "f1": 0.6},
            "test_metrics": {"auroc": 0.1, "f1": 0.1},
        },
        {
            "scorer": "test_winner",
            "aggregation": "max",
            "threshold": 0.7,
            "validation_metrics": {"auroc": 0.6, "f1": 0.7},
            "test_metrics": {"auroc": 1.0, "f1": 1.0},
        },
    ]

    selected = select_validation_config(candidates, seed=42)

    assert selected["scorer"] == "safe"
    assert selected["selection_split"] == "validation"
    assert selected["selection_metric"] == "auroc"
    assert "test_metrics" not in selected


def test_select_validation_config_falls_back_to_validation_f1():
    selected = select_validation_config(
        [
            {
                "scorer": "a",
                "aggregation": "mean",
                "threshold": 0.4,
                "validation_metrics": {"auroc": None, "f1": 0.5},
            },
            {
                "scorer": "b",
                "aggregation": "max",
                "threshold": 0.7,
                "validation_metrics": {"auroc": None, "f1": 0.8},
            },
        ]
    )

    assert selected["scorer"] == "b"
    assert selected["selection_metric"] == "f1"


def test_evaluate_locked_test_uses_exactly_one_selected_configuration():
    selected = {
        "scorer": "safe",
        "aggregation": "mean",
        "threshold": 0.5,
        "selection_split": "validation",
    }
    rows_by_config = {
        ("safe", "mean"): [
            {"source": "normal", "label": 0, "score": 0.2},
            {"source": "buggy", "label": 1, "score": 0.8},
        ],
        ("test_winner", "max"): [
            {"source": "normal", "label": 0, "score": 0.9},
            {"source": "buggy", "label": 1, "score": 1.0},
        ],
    }

    result = evaluate_locked_test(selected, rows_by_config)

    assert result["evaluated_config_count"] == 1
    assert result["scorer"] == "safe"
    assert result["aggregation"] == "mean"
    assert result["test_metrics"]["f1"] == 1.0
