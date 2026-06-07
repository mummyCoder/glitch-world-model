from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_score_series(scores_path: Path) -> tuple[list[int], list[float]]:
    starts: list[int] = []
    scores: list[float] = []
    with scores_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            starts.append(int(row["start_frame"]))
            scores.append(float(row["score"]))
    return starts, scores


def plot_scores(scores_path: Path, output_path: Path) -> Path:
    from PIL import Image, ImageDraw

    starts, scores = read_score_series(scores_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = 1000, 420
    margin_left, margin_top, margin_right, margin_bottom = 70, 40, 30, 60
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((margin_left, 12), "Frame-Difference Anomaly Score", fill="black")

    x0, y0 = margin_left, margin_top + plot_height
    x1, y1 = margin_left + plot_width, margin_top
    draw.line([(x0, y0), (x1, y0)], fill="black", width=2)
    draw.line([(x0, y0), (x0, y1)], fill="black", width=2)
    draw.text((width // 2 - 45, height - 32), "Clip start frame", fill="black")
    draw.text((8, height // 2 - 8), "Score", fill="black")

    if starts and scores:
        min_x, max_x = min(starts), max(starts)
        min_y, max_y = min(scores), max(scores)
        if max_x == min_x:
            max_x += 1
        if max_y == min_y:
            max_y += 1.0

        points = []
        for start, score in zip(starts, scores):
            x = x0 + int((start - min_x) / (max_x - min_x) * plot_width)
            y = y0 - int((score - min_y) / (max_y - min_y) * plot_height)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=(30, 100, 220), width=3)
        for point in points:
            x, y = point
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(30, 100, 220))

        draw.text((x0, y0 + 8), str(min_x), fill="black")
        draw.text((x1 - 40, y0 + 8), str(max_x), fill="black")
        draw.text((x0 - 55, y0 - 8), f"{min_y:.3f}", fill="black")
        draw.text((x0 - 55, y1 - 8), f"{max_y:.3f}", fill="black")

    image.save(output_path)
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot anomaly scores over time.")
    parser.add_argument("--scores", required=True, type=Path, help="Path to scores.csv.")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG path.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_path = plot_scores(args.scores, args.output)
    print(f"Wrote plot: {output_path}")


if __name__ == "__main__":
    main()
