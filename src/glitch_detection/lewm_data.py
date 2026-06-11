from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image

from .manifest import ClipRecord
from .preprocess import IMAGE_EXTENSIONS


class LeWMDataUnavailableError(RuntimeError):
    """Raised when the optional stable-worldmodel data runtime is unavailable."""


@dataclass(frozen=True)
class LeWMEpisode:
    dataset_id: str
    source: str
    episode_id: str
    pixels: list[np.ndarray]
    action: np.ndarray
    label: str
    category: str
    split: str
    pair_id: str
    action_mode: str

    def __post_init__(self) -> None:
        if len(self.pixels) != len(self.action):
            raise ValueError("LeWM episode pixels and actions must have identical lengths.")
        if len(self.pixels) < 2:
            raise ValueError("LeWM episode requires at least two steps.")
        if self.action.ndim != 2:
            raise ValueError("LeWM episode actions must have shape (steps, action_dim).")

    def writer_payload(self) -> dict[str, Any]:
        count = len(self.pixels)
        return {
            "pixels": self.pixels,
            "action": [row for row in self.action.astype(np.float32)],
            "dataset_id": [self.dataset_id] * count,
            "source": [self.source] * count,
            "source_episode_id": [self.episode_id] * count,
            "label": [self.label] * count,
            "category": [self.category] * count,
            "split": [self.split] * count,
            "pair_id": [self.pair_id] * count,
            "action_mode": [self.action_mode] * count,
        }


def _frame_paths(record: ClipRecord) -> list[Path]:
    root = Path(record.clip_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Missing clip directory: {root}")
    frames = sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if len(frames) < 2:
        raise ValueError(f"LeWM conversion requires at least two frames: {root}")
    return frames


def episode_from_clip(
    record: ClipRecord,
    *,
    dataset_id: str,
    category: str,
    label: str,
    split: str,
    pair_id: str,
    action_mode: str = "zero_action",
    actions: np.ndarray | None = None,
) -> LeWMEpisode:
    pixels: list[np.ndarray] = []
    for path in _frame_paths(record):
        with Image.open(path) as image:
            pixels.append(np.asarray(image.convert("RGB"), dtype=np.uint8))
    if action_mode == "real":
        if actions is None:
            raise ValueError("Real-action LeWM conversion requires synchronized actions.")
        action = np.asarray(actions, dtype=np.float32)
    elif action_mode == "zero_action":
        action = np.zeros((len(pixels), 1), dtype=np.float32)
    else:
        raise ValueError("Dataset conversion supports only real or zero_action modes.")
    return LeWMEpisode(
        dataset_id=dataset_id,
        source=record.source,
        episode_id=record.clip_id,
        pixels=pixels,
        action=action,
        label=label,
        category=category,
        split=split,
        pair_id=pair_id,
        action_mode=action_mode,
    )


def write_lance_dataset(
    episodes: Iterable[LeWMEpisode],
    output_path: Path,
    *,
    mode: str = "error",
) -> Path:
    try:
        from stable_worldmodel.data import LanceWriter
    except ImportError as exc:
        raise LeWMDataUnavailableError(
            "Lance conversion requires the isolated LeWM runtime from requirements/lewm-runtime.txt."
        ) from exc
    payloads = [episode.writer_payload() for episode in episodes]
    if not payloads:
        raise ValueError("Cannot write an empty LeWM dataset.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with LanceWriter(output_path.resolve().as_posix(), mode=mode) as writer:
        writer.write_episodes(payloads)
    return output_path


def inspect_lance_dataset(
    path: Path,
    *,
    num_steps: int = 4,
    frameskip: int = 1,
) -> dict[str, Any]:
    try:
        import stable_worldmodel as swm
    except ImportError as exc:
        raise LeWMDataUnavailableError(
            "Dataset inspection requires the isolated LeWM runtime."
        ) from exc
    # LanceDataset's Windows path parser requires POSIX separators in stable-worldmodel 0.1.1.
    dataset = swm.data.LanceDataset(
        path=str(path.resolve().as_posix()),
        num_steps=num_steps,
        frameskip=frameskip,
        keys_to_load=["pixels", "action"],
    )
    if not len(dataset):
        raise ValueError("LeWM dataset contains no valid temporal windows.")
    sample = dataset[0]
    return {
        "path": str(path),
        "format": "lance",
        "window_count": len(dataset),
        "columns": dataset.column_names,
        "pixels_shape": list(sample["pixels"].shape),
        "pixels_dtype": str(sample["pixels"].dtype),
        "action_shape": list(sample["action"].shape),
        "action_dtype": str(sample["action"].dtype),
        "num_steps": num_steps,
        "frameskip": frameskip,
        "episode_boundary_policy": "writer-managed episode_idx; windows generated within episodes",
    }


def write_dataset_inspection(summary: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return output_path
