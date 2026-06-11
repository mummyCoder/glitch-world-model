from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.evaluate import evaluate_scores
from glitch_detection.lewm_adapter import sha256_file


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate Gate 7 validation-only LeWM scores.")
    parser.add_argument("--scores", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = evaluate_scores(
        args.scores,
        args.labels,
        args.output,
        allow_fit_threshold=True,
    )
    result.update(
        {
            "status": "validation_only",
            "scores_sha256": sha256_file(args.scores),
            "labels_sha256": sha256_file(args.labels),
            "higher_is_more_anomalous": True,
            "locked_test_scored": False,
        }
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
