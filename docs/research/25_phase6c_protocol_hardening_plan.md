# Phase 6C Protocol Hardening Plan

## Purpose

Phase 6C hardens the TempGlitch evaluation protocol before any result is treated as
paper-safe. It preserves the existing `preprocess -> score -> evaluate -> report` pipeline and
CSV interfaces while adding controls against pair leakage, test-set configuration search, and
unstated sampling bias.

## Protocol Risks Being Addressed

1. The public artifact describes paired Buggy/Normal videos, but it does not expose a verified
   official pair-ID field. Splitting each label group independently can put suspected pairs in
   different splits.
2. Phase 6B evaluated every scorer and aggregation on test. Those results are useful for
   exploration, but selecting the best displayed test result is test-set hyperparameter search.
3. Sequential subset selection over Hugging Face rows is deterministic but not representative
   random sampling.
4. A 20-video test slice produces unstable point estimates. Confidence intervals and repeated
   grouped splits are needed before performance claims.

## Pair-Suspect Grouping

`src/glitch_detection/pairs.py` implements `pair_id_heuristic`. The heuristic extracts the
trailing numeric index from each source name and scopes it by TempGlitch category. It is
conservative and is never described as an official dataset pair ID.

The new grouped split keeps every suspected pair group in exactly one of train, validation, or
test. Split metadata records the seed and grouping mode. If no numeric suffix exists, the raw
source name becomes its own fallback group.

## Selection And Locked Test

The paper-safe sequence is:

1. Fit scorers using allowed train data.
2. Calibrate thresholds and compare scorer/aggregation candidates using validation only.
3. Save exactly one selected configuration.
4. Evaluate exactly that configuration on locked test.
5. Report source- or pair-level bootstrap confidence intervals.

The Phase 6B test slice has already been inspected, so applying the new locked-test script to
those existing files is a protocol rehearsal, not a fresh final test.

## Sampling

The TempGlitch downloader supports:

- `sequential` for tiny smoke tests
- seeded `random-stratified` selection within each category and public-label group

Subset metadata records `sample_mode`, `seed`, category, label, row index, dataset revision,
video URL, and local path.

## Repeated Grouped Splits

`scripts/run_tempglitch_repeated_grouped_splits.py` validates a default set of five grouped
split seeds in dry-run mode. Repeated performance reporting remains blocked until each seed is
fully refit, validation-selected, and locked-test evaluated.

## Claim Gate

After Phase 6C implementation, the repo may claim that it implements pair-suspect grouped
splitting, validation-only configuration selection, single-config locked-test evaluation, and
group bootstrap confidence intervals.

It must not yet claim final TempGlitch performance, latent-surprise superiority, real
LeWorldModel integration, JEPA/SIGReg success, temporal localization, mIoU, or state of the art.
