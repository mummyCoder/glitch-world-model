from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from glitch_detection.gate6_data import read_rows_by_source, sha256_file
from glitch_detection.manifest import ClipRecord, write_manifest


def evenly_spaced_starts(frame_count: int, clip_frames: int, clips_per_source: int) -> list[int]:
    if frame_count < clip_frames:
        return []
    if clips_per_source <= 1:
        return [(frame_count - clip_frames) // 2]
    maximum = frame_count - clip_frames
    return sorted(
        {round(index * maximum / (clips_per_source - 1)) for index in range(clips_per_source)}
    )


def build_validation_manifest(
    metadata_path: Path,
    split_path: Path,
    video_root: Path,
    output_root: Path,
    *,
    clip_frames: int = 16,
    clips_per_source: int = 4,
    image_size: int = 112,
) -> dict[str, object]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Validation manifest extraction requires opencv-python.") from exc
    metadata = read_rows_by_source(metadata_path)
    split = read_rows_by_source(split_path)
    records: list[ClipRecord] = []
    protocol_rows: list[dict[str, str]] = []
    label_rows: list[dict[str, object]] = []
    frames_root = output_root / "frames"
    for source in sorted(metadata):
        split_row = split.get(source)
        if (
            split_row is None
            or split_row["split"] != "validation"
            or split_row["label"] not in {"Normal", "Buggy"}
            or split_row["materialize"].lower() != "true"
        ):
            continue
        video_path = video_root / metadata[source]["local_video_path"]
        if not video_path.is_file():
            continue
        capture = cv2.VideoCapture(str(video_path))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        for clip_index, start in enumerate(
            evenly_spaced_starts(frame_count, clip_frames, clips_per_source)
        ):
            clip_id = f"{source}__{clip_index:02d}"
            clip_dir = frames_root / clip_id
            clip_dir.mkdir(parents=True, exist_ok=True)
            capture.set(cv2.CAP_PROP_POS_FRAMES, start)
            written = 0
            while written < clip_frames:
                ok, frame = capture.read()
                if not ok:
                    break
                frame = cv2.resize(frame, (image_size, image_size), interpolation=cv2.INTER_AREA)
                cv2.imwrite(str(clip_dir / f"{written:06d}.jpg"), frame)
                written += 1
            if written != clip_frames:
                continue
            end = start + clip_frames - 1
            records.append(ClipRecord(clip_id, source, str(clip_dir), start, end, written, fps))
            protocol_rows.append(
                {
                    "clip_id": clip_id,
                    "source": source,
                    "pair_id": split_row["pair_id"],
                    "category": split_row["category"],
                    "label": split_row["label"],
                    "split": "validation",
                    "locked_test": "False",
                }
            )
            if split_row["label"] == "Buggy":
                label_rows.append(
                    {"source": source, "start_frame": start, "end_frame": end, "label": 1}
                )
        capture.release()
    manifest_path = output_root / "tempglitch_validation_manifest.csv"
    labels_path = output_root / "tempglitch_validation_labels.csv"
    protocol_path = output_root / "tempglitch_validation_protocol.csv"
    write_manifest(manifest_path, records)
    for path, rows, fields in (
        (labels_path, label_rows, ["source", "start_frame", "end_frame", "label"]),
        (
            protocol_path,
            protocol_rows,
            ["clip_id", "source", "pair_id", "category", "label", "split", "locked_test"],
        ),
    ):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    summary = {
        "status": "validation_manifest_ready",
        "manifest": str(manifest_path),
        "labels": str(labels_path),
        "protocol": str(protocol_path),
        "clip_count": len(records),
        "normal_clip_count": sum(row["label"] == "Normal" for row in protocol_rows),
        "buggy_clip_count": sum(row["label"] == "Buggy" for row in protocol_rows),
        "metadata_sha256": sha256_file(metadata_path),
        "split_sha256": sha256_file(split_path),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    (output_root / "manifest_metadata.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build a non-locked TempGlitch validation manifest."
    )
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--video-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--clip-frames", type=int, default=16)
    parser.add_argument("--clips-per-source", type=int, default=4)
    parser.add_argument("--image-size", type=int, default=112)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            build_validation_manifest(
                args.metadata,
                args.split,
                args.video_root,
                args.output_root,
                clip_frames=args.clip_frames,
                clips_per_source=args.clips_per_source,
                image_size=args.image_size,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
