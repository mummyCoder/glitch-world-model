# R3 Seed 42 P100 CUDA Runtime Incompatibility

Date: 2026-06-13

Evidence class: infrastructure/runtime-failure-only

## Summary

- Kernel slug: `huynhdieuthanh/lewm-r3-seed42-eb395860`
- Commit SHA: `dbddafcb6bb681a67c56dee69bc2a9faacccf5ba`
- Package fingerprint: `eb39586088c49ea359d1fba523ae095b4209117991568c60ff218a63d434c586`
- Archived failed output/log root: `outputs/r3_seed42_failed_p100_dbddafc`
- Kaggle accelerator observed: GPU P100
- Failure time: approximately 91 seconds after launch
- Locked test: untouched, unmaterialized, and unscored
- Seed 43/44: not launched

## Failure Classification

Classification: infrastructure/runtime incompatibility.

This failure is not a model result, not a data result, not an optimization result, and not an OOM.
No successful training result was produced. R3 seed 42 remains not passed.

## Error Summary

The Kaggle runtime selected a Tesla P100 GPU with CUDA compute capability `sm_60`. The installed
PyTorch build was `2.10.0+cu128` and reported support for CUDA capabilities `sm_70 sm_75 sm_80
sm_86 sm_90 sm_100 sm_120`. The run crashed when the first batch tensor was moved to CUDA:

```text
Tesla P100-PCIE-16GB with CUDA capability sm_60 is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_70 sm_75 sm_80 sm_86 sm_90 sm_100 sm_120.
torch.AcceleratorError: CUDA error: no kernel image is available for execution on the device
```

## Boundary

This record only preserves failed-run evidence and root-cause classification. It does not support
any LeWM glitch-detection performance claim, baseline comparison, temporal localization claim,
SIGReg benefit claim, or paper result.

## Required Fix Before Relaunch

The Kaggle kernel must fail fast before training when the assigned GPU has compute capability below
`sm_70`. Acceptable R3 accelerators for the current Kaggle PyTorch container are T4 or newer. If
Kaggle assigns P100 again, stop and relaunch only after selecting or obtaining a compatible
accelerator.
