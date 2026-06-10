# Phase 6E Kaggle Validation Results

## Run Identity

- Run date: June 10, 2026
- Kaggle notebook: `https://www.kaggle.com/code/huynhdieuthanh/phase6e-video-autoencoder`
- Private dataset: `huynhdieuthanh/glitch-world-model-phase6e`
- Branch and commit: `main` at `75b0184ac7c3bf37bf17633131290aa6a26ee8ec`
- Model: compact Conv3D autoencoder
- Device recorded by training metadata: `cuda`
- Checkpoint SHA-256: `3d4c6c54fd9782177351b8b8d12bd62768367d96125d58ab7ee25e62ed80e0bf`

Generated artifacts, scores, manifests, and the checkpoint remain gitignored.

## Protocol Audit

| Item | Verified value |
| --- | ---: |
| Fit split | train-normal only |
| Train-normal clips / sources | 1,724 / 31 |
| Validation clips / sources | 1,071 / 18 |
| Test clips / sources counted for audit | 1,125 / 20 |
| Cross-split pair-suspect groups | 0 |
| Test materialized | false |
| Test scored | false |

Configuration: seed `42`, image size `64`, clip length `16`, batch size `8`, `10` epochs,
learning rate `0.001`, and `2` data-loader workers.

Training loss decreased from `0.0227342` in epoch 1 to `0.000782479` in epoch 10. Strict local
ingestion verified exactly `1,071` validation score rows and zero non-finite scores.

## Validation Metrics

These metrics are validation-only and were generated locally from the downloaded score artifact
and existing labels:

| Metric | Value |
| --- | ---: |
| AUROC | 0.403865 |
| F1 | 0.605263 |
| Precision | 0.434372 |
| Recall | 0.997831 |
| Accuracy | 0.439776 |
| Threshold | 0.00017699 |
| Positive clips / total clips | 461 / 1,071 |

The high recall and low precision reflect a threshold that marks nearly all clips positive. The
AUROC is below `0.5`, so this run does not support a detection-improvement claim. F1 must not be
read in isolation as evidence of useful ranking performance.

## Artifact Validation

Required artifacts were downloaded with a filename filter and passed both the automation
validator and `scripts/ingest_phase6e_kaggle_artifacts.py`. The local validation confirmed:

- CUDA training metadata exists.
- Required model, audit, metadata, manifests, and score files exist.
- Validation row count is exact and all scores are finite.
- Pair-suspect grouped split audit reports zero cross-split groups.
- Locked test remains unmaterialized and unscored.

## Scientific Claim Status

Safe claim: the repo has completed and strictly ingested a real Kaggle CUDA engineering run of
the Phase 6E Conv3D validation-only baseline.

Not supported: performance improvement, locked-test neural performance, temporal localization,
JEPA, real LeWorldModel integration, or state of the art. Any locked-test run still requires a
saved validation decision and an explicit release-gate action.
