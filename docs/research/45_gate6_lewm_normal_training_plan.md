# Gate 6 LeWM Normal-Only Training Plan

Status date: 2026-06-11
Status: `partial_after_v3_infrastructure_failure`

Gate 5 passed strict CUDA/resume validation, so Gate 6 may open. The first Gate 6 action is a
bounded TempGlitch normal-only pilot described by `configs/lewm_gate6_pilot.yaml`.

## Data Contract

- Use the frozen TempGlitch revision and grouped protocol from report 40.
- Train only on rows labeled `Normal`.
- Build a normal-only, source/pair-disjoint validation Lance dataset for training selection.
- Keep a non-locked glitch validation clip separate for post-training encoding proof only.
- Do not materialize, train on, score, or select against locked test.
- Record split, source, pair, dataset, config, and checkpoint hashes.

The reduced Gate 5 smoke dataset is not automatically accepted as the Gate 6 pilot source. Its
training labels and validation composition must be audited against the frozen split before a
Gate 6 package is approved.

## Pilot Configuration

- NVIDIA T4, image size 112, batch size 2.
- One epoch, at most 16 train steps and 8 validation steps.
- Zero-action TempGlitch adaptation, explicitly named.
- Prediction plus SIGReg training with 128 projections.
- No threshold fitting and no detection metric in Gate 6.

## Pass Criteria

- Finite training and validation losses.
- Finite non-collapsed latent diagnostics.
- Saved checkpoint with verified SHA-256 and successful strict reload.
- Successful encoding of one normal validation clip and one non-locked glitch validation clip.
- Protocol audit proves normal-only fitting and false locked-test flags.

The source audit passed with 20 train-normal episodes, 10 validation-normal episodes, and one
non-locked validation-buggy encoding probe. The v3 live kernel failed before epoch 1 because its
bundled Python package was not available on Kaggle's script path. The corrected v5 package embeds
the source as a root-level ZIP and remains approval-pending; it has not been pushed.
