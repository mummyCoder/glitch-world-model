from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .lewm_adapter import ActionMode, LeWMAdapter, LeWMCheckpointSpec, LeWMIntegrationError
from .manifest import ClipRecord, read_manifest
from .preprocess import IMAGE_EXTENSIONS


class LeWMUnavailableError(RuntimeError):
    """Raised when the LeWM scorer is requested before model dependencies are ready."""


def resolve_checkpoint(checkpoint: Path | None) -> Path:
    candidate = checkpoint or (
        Path(os.environ["LEWM_CHECKPOINT"]) if "LEWM_CHECKPOINT" in os.environ else None
    )
    if candidate is None:
        raise LeWMUnavailableError(
            "LeWM latent scoring requires a checkpoint. Pass --checkpoint PATH or set "
            "LEWM_CHECKPOINT. Next step: download/convert a LeWM checkpoint from the "
            "official Hugging Face collection, then implement latent prediction error."
        )
    if not candidate.exists():
        raise LeWMUnavailableError(f"LeWM checkpoint does not exist: {candidate}")
    return candidate


def resolve_config(config: Path | None, checkpoint: Path) -> Path:
    candidate = config or (
        Path(os.environ["LEWM_CONFIG"])
        if "LEWM_CONFIG" in os.environ
        else checkpoint.with_name("config.json")
    )
    if not candidate.is_file():
        raise LeWMUnavailableError(
            f"LeWM config does not exist: {candidate}. Pass --config or set LEWM_CONFIG."
        )
    return candidate


def _require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise LeWMUnavailableError(
            "LeWM scoring requires the isolated Python 3.10 runtime from "
            "requirements/lewm-runtime.txt."
        ) from exc
    return torch


def _list_frames(record: ClipRecord) -> list[Path]:
    root = Path(record.clip_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Missing clip directory: {root}")
    frames = sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not frames:
        raise ValueError(f"Clip contains no supported frames: {root}")
    return frames


def _load_pixels(record: ClipRecord, image_size: int) -> Any:
    torch = _require_torch()
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)
    frames: list[np.ndarray] = []
    for path in _list_frames(record):
        with Image.open(path) as image:
            rgb = image.convert("RGB").resize((image_size, image_size), Image.Resampling.BILINEAR)
            frame = np.asarray(rgb, dtype=np.float32) / 255.0
            frames.append(np.transpose((frame - mean) / std, (2, 0, 1)))
    return torch.from_numpy(np.stack(frames).astype(np.float32))


def score_record(adapter: LeWMAdapter, record: ClipRecord) -> float:
    torch = _require_torch()
    pixels = _load_pixels(record, adapter.image_size)
    window_size = adapter.history_size + 1
    if len(pixels) < window_size:
        raise ValueError(f"LeWM scoring requires at least {window_size} frames: {record.clip_id}")
    windows = torch.stack(
        [pixels[start : start + window_size] for start in range(len(pixels) - window_size + 1)]
    )
    surprise = adapter.surprise(windows)
    score = float(surprise.mean().item())
    if not np.isfinite(score):
        raise ValueError(f"LeWM produced a non-finite score for {record.clip_id}.")
    return score


def score_manifest(
    manifest_path: Path,
    labels_path: Path | None,
    output_path: Path,
    checkpoint: Path | None = None,
    config: Path | None = None,
    action_mode: str | None = None,
    device: str = "cpu",
) -> Path:
    _ = labels_path
    checkpoint_path = resolve_checkpoint(checkpoint)
    config_path = resolve_config(config, checkpoint_path)
    selected_mode = action_mode or os.environ.get("LEWM_ACTION_MODE", "zero_action")
    try:
        adapter = LeWMAdapter(
            LeWMCheckpointSpec(
                weights_path=checkpoint_path,
                config_path=config_path,
                action_mode=ActionMode(selected_mode),
                device=device,
            )
        ).load()
    except (ValueError, LeWMIntegrationError) as exc:
        raise LeWMUnavailableError(str(exc)) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
        )
        writer.writeheader()
        for record in read_manifest(manifest_path):
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "source": record.source,
                    "clip_dir": record.clip_dir,
                    "start_frame": record.start_frame,
                    "end_frame": record.end_frame,
                    "score": f"{score_record(adapter, record):.8f}",
                }
            )
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score clips with LeWM latent prediction error.")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.csv.")
    parser.add_argument("--labels", type=Path, default=None, help="Optional labels CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output scores.csv path.")
    parser.add_argument("--checkpoint", type=Path, default=None, help="LeWM checkpoint path.")
    parser.add_argument("--config", type=Path, default=None, help="LeWM checkpoint config.json.")
    parser.add_argument(
        "--action-mode",
        choices=[mode.value for mode in ActionMode],
        default="zero_action",
    )
    parser.add_argument("--device", default="cpu")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        output_path = score_manifest(
            args.manifest,
            args.labels,
            args.output,
            args.checkpoint,
            args.config,
            args.action_mode,
            args.device,
        )
    except LeWMUnavailableError as exc:
        raise SystemExit(f"LeWM latent scorer is not ready: {exc}") from exc
    print(f"Wrote scores: {output_path}")


if __name__ == "__main__":
    main()
