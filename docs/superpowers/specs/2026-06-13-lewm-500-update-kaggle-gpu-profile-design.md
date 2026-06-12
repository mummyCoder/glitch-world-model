# LeWM 500-Update Non-Locked Kaggle GPU Profile Design

## Purpose And Evidence Boundary

Build and execute a private Kaggle GPU workflow that profiles the research MVP LeWM source for
exactly 500 total optimizer updates. The run measures engineering feasibility: CUDA execution,
runtime, throughput, VRAM, checkpoint persistence, and reload correctness.

This is an `engineering-profile-only` run. It must not calculate or report AUROC, AUPRC,
detection performance, scientific conclusions, or paper-facing model-performance claims.
Validation-buggy and locked-test data must not be packaged, materialized, read, or scored.

## Approved Decisions

- Use a dedicated research-profile workflow rather than changing the meaning of the existing
  Gate 5 CUDA/resume smoke.
- Run exactly 500 total optimizer updates, then stop training.
- Save and reload the final checkpoint without performing further optimizer updates.
- Run exactly eight validation-normal batches after reload for pipeline verification only.
- Start with batch size 8 and retry OOM failures using `8 -> 6 -> 4 -> 2`.
- Keep every Kaggle dataset and kernel private.
- Package an immutable project snapshot sufficient for reproduction, subject to security,
  licensing, artifact, and locked-test exclusions.
- Use seed 42 and the frozen profile settings unless a later approved design revision changes
  them.

## Architecture

The profile is a separate workflow with focused components:

- A profile configuration defines the immutable research controls, including optimizer-update
  budget, seed, batch size, AMP state, image size, validation verification batch count, dataset
  names, and locked-test false flags.
- A package builder creates a private Kaggle dataset/kernel package containing the permitted
  project snapshot, train-normal Lance data, and validation-normal Lance data.
- A preflight validator checks repository state, source audit, package inventory, security,
  licenses, required hashes, configuration, and locked-test exclusions before training can start.
- A generated Kaggle kernel records environment metadata, runs the exact 500-update profile,
  measures runtime and memory, saves and reloads the checkpoint, verifies eight
  validation-normal batches, and writes required artifacts.
- A live-action orchestrator uploads or versions the private dataset, pushes one private GPU
  kernel per immutable fingerprint, polls it, downloads artifacts, and preserves each attempt.
- A strict local artifact validator decides whether the downloaded run is trustworthy.

The workflow must reuse existing Kaggle automation, security scanning, fingerprint, training,
and package-validation utilities where their contracts fit. Gate 5 artifacts and claims remain
unchanged.

## Project Snapshot Policy

The private package includes the complete permitted project snapshot needed to reproduce the
profile from the verified Git SHA. It must not depend on cloning a mutable `main` branch during
the Kaggle run.

The snapshot excludes:

- `.git`, credentials, tokens, `.env`, and `kaggle.json`;
- locked-test data, metadata that materializes locked-test inputs, or locked-test outputs;
- validation-buggy data;
- raw or processed data outside the approved train-normal and validation-normal Lance inputs;
- existing outputs, checkpoints, caches, virtual environments, and temporary files;
- files lacking redistribution permission or unnecessary external repositories.

The package builder records included and excluded inventories. Security and package validators
must pass before any live Kaggle action.

## Pre-Run Verification

Before training starts, the workflow records and validates:

- Git SHA and branch name;
- research MVP source audit matching 36 train-normal, 14 validation-normal, and 22
  validation-buggy episodes, while packaging only train-normal and validation-normal;
- `dataset_manifest_hash`, computed from a canonical sorted manifest of relative paths, sizes,
  and SHA-256 values for the approved train-normal and validation-normal Lance inputs;
- train-normal and validation-normal dataset hashes;
- profile config hash;
- Python, CUDA, PyTorch, and Kaggle runtime information;
- private dataset/kernel settings;
- CUDA requirement;
- `validation_only=true`;
- `locked_test_materialized=false` and `locked_test_scored=false`;
- absence of validation-buggy and locked-test inputs from the package;
- absence of credentials and prohibited generated artifacts.

The recorded values are stored in machine-readable metadata. Any failed pre-run check stops the
kernel before training and produces failure evidence.

## Immutable Fingerprint

Every attempt has one unique immutable fingerprint. At minimum, its canonical payload contains:

- Git SHA;
- `dataset_manifest_hash`;
- train-normal and validation-normal dataset hashes;
- config hash;
- batch size;
- AMP state.

The fingerprint may also include the package inventory and kernel code hashes for stronger
idempotency. Any payload change creates a new fingerprint. A fingerprint is pushed at most once;
an existing remote run is polled or downloaded rather than resubmitted.

Attempt directories and remote slugs must identify the fingerprint. No retry may overwrite a
previous attempt.

## Exact Training And Validation Flow

The Kaggle kernel follows this fail-closed sequence:

1. Write pre-run metadata and validate all preflight conditions.
2. Require CUDA, initialize deterministic seed 42, and initialize memory measurements.
3. Train on train-normal only until the global optimizer-update count is exactly 500.
4. Reject overrun, underrun, non-finite loss, or use of prohibited data.
5. Save a final checkpoint and record its timestamp and hash.
6. Reload model weights, optimizer state, scheduler state when present, and global step.
7. Verify the reloaded global step is exactly 500 and all required states reload successfully.
8. Run exactly eight validation-normal batches with no optimizer updates.
9. Verify validation pipeline outputs and losses are finite.
10. Write reports and the artifact integrity manifest.

The profile does not select a checkpoint from validation-normal. The eight batches are only a
reload and inference pipeline check.

## Runtime And Memory Logging

Each attempt records:

- wall-clock runtime;
- training start and end timestamps;
- optimizer updates completed;
- updates per second;
- peak CUDA VRAM;
- average CUDA VRAM when supported by periodic sampling;
- configured and effective batch size;
- AMP state;
- image size, gradient accumulation, workers, pinned memory, and gradient clipping;
- checkpoint save timestamp;
- checkpoint reload timestamp;
- finite-loss status;
- checkpoint save and reload results.

Logs must be sanitized before persistence. Runtime failures retain the sanitized traceback.

## Checkpoint Validation

Checkpoint validation must prove:

- model weights reload successfully;
- optimizer state reloads successfully;
- scheduler state reloads successfully when a scheduler is configured or present;
- absence of a scheduler is explicitly recorded when none is used;
- reloaded global optimizer step equals 500;
- config and dataset hashes match the active attempt;
- the checkpoint file hash matches its recorded hash;
- eight validation-normal batches complete with finite outputs after reload.

Reload validation must not advance training or mutate the saved checkpoint.

## OOM Retry Policy

OOM handling uses separate immutable attempts in the order `8 -> 6 -> 4 -> 2`. A retry is
allowed only after the prior attempt is recorded as an OOM failure and a new fingerprint is
created for the changed batch size.

Every failed attempt preserves:

- fingerprint and canonical fingerprint payload;
- logs and sanitized traceback;
- pre-run metadata;
- partial profile metadata when available;
- failure classification and timestamps;
- package and remote run identifiers.

OOM retries must not silently alter AMP, image size, model shape, or other profile controls.
Changes beyond the approved batch-size ladder require a new design decision.

## Required Artifacts

Every successful attempt must provide:

- `PROFILE_REPORT.md`;
- `profile_metadata.json`;
- `artifact_manifest.json`;
- `environment_snapshot.json`;
- `checkpoint_hashes.json`;
- `retry_history.json`;
- `validator_report.json`;
- final checkpoint and the underlying sanitized logs needed to validate the report.

`PROFILE_REPORT.md` states `engineering-profile-only`, the exact 500-update scope, retry history,
feasibility recommendation, and explicit non-use of validation-buggy and locked test.

`artifact_manifest.json` records cryptographic hashes for the checkpoint, metadata, logs,
profile report, environment snapshot, checkpoint hashes, retry history, and validator report.
The validator report itself may be added to a final local manifest after validation to avoid a
self-hashing cycle.

## Strict Artifact Validation

Downloaded artifacts are untrusted until the local strict validator passes. It rejects:

- missing required artifacts or hash mismatches;
- missing or inconsistent Git, dataset, config, package, or fingerprint metadata;
- a non-private package or unexpected input inventory;
- CUDA unavailable or a non-CUDA training device;
- optimizer updates other than exactly 500;
- further optimizer updates during reload or validation verification;
- failed weights, optimizer, scheduler-if-present, or step-count reload checks;
- checkpoint hash mismatch;
- non-finite losses or validation verification outputs;
- absent runtime, throughput, or peak-VRAM fields;
- overwritten or incomplete retry evidence;
- any validation-buggy or locked-test access;
- AUROC, AUPRC, detection-performance, or paper-claim fields.

Only a passing validator permits the profile result to update repository research documentation.

## Testing Strategy

Focused tests cover:

- canonical fingerprint creation and invalidation on Git SHA, dataset hash, config hash, batch
  size, or AMP changes;
- package inclusion/exclusion and security scans;
- fail-closed preflight behavior;
- exact 500-update stopping with no overrun;
- save/reload of model, optimizer, optional scheduler, and global step;
- exactly eight validation-normal verification batches with no optimizer updates;
- runtime and VRAM metadata schemas;
- OOM ladder sequencing, immutable attempt directories, and evidence preservation;
- artifact hash generation and strict validator rejection cases;
- prohibition of validation-buggy, locked-test, AUROC, AUPRC, and performance claims.

Before live execution, run the repository-required test, Ruff, research-release, claim-registry,
doctor, context-cache, pre-commit, diff, tracked-artifact, and credential-safety checks.

## Execution And Completion Criteria

Live execution may proceed under repository standing authorization only after every pre-run,
security, license, protocol, package, and idempotency check passes. Dataset and kernel remain
private. Remote deletion and validator bypass are prohibited.

The task is complete only when one attempt passes strict local artifact validation or all
approved batch-size attempts fail and their evidence is preserved. Completion updates the
research profile report, claim registry only if needed to preserve the non-claim boundary,
context handoff, and next-action guidance.

The locked test remains closed. The next main multi-seed training schedule may be recommended
from throughput and memory evidence, but it must not be launched as part of this profile task.
