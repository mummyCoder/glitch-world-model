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

No locked-test dataset is included. No live upload, kernel push, or GPU training was performed
during Phase 1-4 implementation.

The reusable runner `scripts/run_kaggle_lewm.py` was verified locally on CPU with a reduced
synthetic smoke configuration. It completed a real LeWM forward/backward step, saved checkpoint
and weights artifacts, and resumed from epoch 1 to epoch 2 only when config and dataset hashes
matched. This does not establish Kaggle CUDA training or gameplay performance.

## Quota Policy

- 50%: dual-primary LeWM.
- 25%: CNN-LSTM, VideoMAE, and TimeSformer.
- 15%: LeWM ablations.
- 10%: open VLM.
