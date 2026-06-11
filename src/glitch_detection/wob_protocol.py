from __future__ import annotations

import io
import re
import tarfile
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

STEP_PATTERN = re.compile(r"^(?P<index>\d{8})\.npz$")
NORMAL_PATTERN = re.compile(r"^NORMAL-TRAIN/(?P<episode>ep-\d+)/[^/]+\.tar$")
SMALL_NORMAL_PATTERN = re.compile(r"^NORMAL-TRAIN-SMALL/")
BUG_PATTERN = re.compile(r"^TEST/(?P<category>[^/]+)/(?P<episode>ep-\d+)/[^/]+\.tar$")
REQUIRED_KEYS = {"state", "action", "reward", "done"}


def parse_wob_inventory(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    normal: list[dict[str, str]] = []
    bugs: list[dict[str, str]] = []
    excluded_small = 0
    unknown: list[str] = []
    for row in rows:
        name = row["name"]
        if SMALL_NORMAL_PATTERN.match(name):
            excluded_small += 1
            continue
        normal_match = NORMAL_PATTERN.match(name)
        if normal_match:
            episode = normal_match.group("episode")
            normal.append(
                {
                    "source": name,
                    "episode_id": f"normal/{episode}",
                    "category": "Normal",
                    "label": "Normal",
                    "size_bytes": row.get("size", ""),
                }
            )
            continue
        bug_match = BUG_PATTERN.match(name)
        if bug_match:
            category = bug_match.group("category")
            episode = bug_match.group("episode")
            bugs.append(
                {
                    "source": name,
                    "episode_id": f"{category}/{episode}",
                    "category": category,
                    "label": "Buggy",
                    "size_bytes": row.get("size", ""),
                }
            )
            continue
        unknown.append(name)

    category_counts = Counter(row["category"] for row in bugs)
    return (
        sorted(normal, key=lambda row: row["source"]),
        sorted(bugs, key=lambda row: row["source"]),
        {
            "normal_episode_count": len(normal),
            "bug_episode_count": len(bugs),
            "bug_category_counts": dict(sorted(category_counts.items())),
            "excluded_small_normal_count": excluded_small,
            "unknown_file_count": len(unknown),
            "unknown_files": sorted(unknown),
        },
    )


def inspect_wob_episode_tar(
    path: Path,
    *,
    minimum_steps: int = 2,
    sample_limit: int = 32,
) -> dict[str, Any]:
    """Inspect numeric WOB fields without unpickling the optional info object."""
    with tarfile.open(path, "r") as archive:
        indexed_members = []
        for member in archive.getmembers():
            match = STEP_PATTERN.match(Path(member.name).name)
            if member.isfile() and match:
                indexed_members.append((int(match.group("index")), member))
        indexed_members.sort(key=lambda item: item[0])
        if len(indexed_members) < minimum_steps:
            raise ValueError(
                f"WOB episode {path} is shorter than minimum_steps={minimum_steps}: "
                f"{len(indexed_members)}"
            )
        indices = [index for index, _ in indexed_members]
        if indices != list(range(indices[0], indices[0] + len(indices))):
            raise ValueError(f"WOB episode {path} step indices are not contiguous.")

        selected = indexed_members[:sample_limit]
        action_values: set[int] = set()
        state_shape: tuple[int, ...] | None = None
        action_shape: tuple[int, ...] | None = None
        keys: set[str] | None = None
        for _, member in selected:
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"Could not read WOB tar member {member.name}.")
            with np.load(io.BytesIO(extracted.read()), allow_pickle=False) as sample:
                sample_keys = set(sample.files)
                if not REQUIRED_KEYS.issubset(sample_keys):
                    missing = sorted(REQUIRED_KEYS - sample_keys)
                    raise ValueError(
                        f"WOB sample {member.name} is missing required keys: {missing}"
                    )
                state = sample["state"]
                action = sample["action"]
                reward = sample["reward"]
                done = sample["done"]
                if state.ndim != 3 or not np.issubdtype(state.dtype, np.floating):
                    raise ValueError(f"WOB sample {member.name} has invalid state tensor.")
                if action.shape != () or not np.issubdtype(action.dtype, np.integer):
                    raise ValueError(f"WOB sample {member.name} has invalid scalar action.")
                if reward.shape != () or done.shape != ():
                    raise ValueError(f"WOB sample {member.name} has invalid reward/done scalar.")
                if not np.isfinite(state).all() or not np.isfinite(reward).all():
                    raise ValueError(
                        f"WOB sample {member.name} contains non-finite numeric values."
                    )
                if state_shape is not None and state.shape != state_shape:
                    raise ValueError(
                        f"WOB sample {member.name} changed state shape within episode."
                    )
                state_shape = state.shape
                action_shape = action.shape
                action_values.add(int(action))
                keys = sample_keys if keys is None else keys & sample_keys

    return {
        "tar_path": str(path),
        "step_count": len(indexed_members),
        "sampled_step_count": len(selected),
        "first_step_index": indices[0],
        "last_step_index": indices[-1],
        "contiguous_step_indices": True,
        "common_keys": sorted(keys or set()),
        "state_shape": list(state_shape or ()),
        "action_shape": list(action_shape or ()),
        "action_values": sorted(action_values),
        "required_numeric_schema_valid": True,
        "action_state_structurally_aligned": True,
        "semantic_action_synchronization_verified": False,
        "info_unpickled": False,
    }
