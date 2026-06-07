from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClipRecord:
    clip_id: str
    source: str
    clip_dir: str
    start_frame: int
    end_frame: int
    frame_count: int
    fps: float


@dataclass(frozen=True)
class LabelInterval:
    source: str
    start_frame: int
    end_frame: int
    label: int


MANIFEST_FIELDS = [
    "clip_id",
    "source",
    "clip_dir",
    "start_frame",
    "end_frame",
    "frame_count",
    "fps",
]


def write_manifest(path: Path, records: list[ClipRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "source": record.source,
                    "clip_dir": record.clip_dir,
                    "start_frame": record.start_frame,
                    "end_frame": record.end_frame,
                    "frame_count": record.frame_count,
                    "fps": f"{record.fps:.6g}",
                }
            )


def read_manifest(path: Path) -> list[ClipRecord]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [
            ClipRecord(
                clip_id=row["clip_id"],
                source=row["source"],
                clip_dir=row["clip_dir"],
                start_frame=int(row["start_frame"]),
                end_frame=int(row["end_frame"]),
                frame_count=int(row["frame_count"]),
                fps=float(row["fps"]),
            )
            for row in reader
        ]


def read_labels(path: Path | None) -> list[LabelInterval]:
    if path is None or not path.exists():
        return []
    labels: list[LabelInterval] = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = int(row.get("label", "1"))
            if label != 1:
                continue
            labels.append(
                LabelInterval(
                    source=row["source"],
                    start_frame=int(row["start_frame"]),
                    end_frame=int(row["end_frame"]),
                    label=label,
                )
            )
    return labels


def clip_has_glitch(
    source: str,
    start_frame: int,
    end_frame: int,
    labels: list[LabelInterval],
) -> bool:
    for interval in labels:
        if interval.source != source:
            continue
        if start_frame <= interval.end_frame and end_frame >= interval.start_frame:
            return True
    return False
