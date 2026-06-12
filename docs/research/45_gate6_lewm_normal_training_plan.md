# Gate 6 LeWM Normal-Only Training Plan

Status date: 2026-06-12
Status: `passed_v8`

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
Gate 6 package is published.

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
bundled Python package was not available on Kaggle's script path. A later Canary A proved the
Python-module submission path, but Gate 6 v6 failed before dependency installation because Kaggle
did not place its auxiliary source ZIP beside the generated script.

Gate 6 v7 embedded a deterministic source archive but exposed Kaggle's duplicate nested Lance
mount layout. V8 selected the deepest same-name Lance leaf, materialized all inputs under
`/tmp/gate6_input`, completed the bounded CUDA pilot, and passed strict validation. The frozen
checkpoint SHA-256 is
`300cefe9622ab43acd79bc2202ac90a214cbc4ae9921ed3434573fc9198ff252`.
