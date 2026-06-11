from pathlib import Path

from glitch_detection.lewm_kaggle import (
    LeWMKaggleConfig,
    prepare_lewm_kaggle_package,
    quota_allocation,
    render_validation_kernel,
    request_package_approvals,
)


def _config() -> LeWMKaggleConfig:
    return LeWMKaggleConfig(
        dataset_slug="user/lewm-private",
        kernel_slug="user/lewm-smoke",
        dataset_id="tempglitch-lewm",
        action_mode="zero_action",
        train_dataset_name="train.lance",
        validation_dataset_name="validation.lance",
    )


def test_quota_allocation_matches_locked_plan():
    allocation = quota_allocation(30)
    assert allocation == {
        "lewm_dual_primary": 15,
        "video_baselines": 7.5,
        "lewm_ablations": 4.5,
        "open_vlm": 3,
    }


def test_kaggle_package_dry_run_is_validation_only(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()

    summary = prepare_lewm_kaggle_package(source, tmp_path / "output", _config(), dry_run=True)

    assert summary["status"] == "dry-run only"
    assert summary["locked_test_included"] is False
    assert not (tmp_path / "output").exists()
    kernel = render_validation_kernel(_config())
    assert "Locked-test execution is forbidden" in kernel
    assert "train_lewm(" in kernel


def test_kaggle_package_creates_separate_fingerprint_bound_requests(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)

    requests = request_package_approvals(package, tmp_path / "approvals")

    dataset = requests["dataset_upload_approval"]
    kernel = requests["kernel_push_approval"]
    assert dataset["fingerprint"] != kernel["fingerprint"]
    assert dataset["one_time_use"] is True
    assert kernel["one_time_use"] is True
    assert requests["live_actions_performed"] is False
    assert (package / "kernel" / "src" / "glitch_detection" / "lewm_training.py").is_file()
