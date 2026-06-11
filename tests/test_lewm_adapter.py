import json
from pathlib import Path

import pytest

from glitch_detection.lewm_adapter import (
    ActionMode,
    LeWMAdapter,
    LeWMCheckpointSpec,
    LeWMIntegrationError,
    sha256_file,
)


def _config(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "encoder": {"image_size": 224},
                "predictor": {"num_frames": 3},
                "action_encoder": {"input_dim": 10},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_checkpoint_hash_is_verified_before_runtime_load(tmp_path: Path):
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"checkpoint")
    adapter = LeWMAdapter(
        LeWMCheckpointSpec(
            weights,
            _config(tmp_path / "config.json"),
            ActionMode.REAL,
            expected_sha256="wrong",
        )
    )

    with pytest.raises(LeWMIntegrationError, match="SHA-256"):
        adapter.load()
    assert sha256_file(weights)


def test_action_free_mode_is_declared_but_fail_closed(tmp_path: Path):
    adapter = LeWMAdapter(
        LeWMCheckpointSpec(
            tmp_path / "weights.pt",
            tmp_path / "config.json",
            ActionMode.ACTION_FREE,
        )
    )
    with pytest.raises(LeWMIntegrationError, match="action_free"):
        adapter._validate_config(
            {
                "encoder": {"image_size": 224},
                "predictor": {"num_frames": 3},
                "action_encoder": {"input_dim": 1},
            }
        )
