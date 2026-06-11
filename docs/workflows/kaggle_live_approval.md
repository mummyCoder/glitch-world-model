# Kaggle Live Approval

Documentation, package creation, and dry-runs never authorize a live Kaggle action.

## Separate Approvals

1. Build and security-scan the private dataset package.
2. Compute the dataset inventory SHA-256.
3. Request a one-time dataset-upload approval bound to that fingerprint.
4. Upload or version the dataset only after that exact approval.
5. Build the final kernel package against the uploaded dataset identity.
6. Compute kernel inventory/script fingerprints.
7. Request a separate one-time kernel-push approval bound to the final fingerprint.
8. Push exactly once, then poll without duplicate submission.

Changing package contents invalidates the associated approval.

## Local Preflight Before Approval

Before requesting or consuming a kernel approval, the package must pass local preflight:

- dataset and kernel slugs are explicit `owner/slug` values;
- placeholder owners such as `private`, `user`, `username`, `owner`, or `your-username` are
  rejected;
- the kernel slug differs from the dataset slug;
- `kernel-metadata.json` contains `id`, `title`, `code_file`, `language`, `kernel_type`,
  `is_private`, `enable_gpu`, and `dataset_sources`;
- `code_file` exists;
- `dataset_sources` exactly matches the approved remote dataset slug;
- kernel metadata hash, kernel code hash, kernel inventory hash, dataset slug, and kernel slug are
  included in the approval fingerprint.

Consumed approvals cannot be reused. A metadata-only fix requires a new package fingerprint and a
new approval request before any live push.

## Required Downloaded Artifacts

- run config and environment
- dataset/training metadata
- loss history and collapse diagnostics
- checkpoint and SHA-256
- protocol audit
- resume metadata
- validation scores/metrics when the gate requires them

## Release Check

Run the gate-specific local validator after download. Approval consumption, Kaggle status, logs,
or a checkpoint alone do not prove a gate. The validator must confirm CUDA, hash-matching resume,
finite outputs, and locked-test false flags.

Never include locked-test data in a validation-only package.
