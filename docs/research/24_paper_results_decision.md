# Paper Results Decision

## 1. Current best available evidence

The strongest current evidence is Phase 3B: a leakage-aware 100-video TempGlitch slice across all five public categories. It uses `5,572` clips and a repo-defined `60 / 20 / 20` train/validation/test video split.

## 2. Main result table

| Scorer | Test precision | Test recall | Test F1 | Test AUROC |
| --- | ---: | ---: | ---: | ---: |
| `frame_diff` | `0.522810` | `1.000000` | `0.686639` | `0.410416` |
| `feature_distance` | `0.525487` | `0.989529` | `0.686441` | `0.504053` |
| `mini_latent` | `0.522810` | `1.000000` | `0.686639` | `0.458728` |

## 3. Does mini_latent outperform baselines?

No. `mini_latent` does not outperform the simple baselines globally. It is below `feature_distance` and above `frame_diff` by AUROC, but both differences are weak and not enough for a superiority claim.

Category-specific note:

- `mini_latent` has its best category AUROC on `Velocity Bug` (`0.531094`).
- It does not win any category by AUROC.

## 4. Does the project support temporal localization?

No. The public TempGlitch labels are binary per-video labels. The repo's current conversion maps buggy videos to full-video positive intervals. That is not temporal-span supervision.

## 5. Does the project support full paper?

Not yet. The engineering package is stronger, but the scientific performance result is weak. A full paper would need:

- stronger method or real LeWM integration
- video-level aggregation for per-video labels
- ablations
- failure-case figures
- preferably verified temporal-span annotations

## 6. Does the project support short paper?

Yes, with an honest framing:

- reproducible benchmark pipeline
- public benchmark access resolution
- leakage-aware evaluation
- failure analysis showing why clip-level evaluation with binary per-video labels is hard
- careful positioning of latent-surprise methods as future work or a negative/diagnostic result

## 7. Recommended next phase

Recommended next: Phase 6B, add video-level aggregation for per-video labels.

Reason:

- The current labels are per-video.
- Clip-level thresholding produces many false positives.
- Video-level aggregation directly matches the available supervision.

## 8. Decision gate before Phase 7 ablations

Do not run broad ablations until one of these is true:

- video-level aggregation shows a clearer signal
- a stronger method improves ranking under the current split
- temporal-span labels become available

If none of those happens, the best paper strategy is short-paper reproducibility and failure analysis.
