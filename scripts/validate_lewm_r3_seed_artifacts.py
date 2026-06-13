from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "cloud_runtime_preflight.json",
    "preflight_passed.json",
    "training_metadata.json",
    "loss_history.json",
    "validation_history.json",
    "collapse_diagnostics.json",
    "checkpoint_weights.pt",
    "weights.pt",
    "best_weights.pt",
    "best_checkpoint_metadata.json",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _finite_numbers(payload: Any, *, label: str, errors: list[str]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            _finite_numbers(value, label=f"{label}.{key}", errors=errors)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _finite_numbers(value, label=f"{label}[{index}]", errors=errors)
    elif isinstance(payload, int | float):
        if not math.isfinite(float(payload)):
            errors.append(f"{label} is not finite")


def validate_artifacts(
    artifact_root: Path,
    *,
    expected_seed: int,
    expected_target_updates: int,
) -> dict[str, Any]:
    errors: list[str] = []
    _assert(artifact_root.is_dir(), f"artifact root does not exist: {artifact_root}", errors)
    for name in REQUIRED_FILES:
        _assert((artifact_root / name).is_file(), f"missing required artifact: {name}", errors)
    if errors:
        raise ValueError("; ".join(errors))

    runtime = _read_json(artifact_root / "cloud_runtime_preflight.json")
    preflight = _read_json(artifact_root / "preflight_passed.json")
    metadata = _read_json(artifact_root / "training_metadata.json")
    loss_history = _read_json(artifact_root / "loss_history.json")
    validation_history = _read_json(artifact_root / "validation_history.json")
    diagnostics = _read_json(artifact_root / "collapse_diagnostics.json")
    best_metadata = _read_json(artifact_root / "best_checkpoint_metadata.json")

    _assert(runtime.get("status") == "passed", "cloud runtime preflight did not pass", errors)
    gpus = runtime.get("gpus", [])
    _assert(bool(gpus), "cloud runtime preflight has no GPU records", errors)
    for gpu in gpus:
        capability = gpu.get("compute_capability", [0, 0])
        _assert(
            int(capability[0]) >= 7,
            f"GPU compute capability below sm_70: {capability}",
            errors,
        )
    _assert(preflight.get("status") == "passed", "preflight_passed.json is not passed", errors)
    _assert(metadata.get("config", {}).get("seed") == expected_seed, "seed mismatch", errors)
    _assert(
        metadata.get("target_optimizer_updates") == expected_target_updates,
        "target optimizer update count mismatch",
        errors,
    )
    updates_completed = int(metadata.get("updates_completed", -1))
    stopped_early = bool(metadata.get("stopped_early"))
    stopped_reason = metadata.get("stopped_early_reason")
    _assert(
        updates_completed == expected_target_updates or (stopped_early and bool(stopped_reason)),
        "updates_completed must reach target or have a documented early-stop reason",
        errors,
    )
    _assert(bool(loss_history), "loss history is empty", errors)
    _assert(bool(validation_history), "validation history is empty", errors)
    _finite_numbers(loss_history, label="loss_history", errors=errors)
    _finite_numbers(validation_history, label="validation_history", errors=errors)
    _assert(
        diagnostics.get("finite") is True, "collapse diagnostics finite flag is not true", errors
    )
    _finite_numbers(diagnostics, label="collapse_diagnostics", errors=errors)
    reload_info = metadata.get("checkpoint_reload", {})
    _assert(
        reload_info.get("weights_reload_verified") is True, "weights reload not verified", errors
    )
    _assert(
        reload_info.get("optimizer_reload_verified") is True,
        "optimizer reload not verified",
        errors,
    )
    _assert(
        reload_info.get("scheduler", {}).get("reload_verified") is True,
        "scheduler reload/absence not verified",
        errors,
    )
    _assert(
        int(reload_info.get("reloaded_global_step", -1)) == updates_completed,
        "reloaded global step mismatch",
        errors,
    )
    _assert(
        best_metadata.get("selection_split") == "validation_normal",
        "best checkpoint was not selected on validation_normal",
        errors,
    )
    _assert(
        metadata.get("validation_buggy_used_for_fit_select") is False,
        "validation-buggy was used for fit/select",
        errors,
    )
    _assert(metadata.get("locked_test_materialized") is False, "locked test materialized", errors)
    _assert(metadata.get("locked_test_scored") is False, "locked test scored", errors)

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "r3_seed42_validated",
        "artifact_root": str(artifact_root),
        "seed": expected_seed,
        "updates_completed": updates_completed,
        "target_optimizer_updates": expected_target_updates,
        "stopped_early": stopped_early,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate R3 seed42 cloud training artifacts.")
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--expected-seed", required=True, type=int)
    parser.add_argument("--expected-target-updates", required=True, type=int)
    args = parser.parse_args(argv)
    result = validate_artifacts(
        args.artifact_root,
        expected_seed=args.expected_seed,
        expected_target_updates=args.expected_target_updates,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
