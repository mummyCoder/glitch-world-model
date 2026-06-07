from glitch_detection.evaluate import auroc, binary_metrics, choose_best_f1_threshold


def test_binary_metrics():
    metrics = binary_metrics(labels=[0, 1, 1, 0], predictions=[0, 1, 0, 0])

    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert round(metrics["f1"], 6) == round(2 / 3, 6)
    assert metrics["accuracy"] == 0.75


def test_choose_best_f1_threshold_and_auroc():
    labels = [0, 0, 1, 1]
    scores = [0.1, 0.2, 0.8, 0.9]

    threshold, metrics = choose_best_f1_threshold(labels, scores)

    assert threshold in scores
    assert metrics["f1"] == 1.0
    assert auroc(labels, scores) == 1.0
