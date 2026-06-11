# NEXT_ACTION.md

Last updated: 2026-06-11T05:12:17+00:00
Commit: `54d35e80d23fabff8dd8d02a5c2bac0fd6d29533`

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
The 2026-06-11 TempGlitch path consumed three kernel approvals: the first push returned HTTP 409
before execution because the package reused the dataset slug, the second v2 push failed before
training because the generated script looked for `/kaggle/src/lewm-runtime.txt`, and the third v3
push failed before training because full LeWM environment dependency installation failed on
`box2d-py`. A v4 package/request exists with kernel slug
`huynhdieuthanh/lewm-gate5-cuda-smoke-v4`; obtain fresh approval for fingerprint
`e3a3ad6bcfd73c99ee295003041db7651e375a1d970b11bd3665a7393c87382a` before any live push.
