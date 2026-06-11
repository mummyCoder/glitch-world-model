# NEXT_ACTION.md

Last updated: 2026-06-11T16:00:34+00:00
Commit: `a741dce5d334905830e6f385670d76429d7d5648`

## Current Priority
Approve and run the corrected Gate 6 v5 normal-only LeWM pilot.

## Success Criteria
- Frozen TempGlitch source/pair-disjoint split audit.
- Normal-only train and normal-only validation Lance inventories.
- False locked-test materialization/scoring flags.
- Fingerprint-bound validation-only Gate 6 package.
- Finite training/validation losses and non-collapsed diagnostics after an approved pilot.
- Checkpoint reload plus normal and non-locked glitch validation encoding.

## Current Known Blocker
Gate 6 data is ready, but v3 failed before training on an import-path error. V5 fixes the source
bundle and is approval-pending. Do not push it without revalidating the exact fingerprint, and do
not run Gate 7 experiments before Gate 6 passes.
