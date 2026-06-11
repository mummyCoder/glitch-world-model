from __future__ import annotations

import json
import math
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .kaggle_automation import FingerprintBuilder, SecurityGuard
from .lewm_kaggle import validate_kaggle_slug

GATE6_REQUIRED_OUTPUTS = (
    "run_config.json",
    "environment.json",
    "dataset_metadata.json",
    "training_metadata.json",
    "loss_history.json",
    "collapse_diagnostics.json",
    "checkpoint.sha256",
    "protocol_audit.json",
    "best_checkpoint_metadata.json",
    "checkpoint_reload.json",
    "encoding_proof.json",
)


@dataclass(frozen=True)
class Gate6KaggleConfig:
    dataset_slug: str
    kernel_slug: str
    dataset_id: str
    train_dataset_name: str
    validation_dataset_name: str
    buggy_probe_dataset_name: str
    image_size: int = 112
    batch_size: int = 2
    max_epochs: int = 1
    max_train_steps: int = 16
    max_validation_steps: int = 8
    sigreg_projections: int = 128
    seed: int = 42
    package_version: str = "v1"
    action_mode: str = "zero_action"
    accelerator: str = "NvidiaTeslaT4"
    validation_only: bool = True

    def __post_init__(self) -> None:
        validate_kaggle_slug(self.dataset_slug, label="dataset_slug")
        validate_kaggle_slug(self.kernel_slug, label="kernel_slug")
        if self.dataset_slug == self.kernel_slug:
            raise ValueError("Kaggle kernel_slug must differ from dataset_slug.")
        if self.action_mode != "zero_action":
            raise ValueError("Gate 6 pilot supports only zero_action.")
        if not self.validation_only:
            raise ValueError("Gate 6 must remain validation-only.")


def render_gate6_kernel(config: Gate6KaggleConfig) -> str:
    payload = json.dumps(asdict(config), sort_keys=True)
    return f'''"""Generated normal-only Gate 6 LeWM Kaggle entrypoint."""
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG = json.loads({payload!r})
OUTPUT = Path("/kaggle/working")
INPUT_ROOT = Path("/kaggle/input")
PACKAGE_ROOT = Path(__file__).resolve().parent

if not CONFIG["validation_only"]:
    raise RuntimeError("Locked-test execution is forbidden in this kernel.")

def materialize_dataset(name, destination_root):
    directories = sorted(path for path in INPUT_ROOT.rglob(name) if path.is_dir())
    archives = sorted(path for path in INPUT_ROOT.rglob(name + ".zip") if path.is_file())
    if len(directories) + len(archives) != 1:
        raise RuntimeError(
            f"Expected exactly one input directory/archive named {{name}}, "
            f"found directories={{directories}}, archives={{archives}}"
        )
    destination = destination_root / name
    if directories:
        shutil.copytree(directories[0], destination)
    else:
        shutil.unpack_archive(str(archives[0]), str(destination_root))
    if not destination.is_dir():
        raise RuntimeError(f"Archive did not produce expected Lance directory: {{destination}}")
    return destination

code_root = Path("/tmp/gate6_code")
shutil.unpack_archive(str(PACKAGE_ROOT / "glitch_detection_src.zip"), str(code_root))

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "--no-cache-dir",
    "stable-worldmodel==0.1.1",
    "stable-pretraining==0.1.7",
    "transformers==4.57.6",
])
sys.path.insert(0, str(code_root))

import torch
from glitch_detection.lewm_training import LeWMTrainConfig, score_lance_probe, train_lewm

if not torch.cuda.is_available():
    raise RuntimeError("Gate 6 LeWM pilot requires CUDA.")

local = Path("/tmp/gate6_input")
local.mkdir(parents=True, exist_ok=True)
paths = {{}}
for key in ("train_dataset_name", "validation_dataset_name", "buggy_probe_dataset_name"):
    paths[key] = materialize_dataset(CONFIG[key], local)

(OUTPUT / "run_config.json").write_text(json.dumps(CONFIG, indent=2) + "\\n")
(OUTPUT / "environment.json").write_text(json.dumps({{
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "cuda_available": True,
    "cuda_device": torch.cuda.get_device_name(0),
}}, indent=2) + "\\n")

train_config = LeWMTrainConfig(
    image_size=CONFIG["image_size"],
    batch_size=CONFIG["batch_size"],
    epochs=CONFIG["max_epochs"],
    sigreg_projections=CONFIG["sigreg_projections"],
    seed=CONFIG["seed"],
    max_train_steps=CONFIG["max_train_steps"],
    max_validation_steps=CONFIG["max_validation_steps"],
)
result = train_lewm(
    paths["train_dataset_name"],
    paths["validation_dataset_name"],
    OUTPUT,
    train_config,
    device="cuda",
)
normal_proof = score_lance_probe(
    paths["validation_dataset_name"],
    OUTPUT / "best_weights.pt",
    OUTPUT / "config.json",
    device="cuda",
)
buggy_proof = score_lance_probe(
    paths["buggy_probe_dataset_name"],
    OUTPUT / "best_weights.pt",
    OUTPUT / "config.json",
    device="cuda",
)
(OUTPUT / "encoding_proof.json").write_text(json.dumps({{
    "normal_validation": normal_proof,
    "nonlocked_buggy_validation": buggy_proof,
    "performance_claim": False,
}}, indent=2) + "\\n")
(OUTPUT / "dataset_metadata.json").write_text(json.dumps({{
    "dataset_id": CONFIG["dataset_id"],
    "dataset_hashes": result["dataset_hashes"],
    "normal_only_training": True,
    "normal_only_validation": True,
    "buggy_probe_use": "encoding_proof_only",
    "action_mode": "zero_action",
}}, indent=2) + "\\n")
(OUTPUT / "protocol_audit.json").write_text(json.dumps({{
    "validation_only": True,
    "normal_only_training": True,
    "normal_only_validation": True,
    "locked_test_materialized": False,
    "locked_test_scored": False,
}}, indent=2) + "\\n")
'''


def prepare_gate6_kaggle_package(
    source_root: Path,
    output_root: Path,
    config: Gate6KaggleConfig,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    names = (
        config.train_dataset_name,
        config.validation_dataset_name,
        config.buggy_probe_dataset_name,
    )
    inputs = [source_root / name for name in names]
    missing = [str(path) for path in inputs if not path.is_dir()]
    if missing:
        raise FileNotFoundError(f"Missing Gate 6 Lance inputs: {', '.join(missing)}")
    summary: dict[str, Any] = {
        "status": "dry-run only" if dry_run else "package complete",
        "config": asdict(config),
        "required_outputs": list(GATE6_REQUIRED_OUTPUTS),
        "locked_test_included": False,
        "locked_test_scored": False,
    }
    if dry_run:
        return summary
    if output_root.exists():
        raise FileExistsError(f"Gate 6 package already exists: {output_root}")
    dataset_root = output_root / "dataset"
    kernel_root = output_root / "kernel"
    dataset_root.mkdir(parents=True)
    kernel_root.mkdir(parents=True)
    for path in inputs:
        shutil.make_archive(
            str(dataset_root / path.name),
            "zip",
            root_dir=path.parent,
            base_dir=path.name,
        )
    (dataset_root / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "id": config.dataset_slug,
                "title": config.dataset_id,
                "licenses": [{"name": "other"}],
                "package_version": config.package_version,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    kernel_script = kernel_root / "lewm_gate6_kernel.py"
    kernel_script.write_text(render_gate6_kernel(config), encoding="utf-8")
    repo_root = Path(__file__).resolve().parents[2]
    shutil.make_archive(
        str(kernel_root / "glitch_detection_src"),
        "zip",
        root_dir=repo_root / "src",
        base_dir="glitch_detection",
    )
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
    SecurityGuard().scan_package(dataset_root, "dataset")
    SecurityGuard().scan_package(kernel_root, "kernel")
    summary["dataset_inventory_sha256"] = FingerprintBuilder.inventory_sha256(dataset_root)
    summary["kernel_script_sha256"] = FingerprintBuilder.sha256_file(kernel_script)
    return summary


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _finite_numbers(payload: Any) -> bool:
    values: list[float] = []

    def collect(value: Any) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, int | float):
            values.append(float(value))
        elif isinstance(value, dict):
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(payload)
    return bool(values) and all(math.isfinite(value) for value in values)


def validate_gate6_artifacts(root: Path) -> dict[str, Any]:
    missing = [name for name in GATE6_REQUIRED_OUTPUTS if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Gate 6 artifacts: {', '.join(missing)}")
    environment = _load_json(root / "environment.json")
    training = _load_json(root / "training_metadata.json")
    dataset = _load_json(root / "dataset_metadata.json")
    protocol = _load_json(root / "protocol_audit.json")
    history = _load_json(root / "loss_history.json")
    diagnostics = _load_json(root / "collapse_diagnostics.json")
    reload_proof = _load_json(root / "checkpoint_reload.json")
    encoding = _load_json(root / "encoding_proof.json")
    if environment.get("cuda_available") is not True or training.get("device") != "cuda":
        raise ValueError("Gate 6 artifacts do not prove CUDA execution.")
    if not _finite_numbers(history):
        raise ValueError("Gate 6 loss history is empty or non-finite.")
    if diagnostics.get("finite") is not True or not _finite_numbers(diagnostics):
        raise ValueError("Gate 6 collapse diagnostics are invalid.")
    if reload_proof.get("checkpoint_reload_verified") is not True:
        raise ValueError("Gate 6 checkpoint reload was not verified.")
    for key in ("normal_validation", "nonlocked_buggy_validation"):
        if encoding.get(key, {}).get("finite") is not True:
            raise ValueError(f"Gate 6 {key} encoding proof is invalid.")
    if not dataset.get("normal_only_training") or not dataset.get("normal_only_validation"):
        raise ValueError("Gate 6 dataset metadata is not normal-only.")
    if not protocol.get("normal_only_training") or not protocol.get("normal_only_validation"):
        raise ValueError("Gate 6 protocol is not normal-only.")
    if any(
        payload.get(flag)
        for payload in (training, protocol)
        for flag in ("locked_test_materialized", "locked_test_scored")
    ):
        raise ValueError("Gate 6 artifacts indicate locked-test access.")
    checkpoint_hash = (root / "checkpoint.sha256").read_text(encoding="utf-8-sig").strip()
    if checkpoint_hash != training.get("checkpoint_sha256"):
        raise ValueError("Gate 6 checkpoint hash does not match training metadata.")
    return {
        "status": "gate6_passed",
        "device": training["device"],
        "completed_epoch": training["completed_epoch"],
        "checkpoint_sha256": checkpoint_hash,
        "best_weights_sha256": reload_proof["best_weights_sha256"],
        "normal_only_training": True,
        "normal_only_validation": True,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
