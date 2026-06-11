# Gate 5 Kernel Approval Status

Status date: 2026-06-11

## Status: CONSUMED

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
