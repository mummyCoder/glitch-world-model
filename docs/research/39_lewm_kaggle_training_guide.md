# Gate 5 LeWM Kaggle Training Guide

The current Kaggle foundation is validation-only and locked-test fail-closed. It prepares a
runnable private CUDA training package, scans it for credentials, records separate dataset/kernel
fingerprints, and requires fresh fingerprint-bound approvals before any live action.

## Required Live Sequence

1. Build and inspect train and validation Lance datasets.
2. Prepare the private Kaggle package with `scripts/prepare_lewm_kaggle_package.py`.
3. Review package inventory and config hashes.
4. Request and consume a dataset-upload approval bound to that fingerprint.
5. Request and consume a separate kernel-push approval bound to the final kernel fingerprint.
6. Run CUDA smoke, download artifacts, and verify checkpoint resume.

No locked-test dataset is included. Gate 5 remains incomplete because no locally validated LeWM
Kaggle CUDA train/resume artifact exists. An approval record, upload, or kernel push by itself
does not prove successful training.

On 2026-06-11, the approved TempGlitch dataset upload was confirmed ready and matched the local
Lance package inventory by file name and size. One exact fingerprint-approved kernel push was
attempted, but Kaggle returned HTTP `409 Conflict`; the approval is now consumed and no run or
downloaded artifacts exist. See
[the current-state audit](41_gate5_current_state.md),
[approval status](42_gate5_kernel_approval_status.md), and
[execution record](43_gate5_kaggle_cuda_smoke_results.md). A fresh exact approval is required
before any retry.

The local 409 diagnosis found that the consumed package reused the dataset slug as the kernel
slug. Current package preflight rejects placeholder owners, kernel/dataset slug equality, missing
kernel code files, dataset-source mismatches, and consumed approval reuse. The corrected ignored
package uses kernel slug `huynhdieuthanh/lewm-gate5-cuda-smoke-v2` and waits for fresh approval.

The reusable runner `scripts/run_kaggle_lewm.py` was first verified locally on synthetic data.
On 2026-06-11, reduced real-gameplay CPU smokes also completed forward/backward and hash-matching
resume from epoch 1 to epoch 2 for both the TempGlitch zero-action and WOB real-action paths.
This does not establish Kaggle CUDA training or gameplay glitch-detection performance.

The generated Gate 5 kernel now fails closed without CUDA, trains once, resumes once with the same
config/data hashes, and requires the resumed epoch to advance. Downloaded artifacts must pass
`scripts/validate_lewm_kaggle_artifacts.py`. The validator rejects missing artifacts, non-finite
losses or collapse diagnostics, hash/resume mismatches, non-CUDA execution, and locked-test flags
in protocol or training metadata.

## Quota Policy

- 50%: dual-primary LeWM.
- 25%: CNN-LSTM, VideoMAE, and TimeSformer.
- 15%: LeWM ablations.
- 10%: open VLM.
