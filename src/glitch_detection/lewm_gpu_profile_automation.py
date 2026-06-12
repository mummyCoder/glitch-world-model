from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .kaggle_automation import (
    AutomationBlockedError,
    AutomationCommandError,
    CommandRunner,
    KaggleAction,
    KaggleExecutionPolicy,
    SecurityGuard,
)
from .lewm_gpu_profile import validate_lewm_gpu_profile_artifacts
from .lewm_gpu_profile_kaggle import (
    LeWMGPUProfileKaggleConfig,
    prepare_profile_kaggle_package,
    validate_profile_kaggle_package,
)

APPROVED_BATCH_LADDER = (8, 6, 4, 2)
EXPECTED_COUNTS = {"train_normal": 36, "validation_normal": 14, "validation_buggy": 22}
EXPECTED_DATASET_HASHES = {
    "train": "e6c48a35eef32edf43a6c78db37c52adcbbe656f47b2e453e1917365355f3aa1",
    "validation": "bb89e66c6afa5d3af7728be8efd0bacbf49cfedca6704fd27cc6178f27e556e6",
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class ProfileAutomationConfig:
    repo_root: Path
    lance_root: Path
    source_audit: Path
    run_root: Path
    dataset_slug: str
    live: bool = False
    amp: bool = False
    accelerator: str = "NvidiaTeslaT4"
    poll_interval_seconds: int = 60
    poll_timeout_seconds: int = 6 * 60 * 60
    python_executable: Path = Path(sys.executable)


class ProfileAttemptRunner:
    def __init__(
        self,
        config: ProfileAutomationConfig,
        *,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self.config = config
        self.guard = SecurityGuard()
        self.commands = command_runner or CommandRunner(security_guard=self.guard, max_attempts=3)
        self.policy = KaggleExecutionPolicy()

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=self.config.repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def _kaggle(self, *args: str) -> list[str]:
        return [
            str(self.config.python_executable),
            "-c",
            "from kaggle.cli import main; main()",
            *args,
        ]

    def _run(self, attempt_root: Path, step: str, command: list[str]) -> Any:
        return self.commands.run(step, command, attempt_root / "logs" / f"{step}.log")

    def preflight(self) -> dict[str, Any]:
        audit = json.loads(self.config.source_audit.read_text(encoding="utf-8-sig"))
        if audit.get("status") != "research_mvp_source_ready":
            raise ValueError("Research MVP source audit is not ready.")
        if audit.get("counts") != EXPECTED_COUNTS:
            raise ValueError("Research MVP source audit counts do not match exact 36/14/22.")
        if audit.get("source_overlap") or audit.get("pair_overlap"):
            raise ValueError("Research MVP source audit contains leakage.")
        if audit.get("locked_test_materialized") or audit.get("locked_test_scored"):
            raise ValueError("Research MVP source audit indicates locked-test access.")
        required = [
            self.config.lance_root / "tempglitch_train_normal_all_local.lance",
            self.config.lance_root / "tempglitch_validation_normal_all_local.lance",
        ]
        missing = [str(path) for path in required if not path.is_dir()]
        if missing:
            raise FileNotFoundError(f"Missing profile Lance inputs: {missing}")
        return {
            "git_sha": self._git("rev-parse", "HEAD"),
            "branch": self._git("branch", "--show-current"),
            "source_audit": str(self.config.source_audit),
            "counts": audit["counts"],
            "source_overlap": [],
            "pair_overlap": [],
            "authorization": "standing",
            "dataset_visibility": "private",
            "kernel_visibility": "private",
            "locked_test_materialized": False,
            "locked_test_scored": False,
        }

    @staticmethod
    def _status(text: str) -> str:
        lowered = text.lower()
        if "error" in lowered or "failed" in lowered:
            return "error"
        if "complete" in lowered or "success" in lowered:
            return "success"
        if "running" in lowered or "queued" in lowered:
            return "running"
        if lowered.strip() == "ready":
            return "ready"
        if "not found" in lowered or "403" in lowered or "404" in lowered:
            return "missing"
        return "unknown"

    def _dataset_upload(self, attempt_root: Path, package_root: Path, fingerprint: str) -> None:
        self.policy.authorize(
            KaggleAction(
                action="dataset_create_or_version",
                fingerprint=fingerprint,
                visibility="private",
                locked_test_materialized=False,
                locked_test_scored=False,
                redistribution_allowed=False,
            )
        )
        try:
            status = self._run(
                attempt_root,
                "dataset_status",
                self._kaggle("datasets", "status", self.config.dataset_slug),
            )
            exists = self._status(status.stdout) != "missing"
        except AutomationCommandError:
            exists = False
        command = (
            self._kaggle(
                "datasets",
                "version",
                "-p",
                str(package_root / "dataset"),
                "-m",
                f"LeWM profile {fingerprint[:12]}",
                "-r",
                "zip",
            )
            if exists
            else self._kaggle(
                "datasets",
                "create",
                "-p",
                str(package_root / "dataset"),
                "-r",
                "zip",
            )
        )
        self._run(attempt_root, "dataset_upload", command)

    def _wait_dataset(self, attempt_root: Path) -> None:
        deadline = time.monotonic() + self.config.poll_timeout_seconds
        while time.monotonic() < deadline:
            try:
                result = self._run(
                    attempt_root,
                    "dataset_ready",
                    self._kaggle("datasets", "status", self.config.dataset_slug),
                )
                if self._status(result.stdout) == "ready":
                    return
            except AutomationCommandError:
                pass
            time.sleep(self.config.poll_interval_seconds)
        raise AutomationBlockedError("Profile dataset readiness polling timed out.")

    def _download(self, attempt_root: Path, kernel_slug: str) -> Path:
        downloaded = attempt_root / "downloaded"
        downloaded.mkdir(parents=True, exist_ok=True)
        self._run(
            attempt_root,
            "artifact_download",
            self._kaggle("kernels", "output", kernel_slug, "-p", str(downloaded), "-o"),
        )
        candidates = [downloaded, *[path.parent for path in downloaded.rglob("failure.json")]]
        candidates.extend(path.parent for path in downloaded.rglob("profile_metadata.json"))
        return next(
            (
                path
                for path in candidates
                if (path / "failure.json").is_file() or (path / "profile_metadata.json").is_file()
            ),
            downloaded,
        )

    def run_attempt(self, batch_size: int) -> dict[str, Any]:
        preflight = self.preflight()
        preview = prepare_profile_kaggle_package(
            self.config.repo_root,
            self.config.lance_root,
            self.config.run_root / "preview-unused",
            LeWMGPUProfileKaggleConfig(
                dataset_slug=self.config.dataset_slug,
                kernel_slug=f"huynhdieuthanh/lewm-profile-b{batch_size}-preview",
                batch_size=batch_size,
                amp=self.config.amp,
                git_sha=preflight["git_sha"],
                branch=preflight["branch"],
            ),
            dry_run=True,
        )
        fingerprint = preview["profile_fingerprint"]
        kernel_slug = f"huynhdieuthanh/lewm-profile-b{batch_size}-{fingerprint[:10]}"
        attempt_root = self.config.run_root / "attempts" / fingerprint
        if attempt_root.exists():
            raise FileExistsError(f"Immutable profile attempt already exists: {attempt_root}")
        attempt_root.mkdir(parents=True)
        _write_json(attempt_root / "audit" / "preflight_metadata.json", preflight)
        package_root = attempt_root / "package"
        result = prepare_profile_kaggle_package(
            self.config.repo_root,
            self.config.lance_root,
            package_root,
            LeWMGPUProfileKaggleConfig(
                dataset_slug=self.config.dataset_slug,
                kernel_slug=kernel_slug,
                batch_size=batch_size,
                amp=self.config.amp,
                git_sha=preflight["git_sha"],
                branch=preflight["branch"],
            ),
            dry_run=False,
        )
        validate_profile_kaggle_package(package_root)
        summary = {
            "batch_size": batch_size,
            "fingerprint": fingerprint,
            "attempt_root": str(attempt_root),
            "kernel_slug": kernel_slug,
            "status": "dry-run",
        }
        _write_json(attempt_root / "attempt.json", summary)
        if not self.config.live:
            return summary
        self._run(attempt_root, "auth_check", self._kaggle("datasets", "list", "--mine"))
        self._dataset_upload(attempt_root, package_root, fingerprint)
        self._wait_dataset(attempt_root)
        self.policy.authorize(
            KaggleAction(
                action="kernel_push",
                fingerprint=result["kernel_inventory_sha256"],
                visibility="private",
                locked_test_materialized=False,
                locked_test_scored=False,
                redistribution_allowed=True,
            )
        )
        self._run(
            attempt_root,
            "kernel_push",
            self._kaggle(
                "kernels",
                "push",
                "-p",
                str(package_root / "kernel"),
                "--accelerator",
                self.config.accelerator,
            ),
        )
        deadline = time.monotonic() + self.config.poll_timeout_seconds
        while time.monotonic() < deadline:
            status_result = self._run(
                attempt_root,
                "kernel_poll",
                self._kaggle("kernels", "status", kernel_slug),
            )
            status = self._status(status_result.stdout)
            if status == "success":
                artifact_root = self._download(attempt_root, kernel_slug)
                validation = validate_lewm_gpu_profile_artifacts(artifact_root)
                summary.update(
                    {
                        "status": "success",
                        "artifact_root": str(artifact_root),
                        "validation": validation,
                    }
                )
                _write_json(attempt_root / "attempt.json", summary)
                return summary
            if status == "error":
                artifact_root = self._download(attempt_root, kernel_slug)
                failure_path = artifact_root / "failure.json"
                failure = (
                    json.loads(failure_path.read_text(encoding="utf-8-sig"))
                    if failure_path.is_file()
                    else {"classification": "runtime_error", "message": status_result.stdout}
                )
                summary.update(
                    {
                        "status": "failed",
                        "artifact_root": str(artifact_root),
                        "failure": failure,
                    }
                )
                _write_json(attempt_root / "attempt.json", summary)
                return summary
            time.sleep(self.config.poll_interval_seconds)
        raise AutomationBlockedError("Profile kernel polling timed out.")


def run_profile_attempt_ladder(
    config: ProfileAutomationConfig,
    *,
    attempt_runner: Callable[[int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    runner = attempt_runner or ProfileAttemptRunner(config).run_attempt
    attempts = []
    for batch_size in APPROVED_BATCH_LADDER:
        result = runner(batch_size)
        attempts.append(result)
        _write_json(config.run_root / "retry_history.json", {"attempts": attempts})
        if result["status"] in {"success", "dry-run"}:
            final = {
                "status": result["status"],
                "attempted_batch_sizes": [row["batch_size"] for row in attempts],
                "attempts": attempts,
                "successful_artifact_root": result.get("artifact_root"),
            }
            _write_json(config.run_root / "final_result.json", final)
            return final
        if result.get("failure", {}).get("classification") != "cuda_oom":
            break
    final = {
        "status": "failed",
        "attempted_batch_sizes": [row["batch_size"] for row in attempts],
        "attempts": attempts,
        "successful_artifact_root": None,
    }
    _write_json(config.run_root / "final_result.json", final)
    return final
