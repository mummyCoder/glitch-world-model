# NEXT_ACTION.md

Last updated: 2026-06-13T09:45:00+00:00
Commit: `ff372c9ec50edbd517024e92ef058cafadfd4abc`

## Current Priority
Advance Roadmap v3 after R1: freeze the main non-locked training configuration and prepare
multi-seed episode-level validation evaluation.

## Success Criteria
- Preserve the Gate 7-9 pilot and the new 36/14/22 research source fingerprints.
- Preserve the validated 500-update GPU profile evidence and use it only for engineering resource
  planning.
- Freeze normal-only checkpoint selection, three seeds, evaluation interval, and wall-clock budget.
- Run only non-locked training/validation until a separate locked-test decision is explicitly made.
- Keep locked-test materialization/scoring false.

## Current Known Blocker
The 500-update GPU profile is complete, but the paper-grade non-locked multi-seed training and
episode-level validation evaluation have not run. This does not justify opening locked test.
