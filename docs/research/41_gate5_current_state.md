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
- Confirmed 409 preflight cause: the consumed package used the same Kaggle slug for dataset and
  kernel, `huynhdieuthanh/lewm-tempglitch-gate5-smoke`.
- Corrected ignored package prepared after the incident:
  `outputs/gate5/packages/tempglitch_kernel_v2`.
- Corrected kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v2`.
- Corrected kernel fingerprint:
  `4d1108f7e9b5f62ba969961f2bee56f9bd226d794ab350386ce510006f91e3f8`.
- Corrected approval request root:
  `outputs/gate5/approvals/tempglitch_kernel_v2`.
- Locked test: not packaged, materialized, or scored.

## 409 Diagnosis Matrix

| Hypothesis | Status | Evidence |
| --- | --- | --- |
| Kernel slug already exists or was reserved | UNKNOWN | No read-only local artifact proves a pre-existing Kaggle kernel; the failed slug was not visible in the account list after the 409. |
| Kernel slug equals dataset slug | CONFIRMED | Consumed `kernel-metadata.json` and `dataset-metadata.json` both used `huynhdieuthanh/lewm-tempglitch-gate5-smoke`. |
| Placeholder owner such as `private/...` | RULED_OUT | Consumed package used owner `huynhdieuthanh`, not a placeholder owner. |
| Bad `id` in kernel metadata | CONFIRMED | The kernel `id` was validly formatted but conflicted with the dataset slug; the new guard requires a distinct kernel slug. |
| Bad or stale dataset source slug | RULED_OUT | Kernel `dataset_sources` matched the ready dataset slug. |
| Duplicate title/slug behavior in Kaggle CLI | LIKELY | Kernel title `lewm-tempglitch-gate5-smoke` slugified to the same slug as the dataset and kernel `id`. |
| Package fingerprint approved before metadata fix | CONFIRMED | Old approval fingerprint `8c918...d0a4` covered the pre-fix package and is consumed. |
| Unresolved Kaggle-side stale state | POSSIBLE | The local metadata conflict is sufficient, but Kaggle-side reservation cannot be fully ruled out without another live action, which is forbidden here. |

## Artifact Contract Audit

| Expected artifact | Produced by | Currently available from Kaggle run? | Blocker | Fix needed |
| --- | --- | --- | --- | --- |
| `run_config.json` | generated validation kernel | no | kernel submission returned HTTP 409 | obtain fresh approval for corrected package, run once |
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

The package dry-run and focused validator fixtures pass locally. The corrected package/request are
ready for a new human approval, but this is engineering evidence only; it does not upgrade Gate 5.
