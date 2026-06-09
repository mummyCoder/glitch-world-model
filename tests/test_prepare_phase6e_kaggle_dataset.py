from pathlib import Path

from glitch_detection.manifest import ClipRecord, write_manifest
from scripts.prepare_phase6e_kaggle_dataset import prepare_phase6e_kaggle_dataset


def _processed_root(tmp_path: Path) -> Path:
    processed_root = tmp_path / "processed" / "tempglitch_phase3b"
    clip_dir = processed_root / "normal_1" / "clips" / "normal_1_000000"
    clip_dir.mkdir(parents=True)
    (clip_dir / "000000.png").write_bytes(b"frame")
    write_manifest(
        processed_root / "manifest.csv",
        [ClipRecord("normal_1_000000", "normal_1", str(clip_dir), 0, 0, 1, 30.0)],
    )
    return processed_root


def test_prepare_dataset_dry_run_validates_without_materializing_output(tmp_path: Path):
    processed_root = _processed_root(tmp_path)
    split_path = tmp_path / "split.csv"
    split_path.write_text(
        "source,category,label,split,pair_id_heuristic\n"
        "normal_1,Blinking,Normal,train,Blinking/1\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "upload"

    summary = prepare_phase6e_kaggle_dataset(
        processed_root=processed_root,
        split_path=split_path,
        output_root=output_root,
        dry_run=True,
    )

    assert summary["status"] == "dry-run only"
    assert summary["manifest_clip_count"] == 1
    assert summary["missing_clip_dir_count"] == 0
    assert summary["estimated_file_count"] >= 2
    assert not output_root.exists()


def test_prepare_dataset_copy_mode_creates_expected_upload_layout(tmp_path: Path):
    processed_root = _processed_root(tmp_path)
    split_path = tmp_path / "split.csv"
    split_path.write_text(
        "source,category,label,split,pair_id_heuristic\n"
        "normal_1,Blinking,Normal,train,Blinking/1\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "upload"

    summary = prepare_phase6e_kaggle_dataset(
        processed_root=processed_root,
        split_path=split_path,
        output_root=output_root,
        dry_run=False,
        mode="copy",
    )

    assert summary["status"] == "dataset package complete"
    assert (output_root / "tempglitch_phase3b" / "manifest.csv").is_file()
    assert (
        output_root / "tempglitch_phase3b" / "normal_1" / "clips" / "normal_1_000000" / "000000.png"
    ).is_file()
    assert (output_root / "split.csv").is_file()
    assert (output_root / "dataset-metadata.template.json").is_file()
    assert (output_root / "UPLOAD_README.md").is_file()
