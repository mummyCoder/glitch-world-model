# Gate 5 Kaggle CUDA Smoke Results

Status date: 2026-06-11
Result: third approved submission executed and failed before training

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

After that fix, a fresh approval was created for fingerprint
`47107246ea537fce9c435717301b12c0408f296b34567602f6408b77a5d856c9`. Dataset status was `ready`,
the approval was consumed at `2026-06-11T05:01:48.445275+00:00`, and exactly one push was
submitted for kernel `huynhdieuthanh/lewm-gate5-cuda-smoke-v3`. Kaggle accepted version 1, then
the run reached `KernelWorkerStatus.ERROR`.

The v3 log shows the dependency path issue was resolved, but the full
`stable-worldmodel[env,train]` install failed before training while building `box2d-py` on Kaggle
Python 3.12:

```text
ERROR: Failed building wheel for box2d-py
ERROR: Failed to build installable wheels for some pyproject.toml based projects (box2d-py)
```

The generator has therefore been updated again for the next package to clone the repository into
`/tmp/glitch-world-model` and install only the minimal smoke dependencies:
`stable-worldmodel==0.1.1`, `stable-pretraining==0.1.7`, and `transformers==4.57.6`.

## Evidence Outcome

- CUDA run started: no verified evidence.
- CUDA used: not established.
- Training completed: not established.
- Resume advanced: not established.
- Expected artifacts downloaded: no; only error logs and partial ignored output were downloaded.
- Strict artifact validator run on Kaggle artifacts: yes, and it failed because all required Gate 5
  artifacts were missing.
- Locked test materialized or scored: no.

Gate 5 therefore remains `partial`. Approval consumption and an attempted push are operational
records, not training evidence.

## Next Action

The v2 and v3 approvals are consumed and must not be reused. A new ignored v4 package/request has
been prepared with kernel slug `huynhdieuthanh/lewm-gate5-cuda-smoke-v4`, minimal dependency
installation, `/tmp` repository clone location, and fingerprint:

`e3a3ad6bcfd73c99ee295003041db7651e375a1d970b11bd3665a7393c87382a`

Any further live push requires a fresh explicit approval for that exact v4 fingerprint.
