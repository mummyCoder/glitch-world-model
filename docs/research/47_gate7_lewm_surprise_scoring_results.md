# Gate 7 LeWM Surprise Scoring

Status date: 2026-06-11
Result: `infrastructure_ready_experiment_blocked`

The repository now provides a production `lewm_surprise` scorer, a scoring CLI with checkpoint
hash verification and sidecar provenance, deterministic non-locked validation-manifest tooling,
validation-only evaluation, and timeline plotting. Scores preserve the six-column public CSV
contract. Mean, maximum, and top-three mean aggregation are supported.

Gate 7 experiments did not run because Gate 6 produced no valid checkpoint. No LeWM gameplay
scores or metrics exist, and no baseline or ablation comparison is authorized yet.

Real-action scoring fails closed because the current TempGlitch manifest has no synchronized
action source. The available path is explicitly zero-action. Locked test remains closed.
