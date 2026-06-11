# Gate 5 Current State

Status date: 2026-06-11

Gate 5 remains `partial`. The validation-only TempGlitch package exists in ignored storage, its
private dataset is ready on Kaggle, and the remote Lance file names and sizes match the approved
local package. No downloaded Kaggle CUDA train/resume artifact set exists.

## Package And Approval Audit

- Dataset inventory SHA-256:
  `897f4a8f310aa9891db5c45cc5bc78285c7cb965a469e46d78346d28c1877f51`
- Kernel approval fingerprint:
  `8c918c264e3a840e47ab11b540de38c2ce0520ca0688bb280637fff49d68d0a4`
- Dataset status: ready; eight Lance files matched by relative name and byte size.
- Dataset approval: consumed by the completed upload.
- Kernel approval: consumed by the single 2026-06-11 push attempt.
- Locked test: not packaged, materialized, or scored.

## Artifact Contract Audit

| Expected artifact | Produced by | Currently available from Kaggle run? | Blocker | Fix needed |
| --- | --- | --- | --- | --- |
| `run_config.json` | generated validation kernel | no | kernel submission returned HTTP 409 | resolve submission conflict, obtain fresh approval, run once |
| `environment.json` | generated validation kernel | no | no Kaggle run | same |
| `dataset_metadata.json` | generated validation kernel after training | no | no Kaggle run | same |
| `training_metadata.json` | `train_lewm` | no | no Kaggle run | same |
| `loss_history.json` | `train_lewm` | no | no Kaggle run | same |
| `collapse_diagnostics.json` | `train_lewm` | no | no Kaggle run | same |
| `checkpoint.sha256` | `train_lewm` | no | no Kaggle run | same |
| `protocol_audit.json` | generated validation kernel | no | no Kaggle run | same |
| `resume_metadata.json` | generated validation kernel after resume | no | no Kaggle run | same |

Local CPU smoke directories contain training outputs, but they are not Kaggle CUDA evidence and
do not satisfy this table.

## Validator Readiness

The strict validator now checks:

- complete artifact presence;
- CUDA availability and training device;
- resumed epoch advancement;
- matching config, dataset, and checkpoint hashes;
- finite non-empty loss history;
- finite collapse diagnostics;
- false locked-test flags in both protocol and training metadata.

The package dry-run and focused validator fixtures pass locally. This is engineering evidence
only; it does not upgrade Gate 5.
