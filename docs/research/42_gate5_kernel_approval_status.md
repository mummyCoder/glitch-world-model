# Gate 5 Kernel Approval Status

Status date: 2026-06-11

## Status: READY_FOR_NEW_KERNEL_APPROVAL

The one-time kernel approval matched fingerprint
`8c918c264e3a840e47ab11b540de38c2ce0520ca0688bb280637fff49d68d0a4`,
passed the package security scan, and was unconsumed immediately before execution.

It was consumed at `2026-06-11T02:31:30.540310+00:00` for exactly one kernel push. Kaggle
returned HTTP `409 Conflict`. The kernel was not visible in the subsequent account kernel list,
so there is no run to poll or artifact set to download.

The repository approval schema records `fingerprint`, `approved_at`, `one_time_use`, and
`consumed_at`; it does not define a separate approval-phrase field. The artifact was valid under
that current schema before consumption.

No retry is authorized. The next live attempt requires:

1. resolve the Kaggle submission conflict without performing another push;
2. regenerate or revalidate the final package and fingerprint;
3. create a new ignored request record;
4. obtain a fresh explicit approval for that exact fingerprint.

Changing the kernel identity, metadata, script, dependencies, or packaged source invalidates the
old fingerprint.

## Corrected Request

A corrected validation-only package was prepared locally under ignored storage without any live
Kaggle action:

- Dataset slug: `huynhdieuthanh/lewm-tempglitch-gate5-smoke`
- New kernel slug: `huynhdieuthanh/lewm-gate5-cuda-smoke-v2`
- Dataset fingerprint: `897f4a8f310aa9891db5c45cc5bc78285c7cb965a469e46d78346d28c1877f51`
- Kernel inventory SHA-256: `8f6474331d4873971d42757ccee96494cd306f455399443b97e860dc40906e4c`
- Kernel metadata SHA-256: `c3749bcf9c41b009f853577eb75fc94338e38312625a1ea372bea66da328abf1`
- Kernel script SHA-256: `0d484a956d29b15c866f60e37efe1c1979b53b1c39bd70762036d4abcea59fca`
- New kernel approval fingerprint:
  `4d1108f7e9b5f62ba969961f2bee56f9bd226d794ab350386ce510006f91e3f8`

The request records are in ignored storage at `outputs/gate5/approvals/tempglitch_kernel_v2`.
They are not approvals. Live push remains blocked until the exact new fingerprint is approved.
