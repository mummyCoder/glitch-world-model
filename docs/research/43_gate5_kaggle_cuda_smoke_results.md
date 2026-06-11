# Gate 5 Kaggle CUDA Smoke Results

Status date: 2026-06-11
Result: second approved submission executed and failed before training

## Execution Record

The first approved TempGlitch validation-only package passed its local security scan. The
associated private dataset was `ready`, and its eight remote Lance files matched the local package
by relative name and byte size.

The exact one-time kernel approval was then consumed and one T4 kernel push was submitted.
Kaggle returned HTTP `409 Conflict`. Read-only status checks found no corresponding kernel in the
account list.

After the local slug conflict was fixed, a fresh approval was created for fingerprint
`4d1108f7e9b5f62ba969961f2bee56f9bd226d794ab350386ce510006f91e3f8`. Dataset status was `ready`,
the approval was consumed at `2026-06-11T03:48:07.773881+00:00`, and exactly one push was
submitted for kernel `huynhdieuthanh/lewm-gate5-cuda-smoke-v2`. Kaggle accepted version 1, then
the run reached `KernelWorkerStatus.ERROR`.

The downloaded error log shows the generated script failed before training while installing
dependencies:

```text
Could not open requirements file: [Errno 2] No such file or directory:
'/kaggle/src/lewm-runtime.txt'
```

This indicates Kaggle executed the uploaded script as `/kaggle/src/script.py` and did not place the
packaged `lewm-runtime.txt` beside it. The generator has been updated so the next package clones
the repository and installs from `requirements/lewm-runtime.txt` instead of assuming auxiliary
files live under `/kaggle/src`.

## Evidence Outcome

- CUDA run started: no verified evidence.
- CUDA used: not established.
- Training completed: not established.
- Resume advanced: not established.
- Expected artifacts downloaded: no; only the error log was downloaded to ignored storage.
- Strict artifact validator run on Kaggle artifacts: yes, and it failed because all required Gate 5
  artifacts were missing.
- Locked test materialized or scored: no.

Gate 5 therefore remains `partial`. Approval consumption and an attempted push are operational
records, not training evidence.

## Next Action

The v2 approval is consumed and must not be reused. A new ignored v3 package/request has been
prepared with kernel slug `huynhdieuthanh/lewm-gate5-cuda-smoke-v3`, repository-clone dependency
installation, and fingerprint:

`47107246ea537fce9c435717301b12c0408f296b34567602f6408b77a5d856c9`

Any further live push requires a fresh explicit approval for that exact v3 fingerprint.
