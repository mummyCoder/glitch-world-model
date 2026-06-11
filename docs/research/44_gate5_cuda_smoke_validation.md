# Gate 5 CUDA Smoke Validation

Status date: 2026-06-11
Result: `passed`

The approved validation-only Kaggle kernel
`huynhdieuthanh/lewm-gate5-cuda-smoke-v6`, version 1, completed on an NVIDIA T4. The downloaded
ignored artifact set passed `scripts/validate_lewm_kaggle_artifacts.py`.

## Verified Evidence

- Kernel fingerprint:
  `358e2d77c60c3986be2e84f3c6044200ebfcc2a5fe8f68b0800273fc8c7b6910`
- Approval consumed at: `2026-06-11T06:43:13.400785+00:00`
- Runtime: Python 3.12.13, PyTorch 2.10.0+cu128
- CUDA available: true
- Training device: `cuda`
- Resume advancement: epoch 1 to epoch 2
- Config hash:
  `a5eea7af02da28901cbfa05e57d19c35229d1c0e73daeab14130714feb0ca60a`
- Train dataset hash:
  `de7ba095239b05a708d0e71be9e35bcb53bc437115ec7fc5622f1f98fb6d3a77`
- Validation dataset hash:
  `62e626646599c2a61bada03a25691c1d9a01b68dd751e1b947cb4d7f5e2819ec`
- Checkpoint SHA-256:
  `3ce9f439cda96f6dff24a39dda45ee394eb753852081edef824b129057d1b585`
- Loss history: finite and non-empty
- Collapse diagnostics: finite
- Locked test materialized: false
- Locked test scored: false

This proves Kaggle CUDA training/resume engineering only. It does not establish gameplay-scale
training, glitch detection, superiority, SIGReg benefit, temporal localization, or a locked-test
result.

