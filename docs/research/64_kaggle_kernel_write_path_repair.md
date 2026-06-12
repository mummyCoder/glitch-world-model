# Kaggle Kernel Write Path Repair

Status date: 2026-06-12
Start commit: `0fcb0756767c873a9db6001e7fd271300c9b4688`

## Scope

Gate 6 v6 preparation remained closed until a minimal Kaggle kernel could be created and complete.
No Gate 6 package, Gate 7 experiment, or locked-test action was performed during diagnosis.

## Environment

- Windows 11 build 26200.
- Python `3.14.4` at `C:\Python314\python.exe`.
- Kaggle CLI/package `2.2.1`.
- One Kaggle executable was discovered:
  `C:\Users\ADMIN\AppData\Roaming\Python\Python314\Scripts\kaggle.exe`.
- `KAGGLE_CONFIG_DIR` was unset; `C:\Users\ADMIN\.kaggle\kaggle.json` existed and was readable.
- The safely read username was `huynhdieuthanh`; no credential value was printed or stored.
- Authenticated kernel/dataset list operations succeeded.
- Dataset `huynhdieuthanh/lewm-tempglitch-gate6-pilot` reported `ready`.

Raw redacted diagnostics are ignored under
`outputs/gate6/diagnostics/write_path_repair/`.

## Canary Matrix

| Variant | Invocation | Result |
|---|---|---|
| A | `python -c "from kaggle.cli import main; main()" kernels push -p <absolute-path>` | Version 1 accepted; remote slug appeared; status `COMPLETE` |
| B | `python -m kaggle ...` | Not run; stop-on-first-success rule |
| C | direct `kaggle.exe ...` | Not run; stop-on-first-success rule |
| D | clean Python 3.12 virtualenv | Not run; stop-on-first-success rule |

Successful canary:
`huynhdieuthanh/lewm-submit-canary-a-20260611-170340`.

The private canary used no GPU, dataset, internet, or repository source. Its downloaded ignored
output contains `heartbeat.json`, proving the worker completed the submitted script.

## Root Cause Decision

The earlier v5 and direct-executable canary failures were not reproduced by Variant A. The
Python-module invocation is therefore the required write path.

Gate 6 v6 was subsequently accepted as remote version 1, then reached `ERROR` before dependency
installation. Its downloaded log reports
`shutil.ReadError: /kaggle/src/glitch_detection_src.zip is not a zip file`. The local ZIP was
valid, while the pulled remote kernel contained only the script and metadata. The v6 failure is
therefore a Kaggle script packaging-contract failure: an auxiliary source file cannot be assumed
to exist beside `/kaggle/src/script.py`.

## Safety Decision

The write path is restored through Variant A. Gate 6 v7 must use a fresh public dataset and kernel
slug, embed all repository source in the single code file, and run through standing-authorized
automation. Gate 7 remains closed until strict Gate 6 artifact validation passes.
