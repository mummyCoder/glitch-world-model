# Gate 7 LeWM Surprise Scoring

Status date: 2026-06-11
Result: `infrastructure_ready_gate6_checkpoint_available`

The repository now provides a production `lewm_surprise` scorer, a scoring CLI with checkpoint
hash verification and sidecar provenance, deterministic non-locked validation-manifest tooling,
validation-only evaluation, and timeline plotting. Scores preserve the six-column public CSV
contract. Mean, maximum, and top-three mean aggregation are supported.

Gate 6 v8 produced a strictly validated checkpoint with SHA-256
`300cefe9622ab43acd79bc2202ac90a214cbc4ae9921ed3434573fc9198ff252`.
Gate 7 validation-only scoring may now run. No LeWM gameplay `scores.csv` or metrics exist yet,
and no baseline or ablation comparison result is supported yet.

Real-action scoring fails closed because the current TempGlitch manifest has no synchronized
action source. The available path is explicitly zero-action. Locked test remains closed.
