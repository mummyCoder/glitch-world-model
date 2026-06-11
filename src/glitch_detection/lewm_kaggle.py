from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .kaggle_automation import ApprovalStore, FingerprintBuilder, SecurityGuard

REQUIRED_OUTPUTS = (
    "run_config.json",
    "environment.json",
    "dataset_metadata.json",
    "training_metadata.json",
    "loss_history.json",
    "collapse_diagnostics.json",
    "checkpoint.sha256",
    "validation_scores.csv",
    "validation_metrics.json",
    "protocol_audit.json",
    "resume_metadata.json",
)


@dataclass(frozen=True)
class LeWMKaggleConfig:
    dataset_slug: str
    kernel_slug: str
    dataset_id: str
    action_mode: str
    train_dataset_name: str
    validation_dataset_name: str
    batch_size: int = 4
    max_epochs: int = 1
    image_size: int = 112
    sigreg_projections: int = 128
    accelerator: str = "NvidiaTeslaT4"
    validation_only: bool = True

    def __post_init__(self) -> None:
        if self.action_mode not in {"real", "zero_action"}:
            raise ValueError("Kaggle LeWM action_mode must be real or zero_action.")
        if not self.validation_only:
            raise ValueError(
                "LeWM Kaggle foundation is validation-only until locked-test approval."
            )
        if self.batch_size < 1 or self.max_epochs < 1:
            raise ValueError("LeWM Kaggle batch_size and max_epochs must be positive.")


def quota_allocation(total_hours: float) -> dict[str, float]:
    if total_hours <= 0:
        raise ValueError("Kaggle GPU quota must be positive.")
    return {
        "lewm_dual_primary": total_hours * 0.50,
        "video_baselines": total_hours * 0.25,
        "lewm_ablations": total_hours * 0.15,
        "open_vlm": total_hours * 0.10,
    }


def render_validation_kernel(config: LeWMKaggleConfig) -> str:
    payload = json.dumps(asdict(config), sort_keys=True)
    return f'''"""Generated validation-only LeWM Kaggle entrypoint."""
import json
import platform
import subprocess
import sys
from pathlib import Path

CONFIG = json.loads({payload!r})
OUTPUT = Path("/kaggle/working")
ROOT = Path(__file__).resolve().parent
DATASET = Path("/kaggle/input") / CONFIG["dataset_slug"].split("/")[-1]

if not CONFIG["validation_only"]:
    raise RuntimeError("Locked-test execution is forbidden in this kernel.")

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-r", str(ROOT / "lewm-runtime.txt")
])
sys.path.insert(0, str(ROOT / "src"))

import torch
from glitch_detection.lewm_training import LeWMTrainConfig, train_lewm

(OUTPUT / "run_config.json").write_text(json.dumps(CONFIG, indent=2) + "\\n")
(OUTPUT / "environment.json").write_text(json.dumps({{
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
}}, indent=2) + "\\n")

result = train_lewm(
    DATASET / CONFIG["train_dataset_name"],
    DATASET / CONFIG["validation_dataset_name"],
    OUTPUT,
    LeWMTrainConfig(
        image_size=CONFIG["image_size"],
        batch_size=CONFIG["batch_size"],
        epochs=CONFIG["max_epochs"],
        sigreg_projections=CONFIG["sigreg_projections"],
    ),
    device="cuda",
)
(OUTPUT / "protocol_audit.json").write_text(json.dumps({{
    "validation_only": True,
    "locked_test_materialized": False,
    "locked_test_scored": False,
}}, indent=2) + "\\n")
(OUTPUT / "resume_metadata.json").write_text(json.dumps({{
    "resume_supported": True,
    "config_hash": result["config_hash"],
    "dataset_hashes": result["dataset_hashes"],
    "completed_epoch": result["completed_epoch"],
}}, indent=2) + "\\n")
'''


def prepare_lewm_kaggle_package(
    source_root: Path,
    output_root: Path,
    config: LeWMKaggleConfig,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    required = [
        source_root / config.train_dataset_name,
        source_root / config.validation_dataset_name,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing LeWM Kaggle dataset inputs: {', '.join(missing)}")
    summary: dict[str, Any] = {
        "status": "dry-run only" if dry_run else "package complete",
        "config": asdict(config),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "required_outputs": list(REQUIRED_OUTPUTS),
        "locked_test_included": False,
        "locked_test_scored": False,
    }
    if dry_run:
        return summary
    if output_root.exists():
        raise FileExistsError(f"LeWM Kaggle package already exists: {output_root}")
    dataset_root = output_root / "dataset"
    kernel_root = output_root / "kernel"
    dataset_root.mkdir(parents=True)
    kernel_root.mkdir(parents=True)
    for path in required:
        target = dataset_root / path.name
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)
    (dataset_root / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "id": config.dataset_slug,
                "title": config.dataset_id,
                "licenses": [{"name": "other"}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    kernel_script = kernel_root / "lewm_validation_kernel.py"
    kernel_script.write_text(render_validation_kernel(config), encoding="utf-8")
    repo_root = Path(__file__).resolve().parents[2]
    shutil.copytree(
        repo_root / "src" / "glitch_detection",
        kernel_root / "src" / "glitch_detection",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copy2(repo_root / "requirements" / "lewm-runtime.txt", kernel_root / "lewm-runtime.txt")
    (kernel_root / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": config.kernel_slug,
                "title": config.kernel_slug.split("/", 1)[-1],
                "code_file": kernel_script.name,
                "language": "python",
                "kernel_type": "script",
                "is_private": True,
                "enable_gpu": True,
                "enable_internet": True,
                "dataset_sources": [config.dataset_slug],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    guard = SecurityGuard()
    guard.scan_package(dataset_root, "dataset")
    guard.scan_package(kernel_root, "kernel")
    summary["dataset_inventory_sha256"] = FingerprintBuilder.inventory_sha256(dataset_root)
    summary["kernel_sha256"] = FingerprintBuilder.sha256_file(kernel_script)
    return summary


def request_package_approvals(package_root: Path, approvals_root: Path) -> dict[str, Any]:
    dataset_root = package_root / "dataset"
    kernel_root = package_root / "kernel"
    kernel_script = kernel_root / "lewm_validation_kernel.py"
    SecurityGuard().scan_package(dataset_root, "dataset")
    SecurityGuard().scan_package(kernel_root, "kernel")
    dataset_fingerprint = FingerprintBuilder.inventory_sha256(dataset_root)
    kernel_payload = {
        "dataset_fingerprint": dataset_fingerprint,
        "kernel_inventory_sha256": FingerprintBuilder.inventory_sha256(kernel_root),
        "kernel_script_sha256": FingerprintBuilder.sha256_file(kernel_script),
    }
    kernel_fingerprint = hashlib.sha256(
        json.dumps(kernel_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    store = ApprovalStore(approvals_root)
    dataset_request = store.request("dataset_upload_approval", dataset_fingerprint)
    kernel_request = store.request("kernel_push_approval", kernel_fingerprint)
    return {
        "dataset_upload_approval": dataset_request,
        "kernel_push_approval": kernel_request,
        "live_actions_performed": False,
    }
