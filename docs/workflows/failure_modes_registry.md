# Failure Modes Registry

Every new failure requires one appended row and one regression test. This table only grows.

| date | bucket | symptom_signature | root_cause | fix_commit_sha | guard_test |
|---|---|---|---|---|---|
| 2026-06-13 | packaging_idempotency | `FileExistsError: ... already exists` | Kaggle materialization reused an existing destination | `b67bfd3` | `test_generated_kernel_bootstraps_from_kaggle_like_cwd` |
| 2026-06-13 | environment_decode | `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f` | Windows subprocess pipe used the default cp1252 decoder | `02e65a6` | `test_default_executor_replaces_non_utf8_subprocess_output` |
| 2026-06-13 | dataloader_spawn | `attempt ... before the current process has finished its bootstrapping phase` | Rendered kernel called training at top level with DataLoader workers | `3ef825a` | `test_generated_kernel_is_immutable_and_fail_closed` |

Only `cuda_oom` may advance the approved batch-size ladder. Transient Kaggle infrastructure
failures receive bounded retry. Every other bucket requires stop-and-fix.
