# Evaluation Protocol

## 1. Dataset and split protocol

TempGlitch is used through the public Hugging Face artifact at <https://huggingface.co/datasets/asgaardlab/TempGlitch>. Phase 3B uses dataset revision `1d46a63c31ebfe3b675b51a2231d547da372eff9`.

The Phase 3B split is repo-defined:

- group by category and public binary label
- split by source/video, never by clip
- for `10` videos per category/label: `6` train, `2` validation, `2` test
- seed: `42`

## 2. Label conversion limitation

The public TempGlitch artifact exposes binary per-video labels, not verified fine temporal spans. This repo maps each buggy video to one full-video positive interval in `source,start_frame,end_frame,label` format. Normal videos remain implicit negatives.

This supports binary clip/video-level analysis only. It does not support temporal localization claims.

## 3. Scorer fitting protocol

- `frame_diff`: no fitted parameters.
- `feature_distance`: fit centroid on train-normal clips only.
- `mini_latent`: fit PCA encoder and transition model on train-normal clips only.

Validation and test clips are never used for fitting.

## 4. Threshold calibration protocol

Thresholds are selected on validation scores and labels by best validation F1. Test metrics are computed with the fixed validation-selected threshold. Test labels are not used to tune thresholds.

## 5. Metrics

Primary metrics:

- precision
- recall
- F1
- accuracy
- AUROC

AUROC is reported as `null` when a group has only positives or only negatives.

## 6. Per-category analysis

Per-category metrics are computed on the test split using the fixed validation threshold. Category-level AUROC is used to compare ranking quality, while F1 is interpreted cautiously because validation thresholds currently favor high recall.

## 7. Failure analysis

Failure analysis exports:

- false positives sorted by highest score
- false negatives sorted by lowest score
- source-level metrics
- score distribution summaries by category

False positives and false negatives must be interpreted against the binary per-video label limitation.

## 8. Provenance requirement

Every paper-facing metric must cite:

- dataset URL
- access date
- dataset revision
- split file
- command
- scorer
- threshold protocol
- metrics JSON path

Generated data and outputs must remain gitignored.

## 9. What can and cannot be claimed

Can claim:

- reproducible benchmark pipeline
- leakage-aware train/validation/test split
- validation-only threshold calibration
- preliminary category-level findings

Cannot claim:

- temporal localization
- state of the art
- real LeWorldModel integration
- global `mini_latent` superiority
- full-paper-ready benchmark performance
