# LAST_HANDOFF.md

Last completed task: Kaggle LeWM runner seed wiring and CodeGraph setup
Commit: pending
Date: 2026-06-13

## What Changed

- Added a `--seed` argument to the validation-only Kaggle LeWM runner.
- Wired the parsed seed into `LeWMTrainConfig.seed`.
- Added focused runner tests that stub training and inspect the constructed config.
- Installed and initialized CodeGraph for fast agent code navigation.
- Added `.codegraph/` to `.gitignore`; the local index remains untracked.
- Enabled the full CodeGraph MCP tool set in the user's global Codex configuration.
- No training semantics changed beyond seed wiring.
- No Kaggle, GPU, locked-test, or paper-claim action was performed.

## Checks Passed

- `python -m pytest tests/test_run_kaggle_lewm.py` passed.
- `python -m pytest tests/test_lewm_training.py` passed.
- `python -m pytest` passed with 277 tests.
- `python -m ruff check .` passed.
- `python -m ruff format --check .` passed.
- `python scripts/validate_research_release.py --ci` passed.
- `python scripts/check_claim_registry.py` passed with 58 claim IDs and no errors.
- `python scripts/doctor.py` and `python scripts/validate_context_cache.py` passed.
- `pre-commit run --all-files` passed.
- CodeGraph `explore`, `node`, `impact`, and `affected` queries passed.

## Safety Status

- Locked test remains closed, unmaterialized, and unscored.
- No live Kaggle action was performed.
- No long GPU job was run.
- No secret material was printed or committed.
- CodeGraph telemetry is disabled.
- CodeGraph index/cache files remain ignored and untracked.
- No performance or paper-facing claim was added.

## Gate Status After Task

- Gates 1-8 remain passed.
- Gate 9 remains only the limited non-locked one-buggy-episode validation pilot.
- Research MVP source readiness remains unchanged.
- Gate 10 and locked test remain closed.

## Open Blockers

- The 500-update Kaggle GPU throughput/VRAM profile has not run.
- Main training batch size, evaluation interval, and wall-clock budget are not frozen.
- Multi-seed episode-level results and robust calibration do not yet exist.

## Next Recommended Task

- Use the new seed CLI to prepare separate non-locked profile/main-run invocations for seeds
  42, 43, and 44, starting with the predeclared 500-update GPU profile only.

## Files Likely Relevant Next

- `scripts/run_kaggle_lewm.py`
- `configs/lewm_research_mvp.yaml`
- `docs/plans/2026-06-12-lewm-research-grade-experiment.md`
- `src/glitch_detection/lewm_training.py`
