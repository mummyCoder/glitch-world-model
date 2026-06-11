# AGENTS.md

## Project Identity

This repository studies LeWM/JEPA-style latent-surprise methods for video game glitch
detection.

Current verified status:

- Gates 1-4 passed at the engineering and smoke level.
- Gate 5 is partial: local CPU train/resume exists, but Kaggle CUDA train/resume proof is
  missing.
- Gates 6-10 have not run.
- Locked test is closed.
- LeWM integration engineering exists; LeWM gameplay evaluation is not yet established.

Safe claims are limited to checkpoint-level LeWM integration, real-data conversion, and local
CPU forward/backward/resume smoke evidence. Do not claim LeWM glitch-detection performance,
superiority, state of the art, temporal localization, or a neural locked-test result.

## Agent Operating Mode

- Work as a senior research engineer: inspect evidence before editing or claiming.
- Use gate-based execution and keep `docs/research/16_claim_registry.md` synchronized.
- Prefer small, testable changes and tests first for behavioral code.
- Preserve unrelated user changes and report skipped checks honestly.
- Never convert scaffolding, fixture output, or smoke evidence into an experiment claim.
- Follow the non-negotiable rules in `RULES.md`.

## Repository Map

- `src/`: reusable pipeline and model integration code.
- `scripts/`: auditable command-line entry points.
- `tests/`: fast default-environment tests.
- `docs/research/`: evidence, protocols, results, and claim registry.
- `docs/roadmap/`: gate definitions and planned work.
- `docs/workflows/`: operational playbooks.
- `configs/`: experiment and runtime configuration.
- `kaggle/`: validation-only launch packages.
- `paper/`: cautious manuscript scaffold and generated tables.
- `external/`: read-only upstream references unless an integration task explicitly says otherwise.

## Engineering Contracts

- Preserve `manifest.csv`, labels CSV, `scores.csv`, and `metrics.json` interfaces.
- Keep scorers pluggable through `src/glitch_detection/score_clips.py`.
- Keep the default install and CI free of heavy GPU dependencies.
- Split by source/pair/episode before windowing; fit train-dependent methods on allowed
  train-normal data only.
- Select configurations and thresholds on validation only.
- Do not edit upstream code under `external/` to make local checks pass.

## Safety Gates

- Do not run new GPU training, Kaggle live actions, or locked-test scoring without explicit,
  action-specific approval.
- Dataset upload and kernel push require separate fingerprint-bound approvals.
- Locked test requires a frozen validation decision naming exactly one configuration and claim
  scope.
- Never print or commit credentials, tokens, private keys, `.env`, or `kaggle.json`.
- Never commit raw data, processed data, outputs, Lance datasets, checkpoints, or caches.

## Required Commands

Run before completion:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
```

When pre-commit is available:

```powershell
pre-commit run --all-files
```

## Documentation And Claims

- `verified`: supported by a checked artifact, repository document, or primary source.
- `experiment-pending`: experiment has not run.
- `future-work`: planned only.
- `rejected`: must not appear as a positive claim.
- Paper-facing claims must be registered before use.
- Cite primary sources and keep negative results and limitations visible.

## Final Report

Report changed files, verification evidence, scientific claim status, locked-test and Kaggle-live
status, artifact/credential safety, unresolved risks, branch/SHA, and the next gate.
