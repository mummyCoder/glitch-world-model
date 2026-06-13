# R3 Seed 42 Live Run Record

Date: 2026-06-13

Evidence class: infrastructure/runtime-preflight-only

## Current Status

R3 seed 42 has not passed. No full 15,000-update training run was launched after the cloud
preflight because Kaggle assigned an unsupported Tesla P100 GPU.

## Source State

- Latest source commit used for preflight packaging: `b91df90`
- Previous CUDA guard/failure commit: `ab40d218b47198b4bb751907316262fb0922a230`
- Dataset slug: `huynhdieuthanh/lewm-r3-seed42-private`
- Locked test: untouched, unmaterialized, and unscored
- Seed 43/44: not launched

## Preflight Attempt 1

- Kernel slug: `huynhdieuthanh/lewm-r3-seed42-preflight-b91df90`
- Kaggle URL: `https://www.kaggle.com/code/huynhdieuthanh/lewm-r3-seed42-preflight-b91df90`
- Intended scope:
  - print torch/CUDA/GPU metadata
  - require compute capability `sm_70+`
  - load train-normal and validation-normal Lance inputs
  - run exactly one optimizer update
  - save and reload a tiny checkpoint
  - write `preflight_passed.json` or `preflight_failed.json`
- Result: failed before training by design.
- Failure artifact: `preflight_failed.json`
- Failure reason: `unsupported_cuda_compute_capability`
- Torch: `2.10.0+cu128`
- GPU: `Tesla P100-PCIE-16GB`
- Compute capability: `sm_60`
- Required compute capability: `sm_70+`

The failure occurred before the one-update training step. It confirms the guard works and prevents
wasting a full R3 run on an unsupported GPU.

## Stop Decision

The immediately previous live R3 seed 42 attempt
`huynhdieuthanh/lewm-r3-seed42-eb395860` also received a Tesla P100 `sm_60` GPU and failed due to
the same PyTorch CUDA support boundary. Because Kaggle assigned P100 twice in a row, execution
stops here. Do not relaunch seed 42 on Kaggle until a T4-or-newer GPU can be selected or obtained.

## Claim Boundary

This record supports only an infrastructure/runtime-preflight statement. It does not support any
LeWM training success, glitch-detection performance, AUROC/AUPRC, baseline superiority, temporal
localization, SIGReg benefit, or locked-test result.

## Next Concrete Action

Obtain a compatible accelerator for R3 seed 42: T4, L4, A100, or another GPU with compute
capability `sm_70+`. After that, rerun the preflight kernel first. Launch the full 15,000-update
R3 seed 42 training only if preflight writes `preflight_passed.json`.
