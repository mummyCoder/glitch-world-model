# LeWM 500-Update Kaggle GPU Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, validate, and execute a private non-locked Kaggle workflow that trains LeWM for exactly 500 optimizer updates and produces strictly validated engineering-profile artifacts.

**Architecture:** Add a dedicated profile runtime and artifact contract, a private immutable Kaggle package builder, and a resumable live automation layer with immutable OOM attempts. Reuse the repository's existing Kaggle security, command, policy, and orchestrator utilities while keeping Gate 5 and Gate 6 semantics unchanged.

**Tech Stack:** Python 3.10+, PyTorch/LeWM optional runtime, Kaggle CLI, Lance datasets, pytest, Ruff, repository research validators.

---

## File Structure

Create these focused files:

- `src/glitch_detection/lewm_gpu_profile.py`: pure fingerprint/manifest helpers, exact-update
  control loop, CUDA profile runtime, artifact generation, and strict artifact validation.
- `src/glitch_detection/lewm_gpu_profile_kaggle.py`: immutable permitted-project snapshot,
  private Kaggle dataset/kernel package generation, generated kernel, and package validation.
- `src/glitch_detection/lewm_gpu_profile_automation.py`: one-attempt Kaggle handlers plus the
  immutable `8 -> 6 -> 4 -> 2` OOM attempt coordinator.
- `scripts/prepare_lewm_gpu_profile_package.py`: package dry-run/build CLI.
- `scripts/run_lewm_gpu_profile_automation.py`: dry-run/live automation CLI.
- `scripts/validate_lewm_gpu_profile_artifacts.py`: strict downloaded-artifact validator CLI.
- `tests/test_lewm_gpu_profile.py`: core contract and strict artifact tests.
- `tests/test_lewm_gpu_profile_kaggle.py`: snapshot, package, and generated-kernel tests.
- `tests/test_lewm_gpu_profile_automation.py`: idempotency, OOM retry, and evidence-preservation
  tests.
- `docs/research/66_lewm_gpu_profile_results.md`: final engineering-profile report, written only
  after strict artifact validation.

Modify these existing files:

- `docs/research/16_claim_registry.md`: register only the bounded engineering-profile claim after
  validated completion.
- `docs/context/LAST_HANDOFF.md`: record execution result and safety state.
- Generated context files through `scripts/update_context_cache.py --refresh-boot`.

Preserve the existing uncommitted changes in `scripts/run_kaggle_lewm.py`,
`tests/test_run_kaggle_lewm.py`, and `docs/context/LAST_HANDOFF.md`; do not overwrite or fold them
into unrelated implementation commits.

### Task 1: Define The Immutable Profile Contract

**Files:**
- Create: `src/glitch_detection/lewm_gpu_profile.py`
- Create: `tests/test_lewm_gpu_profile.py`

- [ ] **Step 1: Write failing tests for configuration, dataset manifest, and fingerprints**

Add tests that establish the frozen profile values and fingerprint invalidation:

```python
from dataclasses import replace
from pathlib import Path

import pytest

from glitch_detection.lewm_gpu_profile import (
    LeWMGPUProfileConfig,
    build_dataset_manifest,
    build_profile_fingerprint,
)


def test_profile_config_freezes_engineering_only_contract():
    config = LeWMGPUProfileConfig(batch_size=8)

    assert config.optimizer_updates == 500
    assert config.validation_batches == 8
    assert config.seed == 42
    assert config.validation_only is True
    assert config.locked_test_materialized is False
    assert config.locked_test_scored is False


def test_dataset_manifest_is_canonical_and_content_sensitive(tmp_path: Path):
    train = tmp_path / "train.lance"
    validation = tmp_path / "validation.lance"
    train.mkdir()
    validation.mkdir()
    (train / "part.bin").write_bytes(b"train")
    (validation / "part.bin").write_bytes(b"validation")

    first = build_dataset_manifest(train, validation)
    (train / "part.bin").write_bytes(b"changed")
    second = build_dataset_manifest(train, validation)

    assert first["dataset_manifest_hash"] != second["dataset_manifest_hash"]
    assert [row["split"] for row in first["files"]] == ["train_normal", "validation_normal"]


@pytest.mark.parametrize(
    "change",
    [
        {"git_sha": "other"},
        {"dataset_manifest_hash": "other"},
        {"config_hash": "other"},
        {"batch_size": 6},
        {"amp": True},
    ],
)
def test_profile_fingerprint_changes_for_every_immutable_field(change):
    base = {
        "git_sha": "abc",
        "dataset_manifest_hash": "dataset",
        "train_dataset_hash": "train",
        "validation_dataset_hash": "validation",
        "config_hash": "config",
        "batch_size": 8,
        "amp": False,
    }

    assert build_profile_fingerprint(base) != build_profile_fingerprint({**base, **change})
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_lewm_gpu_profile.py -q
```

Expected: collection fails because `glitch_detection.lewm_gpu_profile` does not exist.

- [ ] **Step 3: Implement the immutable contract and canonical hashing**

Create the module with explicit validation and stable JSON hashing:

```python
@dataclass(frozen=True)
class LeWMGPUProfileConfig:
    batch_size: int
    optimizer_updates: int = 500
    validation_batches: int = 8
    seed: int = 42
    image_size: int = 112
    amp: bool = False
    num_workers: int = 2
    pin_memory: bool = True
    gradient_clip_norm: float | None = None
    validation_only: bool = True
    locked_test_materialized: bool = False
    locked_test_scored: bool = False
    evidence_class: str = "engineering-profile-only"

    def __post_init__(self) -> None:
        if self.batch_size not in {8, 6, 4, 2}:
            raise ValueError("Profile batch_size must follow the approved 8, 6, 4, 2 ladder.")
        if self.optimizer_updates != 500 or self.validation_batches != 8:
            raise ValueError("Profile requires exactly 500 updates and eight validation batches.")
        if not self.validation_only or self.locked_test_materialized or self.locked_test_scored:
            raise ValueError("Profile must remain validation-only with locked test disabled.")


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_profile_fingerprint(payload: dict[str, Any]) -> str:
    required = {
        "git_sha", "dataset_manifest_hash", "train_dataset_hash",
        "validation_dataset_hash", "config_hash", "batch_size", "amp",
    }
    if set(payload) != required:
        raise ValueError(f"Profile fingerprint payload must contain exactly {sorted(required)}.")
    return canonical_sha256(payload)
```

Implement `build_dataset_manifest()` as a sorted list of relative path, size, SHA-256, and split,
then hash the complete list.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_lewm_gpu_profile.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the contract**

```powershell
git add src/glitch_detection/lewm_gpu_profile.py tests/test_lewm_gpu_profile.py
git commit -m "feat(profile): define immutable LeWM GPU profile contract"
```

### Task 2: Implement Exact-Update Training And Reload Verification

**Files:**
- Modify: `src/glitch_detection/lewm_gpu_profile.py`
- Modify: `tests/test_lewm_gpu_profile.py`

- [ ] **Step 1: Write failing control-loop tests**

Add a pure injected-loop test so exact-update behavior is testable without the heavy LeWM runtime:

```python
from glitch_detection.lewm_gpu_profile import run_exact_updates


def test_exact_update_loop_stops_at_500_without_overrun():
    calls = []

    result = run_exact_updates(
        target_updates=500,
        train_step=lambda update: calls.append(update) or {"loss": 1.0 / update},
    )

    assert calls == list(range(1, 501))
    assert result["updates_completed"] == 500
    assert result["history"][-1]["update"] == 500


def test_exact_update_loop_rejects_non_finite_loss():
    with pytest.raises(ValueError, match="non-finite"):
        run_exact_updates(target_updates=500, train_step=lambda _update: {"loss": float("nan")})
```

Add tests for a checkpoint payload containing `model`, `optimizer`, explicit scheduler presence,
`global_step=500`, config hash, and dataset hashes. Add a reload test that rejects step `499`.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_lewm_gpu_profile.py -q`

Expected: FAIL because exact-update and checkpoint helpers are missing.

- [ ] **Step 3: Implement pure exact-update and checkpoint helpers**

Add:

```python
def run_exact_updates(
    *,
    target_updates: int,
    train_step: Callable[[int], dict[str, float]],
    on_update: Callable[[int], None] | None = None,
) -> dict[str, Any]:
    history = []
    started = time.perf_counter()
    for update in range(1, target_updates + 1):
        metrics = {"update": update, **train_step(update)}
        if not all(math.isfinite(float(value)) for key, value in metrics.items() if key != "update"):
            raise ValueError(f"Profile update {update} produced non-finite metrics.")
        history.append(metrics)
        if on_update is not None:
            on_update(update)
    elapsed = time.perf_counter() - started
    return {
        "updates_completed": len(history),
        "history": history,
        "training_runtime_seconds": elapsed,
        "updates_per_second": len(history) / elapsed,
    }
```

Add `build_checkpoint_payload(...)` and `verify_reloaded_checkpoint(...)`. Scheduler absence must
be represented as `{"present": False, "reload_verified": True}` rather than omitted.

- [ ] **Step 4: Implement `run_lewm_gpu_profile()`**

Use the existing internal LeWM model/data helpers, but keep the profile loop separate from
`train_lewm()`:

```python
def run_lewm_gpu_profile(
    train_path: Path,
    validation_path: Path,
    output_root: Path,
    config: LeWMGPUProfileConfig,
    *,
    preflight_metadata: dict[str, Any],
) -> dict[str, Any]:
    # Require CUDA, build model/optimizer/scaler, cycle train-normal batches,
    # call run_exact_updates(target_updates=500), save checkpoint,
    # instantiate fresh model/optimizer, reload all states, then run exactly
    # eight validation-normal batches with optimizer disabled.
```

Reset CUDA peak-memory stats before training. Sample `torch.cuda.memory_allocated()` after every
update for average VRAM and use `torch.cuda.max_memory_allocated()` for peak VRAM. Record UTC
timestamps around training, checkpoint save, and reload. Ensure validation runs under
`torch.no_grad()` and does not change `global_step`.

- [ ] **Step 5: Run core and existing training tests**

Run:

```powershell
python -m pytest tests/test_lewm_gpu_profile.py tests/test_lewm_training.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit exact training behavior**

```powershell
git add src/glitch_detection/lewm_gpu_profile.py tests/test_lewm_gpu_profile.py
git commit -m "feat(profile): run exact LeWM optimizer update budget"
```

### Task 3: Generate Required Artifacts And Strictly Validate Them

**Files:**
- Modify: `src/glitch_detection/lewm_gpu_profile.py`
- Modify: `tests/test_lewm_gpu_profile.py`
- Create: `scripts/validate_lewm_gpu_profile_artifacts.py`

- [ ] **Step 1: Write failing artifact-schema and rejection tests**

Create a `_write_valid_profile_artifacts()` test helper that writes:

```text
PROFILE_REPORT.md
profile_metadata.json
artifact_manifest.json
environment_snapshot.json
checkpoint_hashes.json
retry_history.json
checkpoint.pt
profile.log
```

Test acceptance, then parameterize rejection for:

- updates completed not equal to 500;
- validation batches not equal to 8;
- CUDA false;
- checkpoint/reload/global-step failure;
- missing throughput or peak VRAM;
- hash mismatch;
- `validation_buggy`, `locked_test`, `AUROC`, or `AUPRC` keys/claims.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_lewm_gpu_profile.py -q`

Expected: FAIL because artifact writers and validator are missing.

- [ ] **Step 3: Implement artifact generation**

Add constants and writers:

```python
PROFILE_REQUIRED_REMOTE_ARTIFACTS = (
    "PROFILE_REPORT.md",
    "profile_metadata.json",
    "artifact_manifest.json",
    "environment_snapshot.json",
    "checkpoint_hashes.json",
    "retry_history.json",
    "checkpoint.pt",
    "profile.log",
)
```

`artifact_manifest.json` hashes every remote artifact except itself and the local-only
`validator_report.json`. The strict local validator writes `validator_report.json`, then writes
`validated_artifact_manifest.json` hashing the validator report and original manifest without
creating a self-hashing cycle.

- [ ] **Step 4: Implement strict validator and CLI**

Implement:

```python
def validate_lewm_gpu_profile_artifacts(root: Path) -> dict[str, Any]:
    # Load required files, verify manifest hashes and immutable fingerprint,
    # reject forbidden keys/claims recursively, require CUDA and exact counts,
    # verify checkpoint/reload states, finite losses, runtime/VRAM fields,
    # and false validation-buggy/locked-test flags.
```

The CLI accepts `--artifacts-root` and `--output`; it must write
`validator_report.json` only after validation succeeds.

- [ ] **Step 5: Run validator tests and CLI help**

Run:

```powershell
python -m pytest tests/test_lewm_gpu_profile.py -q
python scripts/validate_lewm_gpu_profile_artifacts.py --help
```

Expected: PASS and help exits zero.

- [ ] **Step 6: Commit artifact integrity**

```powershell
git add src/glitch_detection/lewm_gpu_profile.py tests/test_lewm_gpu_profile.py scripts/validate_lewm_gpu_profile_artifacts.py
git commit -m "feat(profile): validate LeWM GPU profile artifacts"
```

### Task 4: Build The Immutable Private Kaggle Package

**Files:**
- Create: `src/glitch_detection/lewm_gpu_profile_kaggle.py`
- Create: `tests/test_lewm_gpu_profile_kaggle.py`
- Create: `scripts/prepare_lewm_gpu_profile_package.py`

- [ ] **Step 1: Write failing snapshot and package tests**

Test that the snapshot uses only permitted Git-tracked files and excludes `.git`, outputs,
credentials, caches, checkpoints, `external/`, data, and locked-test paths. Test the dataset
package contains only:

```text
train-normal.lance.zip
validation-normal.lance.zip
project_snapshot.zip
project_snapshot_manifest.json
profile_input_metadata.json
dataset-metadata.json
```

Test both dataset and kernel metadata are private and that no validation-buggy archive appears.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_lewm_gpu_profile_kaggle.py -q`

Expected: collection fails because package module is missing.

- [ ] **Step 3: Implement deterministic permitted-project snapshot**

Add a tracked-file snapshot builder:

```python
SNAPSHOT_EXCLUDED_PREFIXES = (
    ".git/", "data/", "outputs/", "external/", ".venv/", "venv/",
)


def build_permitted_project_snapshot(
    repo_root: Path,
    tracked_paths: list[str],
) -> tuple[bytes, dict[str, Any]]:
    # Reject forbidden/locked-test/credential/checkpoint paths,
    # scan included files with SecurityGuard.scan_tracked_files(),
    # write deterministic ZIP timestamps, and return archive plus manifest.
```

Include source, scripts, configs, requirements, packaging metadata, and relevant docs needed to
reproduce the run. The snapshot manifest records every included/excluded path and reason.

- [ ] **Step 4: Implement package config and preparation**

Define `LeWMGPUProfileKaggleConfig` with private-only validation. Prepare the two Lance archives,
project snapshot, metadata, generated kernel, and package audit. Reuse `SecurityGuard`,
`FingerprintBuilder`, and `validate_kaggle_slug`.

The package validator must reject:

- non-private metadata;
- unexpected dataset archives/files;
- validation-buggy or locked-test names;
- missing project snapshot manifest;
- mismatched snapshot/archive hashes;
- auxiliary kernel files;
- any credentials or Windows absolute paths.

- [ ] **Step 5: Implement package CLI**

Support:

```powershell
python scripts/prepare_lewm_gpu_profile_package.py `
  --repo-root . `
  --source-root outputs/research_mvp/datasets `
  --output-root outputs/lewm_gpu_profile/attempts/b8/package `
  --dataset-slug huynhdieuthanh/lewm-research-mvp-profile-private `
  --kernel-slug huynhdieuthanh/lewm-research-mvp-profile-b8 `
  --batch-size 8 `
  --dry-run
```

The CLI prints config, dataset manifest hash, profile fingerprint, package inventories, exact
training command, and locked-test false flags.

- [ ] **Step 6: Run package tests**

Run:

```powershell
python -m pytest tests/test_lewm_gpu_profile_kaggle.py -q
python scripts/prepare_lewm_gpu_profile_package.py --help
```

Expected: PASS.

- [ ] **Step 7: Commit private packaging**

```powershell
git add src/glitch_detection/lewm_gpu_profile_kaggle.py tests/test_lewm_gpu_profile_kaggle.py scripts/prepare_lewm_gpu_profile_package.py
git commit -m "feat(profile): package private immutable Kaggle profile"
```

### Task 5: Render And Bootstrap The Fail-Closed Kaggle Kernel

**Files:**
- Modify: `src/glitch_detection/lewm_gpu_profile_kaggle.py`
- Modify: `tests/test_lewm_gpu_profile_kaggle.py`

- [ ] **Step 1: Write failing generated-kernel tests**

Assert generated code:

- extracts `project_snapshot.zip` instead of cloning mutable `main`;
- locates exactly train-normal and validation-normal Lance inputs;
- writes pre-run metadata before calling `run_lewm_gpu_profile`;
- requires CUDA;
- passes exact `optimizer_updates=500`, `validation_batches=8`, batch size, seed, and AMP;
- contains no scorer, AUROC, AUPRC, validation-buggy, or locked-test access;
- supports `LEWM_PROFILE_BOOTSTRAP_ONLY=1`.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_lewm_gpu_profile_kaggle.py -q`

Expected: FAIL on missing kernel behavior.

- [ ] **Step 3: Implement generated kernel**

The generated entrypoint must:

```python
if CONFIG["locked_test_materialized"] or CONFIG["locked_test_scored"]:
    raise RuntimeError("Locked-test execution is forbidden.")
if CONFIG["optimizer_updates"] != 500 or CONFIG["validation_batches"] != 8:
    raise RuntimeError("Profile contract changed.")
```

Extract the immutable snapshot to `/tmp/glitch-world-model`, install only pinned LeWM runtime
requirements, materialize the two Lance datasets under `/tmp/lewm_profile_input`, collect
`environment_snapshot.json`, validate the profile fingerprint, then call
`run_lewm_gpu_profile(...)`.

On exception, write a sanitized `failure.json`, traceback log, partial metadata, and artifact
manifest before re-raising.

- [ ] **Step 4: Add Kaggle-like bootstrap test**

Run the generated script locally with `LEWM_PROFILE_BOOTSTRAP_ONLY=1`, assert zero exit and
`LEWM_PROFILE_BOOTSTRAP_OK`.

- [ ] **Step 5: Run generated-kernel tests**

Run: `python -m pytest tests/test_lewm_gpu_profile_kaggle.py -q`

Expected: PASS.

- [ ] **Step 6: Commit the kernel**

```powershell
git add src/glitch_detection/lewm_gpu_profile_kaggle.py tests/test_lewm_gpu_profile_kaggle.py
git commit -m "feat(profile): render fail-closed Kaggle profile kernel"
```

### Task 6: Add Resumable Live Automation And Immutable OOM Attempts

**Files:**
- Create: `src/glitch_detection/lewm_gpu_profile_automation.py`
- Create: `tests/test_lewm_gpu_profile_automation.py`
- Create: `scripts/run_lewm_gpu_profile_automation.py`

- [ ] **Step 1: Write failing one-attempt automation tests**

Use a fake `CommandRunner` and test:

- preflight records Git SHA/branch/config/source audit and blocks on any mismatch;
- private dataset create/version never adds `--public`;
- each kernel fingerprint pushes at most once;
- error status downloads outputs/logs before blocking;
- artifact validation runs only after download;
- run roots include immutable fingerprint and are never reused.

- [ ] **Step 2: Write failing OOM coordinator tests**

Add:

```python
def test_oom_coordinator_tries_8_6_4_2_and_preserves_attempts(tmp_path):
    outcomes = {8: "oom", 6: "oom", 4: "success"}
    result = run_profile_attempt_ladder(tmp_path, outcomes=outcomes)

    assert result["attempted_batch_sizes"] == [8, 6, 4]
    assert len({row["fingerprint"] for row in result["attempts"]}) == 3
    assert all(Path(row["attempt_root"]).is_dir() for row in result["attempts"])
```

Test that non-OOM runtime failures stop immediately and do not advance the ladder.

- [ ] **Step 3: Run tests and verify failure**

Run: `python -m pytest tests/test_lewm_gpu_profile_automation.py -q`

Expected: collection fails because automation module is missing.

- [ ] **Step 4: Implement one-attempt handlers**

Reuse `KaggleOrchestrator`, `CommandRunner`, `KaggleExecutionPolicy`, and `SecurityGuard`. Define
steps:

```python
PROFILE_AUTOMATION_STEPS = (
    "preflight",
    "package_prepare",
    "package_validate",
    "dataset_fingerprint",
    "dataset_create_or_version",
    "dataset_ready",
    "kernel_fingerprint",
    "kernel_validate",
    "kernel_push_once",
    "kernel_poll",
    "artifact_download",
    "artifact_validate",
    "complete",
)
```

Preflight must run the research source audit and compare exact `36/14/22` counts and the frozen
Lance hashes from `configs/lewm_research_mvp.yaml`. It must record
`audit/preflight_metadata.json` before package preparation.

- [ ] **Step 5: Implement immutable OOM coordinator**

Implement an outer coordinator that creates a new attempt root and kernel slug per profile
fingerprint. It may advance only when downloaded `failure.json` classifies the prior failure as
CUDA OOM. It appends, never rewrites, `retry_history.json`; each attempt retains logs, traceback,
metadata, package audit, state, and downloaded outputs.

- [ ] **Step 6: Implement automation CLI**

The CLI supports `--dry-run` and `--live`, defaults to batch ladder `8,6,4,2`, requires explicit
paths to the research source audit inputs and Lance root, and prints the final attempt/fingerprint
history without credential values. It also writes `outputs/lewm_gpu_profile/final_result.json`
with `successful_artifact_root` after a validated successful attempt.

- [ ] **Step 7: Run automation tests**

Run:

```powershell
python -m pytest tests/test_lewm_gpu_profile_automation.py tests/test_kaggle_automation_orchestrator.py -q
python scripts/run_lewm_gpu_profile_automation.py --help
```

Expected: PASS.

- [ ] **Step 8: Commit automation**

```powershell
git add src/glitch_detection/lewm_gpu_profile_automation.py tests/test_lewm_gpu_profile_automation.py scripts/run_lewm_gpu_profile_automation.py
git commit -m "feat(profile): automate immutable Kaggle GPU attempts"
```

### Task 7: Run Local Dry-Run Preparation And Full Repository Verification

**Files:**
- Modify only if validators expose a real defect in the new workflow.

- [ ] **Step 1: Inspect worktree and current source paths**

Run:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
python scripts/run_lewm_gpu_profile_automation.py --help
```

Expected: branch/SHA recorded; existing unrelated/user changes preserved.

- [ ] **Step 2: Run the source audit and inspect Lance inventories**

Use the exact metadata, split, video-root, and Lance paths recorded by the current research MVP
handoff/source preparation. Run:

```powershell
python scripts/audit_lewm_research_source.py --metadata data/raw/tempglitch_phase3b/metadata.csv --split outputs/gate3/tempglitch/split.csv --video-root data/raw/tempglitch_phase3b --output outputs/lewm_gpu_profile/preflight/research_source_audit.json
python scripts/inspect_lewm_dataset.py --dataset outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance --output outputs/lewm_gpu_profile/preflight/train_inspection.json
python scripts/inspect_lewm_dataset.py --dataset outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance --output outputs/lewm_gpu_profile/preflight/validation_normal_inspection.json
```

Expected: exact `36/14/22` audit, `34,844` train windows, `12,825` validation-normal windows,
zero overlap, and locked-test false.

- [ ] **Step 3: Run dry-run automation for batch size 8**

Run:

```powershell
python scripts/run_lewm_gpu_profile_automation.py `
  --dry-run `
  --lance-root outputs/research_mvp/datasets `
  --source-audit outputs/lewm_gpu_profile/preflight/research_source_audit.json `
  --run-root outputs/lewm_gpu_profile `
  --dataset-slug huynhdieuthanh/lewm-research-mvp-profile-private
```

Expected: package/security/preflight validation passes and execution stops before live dataset
upload/kernel push. Record the exact profile fingerprint and command.

- [ ] **Step 4: Run focused and full checks**

Run:

```powershell
python -m pytest tests/test_lewm_gpu_profile.py tests/test_lewm_gpu_profile_kaggle.py tests/test_lewm_gpu_profile_automation.py -q
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
pre-commit run --all-files
git diff --check
git status --short
```

Expected: all available checks pass. Document unavailable `pre-commit` or optional-runtime checks
honestly.

### Task 8: Execute Live Private Kaggle Profile And Validate Downloads

**Files:**
- Generated ignored outputs only until validation succeeds.

- [ ] **Step 1: Re-run all preflight checks immediately before live execution**

Run full checks from Task 7 and verify:

- current Git SHA equals the packaged SHA;
- no uncommitted profile implementation change affects the package;
- package and kernel are private;
- no validation-buggy or locked-test input exists;
- credentials are outside the repository;
- generated outputs/checkpoints remain ignored and untracked.

Expected: every pre-run check passes. Otherwise stop before training.

- [ ] **Step 2: Launch live attempt ladder**

Run:

```powershell
python scripts/run_lewm_gpu_profile_automation.py `
  --live `
  --lance-root outputs/research_mvp/datasets `
  --source-audit outputs/lewm_gpu_profile/preflight/research_source_audit.json `
  --run-root outputs/lewm_gpu_profile `
  --dataset-slug huynhdieuthanh/lewm-research-mvp-profile-private
```

Expected: batch 8 succeeds, or only CUDA OOM advances to 6, then 4, then 2. Every attempt gets a
unique fingerprint/root and preserves evidence. No 15,000-update training is launched.

- [ ] **Step 3: Strictly validate downloaded successful artifacts**

Run:

```powershell
$successful = (Get-Content -Raw outputs/lewm_gpu_profile/final_result.json | ConvertFrom-Json).successful_artifact_root
python scripts/validate_lewm_gpu_profile_artifacts.py `
  --artifacts-root $successful `
  --output (Join-Path $successful 'validator_report.json')
```

Expected: `status=lewm_gpu_profile_validated`, exactly 500 updates, eight validation-normal
batches, CUDA true, checkpoint states reloaded, hashes valid, locked test false, and no
performance metrics/claims.

- [ ] **Step 4: Record command and evidence inventory**

Run:

```powershell
git status --short
git ls-files outputs data
```

Expected: no generated output, Lance dataset, checkpoint, cache, or credential is tracked.

### Task 9: Write The Bounded Result Report And Synchronize Context

**Files:**
- Create: `docs/research/66_lewm_gpu_profile_results.md`
- Modify: `docs/research/16_claim_registry.md`
- Modify: `docs/context/LAST_HANDOFF.md`
- Modify generated context files through `scripts/update_context_cache.py --refresh-boot`

- [ ] **Step 1: Write the result report from validated artifacts only**

The report must include:

```markdown
# LeWM 500-Update Kaggle GPU Profile Results

Evidence class: engineering-profile-only
Paper-performance claim: forbidden
Locked test: closed, unmaterialized, unscored
Validation-buggy: not packaged or used

## Immutable Inputs
## Kaggle Run Status
## Runtime / VRAM / Throughput
## Checkpoint Validation
## Retry History
## Artifact Validation
## Feasibility Recommendation
## Limitations
```

Copy exact hashes, timestamps, runtime, updates/sec, peak/average VRAM, effective batch size, AMP
state, checkpoint reload results, and validator status from checked artifacts. Do not include
AUROC, AUPRC, detection claims, or scientific conclusions.

- [ ] **Step 2: Register only the bounded engineering claim**

Add a claim-registry entry equivalent to:

```text
The private non-locked research MVP Kaggle profile completed exactly 500 CUDA optimizer updates
and passed strict checkpoint/reload and artifact validation.
```

Mark it `verified`, `engineering-profile-only`, and explicitly forbid performance interpretation.

- [ ] **Step 3: Update handoff and context cache**

Run:

```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
```

Record the successful batch size or complete OOM ladder failure, safe claim boundary, locked-test
status, artifact safety, unresolved risks, and the next gate: freeze the feasible main-run
schedule without launching it.

- [ ] **Step 4: Run final required checks**

Run:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
pre-commit run --all-files
git diff --check
git status --short
git branch --show-current
git rev-parse HEAD
```

Expected: all available checks pass; generated artifacts and credentials remain untracked.

- [ ] **Step 5: Commit validated documentation and context**

```powershell
git add docs/research/66_lewm_gpu_profile_results.md docs/research/16_claim_registry.md docs/context
git commit -m "docs(profile): record validated 500-update GPU profile"
```

## Completion Gate

The implementation is complete only when:

- one immutable attempt passes the strict local validator, or all approved OOM attempts preserve
  complete failure evidence;
- training completed exactly 500 total optimizer updates with no post-reload update;
- checkpoint weights, optimizer, optional scheduler, and global step reload checks pass;
- eight validation-normal verification batches complete with finite outputs;
- required runtime, VRAM, throughput, timestamps, hashes, retry history, and manifests exist;
- validation-buggy and locked test remain unused;
- no AUROC, AUPRC, paper claim, or scientific-performance conclusion is produced;
- no raw data, Lance dataset, output, checkpoint, cache, or credential is tracked;
- repository-required checks pass or unavailable checks are reported honestly.
