# R2-R5 Fast Track Design

Date: 2026-06-13

## Goal

Advance Roadmap v3 quickly after the validated 500-update GPU profile by running the main LeWM
non-locked training/evaluation path while preparing one optional strong video-representation
baseline in parallel. The critical path is LeWM R2-R5; the optional baseline must not block seed 42,
seed 43/44, or the first episode-level validation table.

## Current Evidence

- R1 completed a non-locked 500-update CUDA profile at batch size 8 with AMP.
- Profile throughput was about 13.06 updates/sec with peak VRAM about 512 MB.
- The final artifact set passed strict validation and included `validator_report.json`.
- No validation-buggy scoring or locked-test access occurred during profiling.

## Approach

Use the R1 evidence to freeze a conservative main-run family immediately:

- batch size: 8
- AMP: enabled
- `num_workers`: 0 unless a later isolated data-loader profile proves safe
- checkpoint/reload validation: mandatory
- seeds: 42, 43, 44
- seed order: 42 first, then 43/44 only after seed 42 validates
- checkpoint selection: validation-normal prediction loss only
- locked test: closed

In parallel, add a fail-closed optional baseline adapter for frozen video representations:

- preferred path: VideoMAE-small or TimeSformer-small if dependencies are present
- fallback path: skip with a machine-readable skip reason
- no internet/download assumption inside default CI
- no blocking of LeWM training
- identical R5 episode manifest and labels when enabled

## Data Flow

R2 writes a frozen main-run config family with dataset hashes, profile evidence, seeds, update
budget, evaluation interval, checkpoint interval, and claim boundary.

R3-R4 launch and validate LeWM seed runs on train-normal plus validation-normal checkpoint
selection. Validation-buggy remains unavailable during fitting and selection.

R5 scores the same non-locked validation episode manifest for LeWM and available baselines:

- LeWM latent surprise
- frame difference
- train-normal-fitted feature distance
- Conv3D autoencoder if existing artifact/protocol is usable
- optional frozen video representation baseline if dependencies and runtime are available

## Error Handling

- Any non-finite loss, invalid reload, wrong update count, hash mismatch, or locked-test access is
  stop-and-fix.
- Optional baseline dependency/runtime failure is not fatal to the LeWM critical path; it records a
  skip artifact.
- No OOM ladder is used unless the failure classifier identifies CUDA OOM.
- Any config change after freeze creates a new experiment family and is disclosed.

## Testing And Validation

Use focused tests while iterating. Run the full required command set only at stage exit or before
commit/push:

- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/validate_research_release.py --ci`
- `python scripts/check_claim_registry.py`
- `python scripts/doctor.py`
- `python scripts/validate_context_cache.py`
- `pre-commit run --all-files` when available

## Exit Gates

R2 exits when one config family is frozen and documented.

R3 exits when seed 42 completes with valid artifacts.

R4 exits when seeds 43 and 44 complete with valid artifacts.

R5 exits when every reported metric table cell traces to a score hash, metric hash, config
fingerprint, and identical episode manifest. Negative results remain visible.
