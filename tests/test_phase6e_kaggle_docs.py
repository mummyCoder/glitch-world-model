from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "kaggle" / "phase6e_video_autoencoder"


def test_phase6e_kaggle_launch_package_contains_required_docs():
    required = [
        PACKAGE_ROOT / "README.md",
        PACKAGE_ROOT / "phase6e_kaggle_cells.md",
        PACKAGE_ROOT / "dataset-metadata.template.json",
        PACKAGE_ROOT / "DO_NOT_COMMIT_ARTIFACTS.md",
        ROOT / "docs" / "research" / "30_phase6e_kaggle_run_log_template.md",
    ]

    assert all(path.is_file() for path in required)


def test_phase6e_kaggle_cells_keep_locked_test_untouched():
    cells = (PACKAGE_ROOT / "phase6e_kaggle_cells.md").read_text(encoding="utf-8")

    assert "--dry-run" in cells
    assert "test_scored" in cells
    assert 'assert summary.get("test_scored") is False' in cells
    assert "run_kaggle_video_autoencoder.py" in cells
