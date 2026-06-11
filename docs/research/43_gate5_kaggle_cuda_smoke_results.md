# Gate 5 Kaggle CUDA Smoke Results

Status date: 2026-06-11
Result: submission blocked before execution

## Execution Record

The approved TempGlitch validation-only package passed its local security scan. The associated
private dataset was `ready`, and its eight remote Lance files matched the local package by
relative name and byte size.

The exact one-time kernel approval was then consumed and one T4 kernel push was submitted.
Kaggle returned HTTP `409 Conflict`. Read-only status checks found no corresponding kernel in the
account list.

## Evidence Outcome

- CUDA run started: no verified evidence.
- CUDA used: not established.
- Training completed: not established.
- Resume advanced: not established.
- Expected artifacts downloaded: none.
- Strict artifact validator run on Kaggle artifacts: no, because no artifacts exist.
- Locked test materialized or scored: no.

Gate 5 therefore remains `partial`. Approval consumption and an attempted push are operational
records, not training evidence.

## Next Action

The 409 cause is now locally classified: the consumed package used the same slug for the Kaggle
dataset and kernel. A corrected package with kernel slug
`huynhdieuthanh/lewm-gate5-cuda-smoke-v2` has been prepared and fingerprinted, but no retry was
performed. Any live push requires fresh approval for fingerprint
`4d1108f7e9b5f62ba969961f2bee56f9bd226d794ab350386ce510006f91e3f8`.
