# NEXT_ACTION.md

Last updated: 2026-06-11T06:17:37+00:00
Commit: `0bec339afc854fa7f518c46c63867e691c16a362`

## Current Priority
Complete or unblock Gate 5 Kaggle CUDA smoke/resume artifact.

## Success Criteria
- `environment.json`
- `resume_metadata.json`
- `protocol_audit.json`
- `run_config.json` or `run_config.resolved.json` according to validator
- `dataset_metadata.json`
- `training_metadata.json`
- `loss_history.json`
- `collapse_diagnostics.json`
- `checkpoint.sha256`
- strict validator pass

## If Approval Missing
Prepare request/fingerprint, update docs/cache, commit and push, and report
`BLOCKED_ON_APPROVAL`.

## If Approval Valid
Execute exactly the approved kernel push/smoke, download artifacts, validate, update
playbook/cache, commit and push.

## Current Known Blocker
The 2026-06-11 TempGlitch path has four failed submissions: v1 returned HTTP 409, v2 failed on a
runtime-file path, v3 failed installing `box2d-py`, and v4 reached the Lance loader but failed
because `/kaggle/input` is read-only. The v5 generator copies both Lance datasets to writable
`/tmp/lewm_input`, but `outputs/gate5/source` is absent. Restore that source before preparing a
new fingerprint-bound request. No live push is authorized.
