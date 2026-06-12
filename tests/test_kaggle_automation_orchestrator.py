from pathlib import Path

import pytest

from glitch_detection.kaggle_automation import (
    AutomationBlockedError,
    AutomationState,
    KaggleOrchestrator,
    Phase6EKaggleOrchestrator,
    StateStore,
)


def _handlers(calls: list[str]):
    def handler(step: str):
        def run(_state: AutomationState):
            calls.append(step)
            if step == "dataset_fingerprint":
                return {"dataset_fingerprint": "dataset-fp"}
            if step == "kernel_package_generate":
                return {"kernel_fingerprint": "kernel-fp"}
            if step == "kernel_push_once":
                return {"kernel_status": "running"}
            if step == "kernel_poll":
                return {"kernel_status": "success"}
            return {}

        return run

    return {
        step: handler(step)
        for step in [
            "preflight",
            "auth_check_or_request_login",
            "repo_and_security_scan",
            "dataset_dry_run",
            "dataset_prepare",
            "dataset_validate_package",
            "dataset_fingerprint",
            "dataset_create_or_version",
            "kernel_package_generate",
            "kernel_validate_package",
            "kernel_push_once",
            "kernel_poll",
            "artifact_download",
            "artifact_validate",
            "artifact_ingest",
            "complete",
        ]
    }


def test_live_orchestrator_runs_dataset_and_kernel_without_approval_stop(tmp_path: Path):
    calls: list[str] = []
    state = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    ).run()

    assert state.current_step == "complete"
    assert state.requires_approval is None
    assert "dataset_create_or_version" in calls
    assert "kernel_push_once" in calls
    assert not (tmp_path / "approvals").exists()


def test_dry_run_stops_before_first_live_action(tmp_path: Path):
    calls: list[str] = []
    state = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=True,
    ).run()

    assert state.current_step == "dataset_create_or_version"
    assert state.blocked_reason == "dry-run: live action not executed"
    assert "dataset_create_or_version" not in calls


def test_same_kernel_fingerprint_can_only_start_one_push(tmp_path: Path):
    calls: list[str] = []
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    )
    orchestrator.state_store.save(
        AutomationState(
            current_step="kernel_push_once",
            kernel_fingerprint="kernel-fp",
            pushed_kernel_fingerprints=["kernel-fp"],
        )
    )

    with pytest.raises(AutomationBlockedError, match="changed package"):
        orchestrator.run()
    assert "kernel_push_once" not in calls


def test_changed_dataset_fingerprint_resets_to_dataset_live_action(tmp_path: Path):
    calls: list[str] = []
    handlers = _handlers(calls)
    handlers["refresh_dataset_fingerprint"] = lambda _state: {
        "dataset_fingerprint": "dataset-fp-new"
    }
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=handlers,
        dry_run=False,
    )
    orchestrator.state_store.save(
        AutomationState(
            current_step="kernel_package_generate",
            completed_steps=[
                "preflight",
                "auth_check_or_request_login",
                "repo_and_security_scan",
                "dataset_dry_run",
                "dataset_prepare",
                "dataset_validate_package",
                "dataset_fingerprint",
                "dataset_create_or_version",
            ],
            dataset_fingerprint="dataset-fp-old",
        )
    )

    result = orchestrator.run()

    assert result.dataset_fingerprint == "dataset-fp-new"
    assert "dataset_create_or_version" in calls


def test_switching_from_dry_run_to_live_resets_before_real_dataset_prepare(tmp_path: Path):
    calls: list[str] = []
    StateStore(tmp_path / "state.json").save(
        AutomationState(
            current_step="dataset_create_or_version",
            completed_steps=[
                "preflight",
                "auth_check_or_request_login",
                "repo_and_security_scan",
                "dataset_dry_run",
                "dataset_prepare",
                "dataset_validate_package",
                "dataset_fingerprint",
            ],
            dataset_fingerprint="dry-fingerprint",
            execution_mode="dry-run",
        )
    )

    result = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    ).run()

    assert "dataset_prepare" in calls
    assert result.execution_mode == "live"


def test_state_store_migrates_old_gpu_push_field(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text(
        '{"current_step":"preflight","gpu_push_fingerprints":["old"],'
        '"requires_approval":"kernel_push_approval"}',
        encoding="utf-8",
    )

    state = StateStore(path).load()

    assert state.pushed_kernel_fingerprints == ["old"]
    assert state.requires_approval is None


def test_generic_orchestrator_accepts_custom_workflow(tmp_path: Path):
    calls: list[str] = []

    def run_step(_state: AutomationState):
        calls.append("prepare")
        return {"dataset_fingerprint": "fp"}

    orchestrator = KaggleOrchestrator(
        root=tmp_path,
        handlers={"prepare": run_step, "complete": lambda _state: {}},
        steps=("prepare", "complete"),
        live_action_fingerprints={},
        dry_run=False,
    )

    state = orchestrator.run()

    assert calls == ["prepare"]
    assert state.current_step == "complete"
