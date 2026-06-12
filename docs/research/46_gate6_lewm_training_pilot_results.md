# Gate 6 LeWM Training Pilot Results

Status date: 2026-06-12
Result: `gate6_passed_v8`

Gate 6 is open for preparation because Gate 5 passed strict CUDA/resume validation. The pilot
configuration and acceptance criteria are frozen in `configs/lewm_gate6_pilot.yaml` and report
45.

The local source audit passed:

- 20 deterministic train-normal episodes and 20,156 four-step windows.
- 10 deterministic validation-normal episodes and 8,993 four-step windows.
- One separate validation-buggy encoding probe and 1,088 four-step windows.
- Zero train/validation source or heuristic-pair overlap.
- Metadata SHA-256 `5aed6612d2c4bcee3da000db08ff56e9283432d4ba8795b7c388155b65916472`.
- Split SHA-256 `717b43f123e89681d81ad92e4c7308104c52a4068c1ef7a47f77230e6e74f207`.

The Gate 6 dataset was uploaded and reached Kaggle status `ready`. Exactly one v3 kernel was
pushed. It reached `ERROR` before epoch 1 because `glitch_detection` was not importable from the
Kaggle script mount. Strict validation failed because all required training artifacts were absent.
This is an infrastructure failure, not a training or model result.

The corrected v5 package stores the source tree as `glitch_detection_src.zip` beside the entry
script and unpacks it before import. Its content-based kernel fingerprint is
`ae0aae43793adb94f8498f8d07c292426e69a0657ba545dbecbfda8682e03504`.
That exact approval was created, validated, consumed, and submitted exactly once. Kaggle CLI then
returned `Expecting value: line 1 column 1 (char 0)` and no remote `lewm-gate6-pilot-v5` kernel
appeared in `kernels list --mine` or `kernels status`. This is preserved as a submission-stage
failure with no same-fingerprint retry.

A secret-safe diagnostic confirmed Kaggle CLI 2.2.1 on Python 3.14.4, authenticated read access,
dataset status `ready`, valid v5 metadata, an existing entry script, and a 447,813-byte package.
An initial private CPU-only, dataset-free canary through the direct executable returned the same
JSON parse error and was not retried.

The later Canary A completed, proving the Python-module Kaggle write path worked. Gate 6 v6 was
accepted as remote version 1 and failed at runtime before dependency installation:
`shutil.ReadError: /kaggle/src/glitch_detection_src.zip is not a zip file`.
The local ZIP was valid, but Kaggle did not place that auxiliary file beside
`/kaggle/src/script.py`. This narrows v6 to a packaging-contract failure, not training evidence.

V7 embedded the source archive and reached runtime, then failed because Kaggle exposed each Lance
input at both a shallow mount point and a nested same-name directory. V8 changed candidate
selection to discard ancestor mount points and copy the deepest leaf into `/tmp/gate6_input`.

Public kernel `huynhdieuthanh/lewm-gate6-pilot-v8` completed on a Tesla T4. The strict validator
returned:

- status `gate6_passed`;
- device `cuda`, completed epoch `1`;
- checkpoint SHA-256
  `300cefe9622ab43acd79bc2202ac90a214cbc4ae9921ed3434573fc9198ff252`;
- verified checkpoint reload and finite collapse diagnostics;
- finite encoding for 8,993 normal-validation windows and 1,088 non-locked buggy-probe windows;
- `normal_only_training=true` and `normal_only_validation=true`;
- `locked_test_materialized=false` and `locked_test_scored=false`.

This establishes bounded normal-only gameplay training engineering. Gate 6 did not fit a
detection threshold or compute AUROC, F1, temporal localization, superiority, or locked-test
performance.

Locked test remains unmaterialized and unscored.
