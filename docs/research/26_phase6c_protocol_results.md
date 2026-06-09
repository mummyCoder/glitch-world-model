# Phase 6C Protocol Results

## Status

Phase 6C protocol hardening is implemented and verified on the existing local Phase 3B
artifacts. Performance numbers below remain exploratory because the Phase 3B test slice was
already inspected during Phase 6B and no repeated grouped refit/scoring run has completed.

## Old Split Leakage Audit

The conservative `category + trailing numeric index` heuristic found:

- `65` total heuristic grouping units in the 100-video Phase 3B subset
- `35` suspected pairs containing at least two sources
- `19 / 35` suspected pairs crossing train, validation, or test

This does not prove official-pair leakage because the public artifact has no verified official
pair-ID field. It does prove the old source-only split is not safe against the available pair
signal.

## New Grouped Split Dry-Run

Five seeds (`42` through `46`) were generated from the same Phase 3B metadata:

| Seed | Train videos | Validation videos | Test videos | Cross-split suspected groups |
| ---: | ---: | ---: | ---: | ---: |
| 42 | 62 | 18 | 20 | 0 |
| 43 | 60 | 21 | 19 | 0 |
| 44 | 62 | 19 | 19 | 0 |
| 45 | 63 | 19 | 18 | 0 |
| 46 | 61 | 19 | 20 | 0 |

The slight count variation is expected because whole suspected-pair groups, rather than
individual videos, are assigned together.

## Validation-Only Selection Rehearsal

Using only existing Phase 6B validation calibration JSON files:

- selected scorer: `mini_latent`
- selected aggregation: `p95`
- selection metric: validation AUROC
- validation AUROC: `0.58`
- fixed threshold: `0.141307474`

The selection artifact is
`outputs/tempglitch_phase3b_video_level/selected_protocol_config.json` and is gitignored.

## Locked-Test Rehearsal With Pair Bootstrap

Exactly one selected configuration was evaluated:

| Metric | Point | Pair-bootstrap 95% CI |
| --- | ---: | ---: |
| AUROC | `0.52` | `[0.2395, 0.7693]` |
| F1 | `0.6897` | `[0.4665, 0.8387]` |

Bootstrap settings: `1,000` samples, seed `42`, grouped by `pair_id_heuristic`. All `1,000`
samples were valid for both reported metrics.

The wide AUROC interval confirms that the 20-video test estimate is unstable and cannot support
a superiority claim.

## Reproducible Commands

```powershell
python scripts\run_tempglitch_repeated_grouped_splits.py --dry-run
python scripts\select_tempglitch_protocol_config.py
python scripts\evaluate_tempglitch_locked_test.py --n-bootstrap 1000 --group-key pair_id_heuristic
```

## Remaining Limitations

- `pair_id_heuristic` is not an official TempGlitch pair ID.
- Repeated grouped split performance is `TBD`; only split dry-runs are complete.
- The current locked-test result is a rehearsal on an already exposed test slice.
- The current subset was originally sampled sequentially.
- Public labels remain binary per video, so temporal localization and mIoU remain unsupported.
