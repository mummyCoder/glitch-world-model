# NEXT_ACTION.md

Last updated: 2026-06-11T03:56:19+00:00
Commit: `b7150d232127fd8abf8f97b00fc03d730cdd9697`

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
The 2026-06-11 TempGlitch path consumed two kernel approvals: the first push returned HTTP 409
before execution because the package reused the dataset slug, and the second v2 push was accepted
but failed before training because the generated script looked for `/kaggle/src/lewm-runtime.txt`.
A v3 package/request exists with kernel slug `huynhdieuthanh/lewm-gate5-cuda-smoke-v3`; obtain
fresh approval for fingerprint `47107246ea537fce9c435717301b12c0408f296b34567602f6408b77a5d856c9`
before any live push.
