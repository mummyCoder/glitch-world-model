from pathlib import Path

import pytest

from glitch_detection.lewm_latent import LeWMUnavailableError, score_manifest
from glitch_detection.score_clips import available_scorers


def test_lewm_latent_registered():
    assert "lewm_latent" in available_scorers()


def test_lewm_latent_requires_checkpoint(tmp_path: Path):
    with pytest.raises(LeWMUnavailableError, match="checkpoint"):
        score_manifest(
            manifest_path=tmp_path / "manifest.csv",
            labels_path=None,
            output_path=tmp_path / "scores.csv",
        )
