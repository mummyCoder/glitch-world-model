from __future__ import annotations

import argparse
import csv
from pathlib import Path


def plot_scores(scores_path: Path, output_path: Path) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Timeline plotting requires matplotlib.") from exc
    with scores_path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Cannot plot an empty scores.csv.")
    values = [float(row["score"]) for row in rows]
    figure, axis = plt.subplots(figsize=(10, 4))
    axis.plot(range(len(values)), values, linewidth=1.5)
    axis.set_title("LeWM latent-surprise timeline")
    axis.set_xlabel("Clip index")
    axis.set_ylabel("Surprise score")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot LeWM scores without changing CSV format.")
    parser.add_argument("--scores", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    print(plot_scores(args.scores, args.output))


if __name__ == "__main__":
    main()
