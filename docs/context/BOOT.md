# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-11T03:26:01+00:00
Commit: `d50e3c7f0072219abdfd83eeec9622cf648a3351`

## Read Order
1. `RULES.md`
2. `AGENTS.md`
3. `docs/context/BOOT.md`
4. `docs/context/PROJECT_STATE.md`
5. `docs/context/NEXT_ACTION.md`
6. `docs/context/LAST_HANDOFF.md`
7. `docs/context/TASK_ROUTER.md`

Only open `PLAYBOOK.md` for roadmap, paper, claim, gate-status, or ambiguous tasks, or when the
context cache is stale. Use `docs/context/REPO_MAP.md` before broad repo searches.

## Current Status
- Gates 1-4 passed at engineering/smoke level.
- Gate 5 is partial.
- Gates 6-10 have not run.
- Locked test is closed.
- LeWM integration engineering exists.
- LeWM gameplay evaluation is not established.

## Immediate Next Task
- Complete or unblock Gate 5 Kaggle CUDA smoke/resume artifact.
- Current known blocker: fresh approval is required for corrected kernel fingerprint
  `4d1108f7e9b5f62ba969961f2bee56f9bd226d794ab350386ce510006f91e3f8`.

## Safety
- No Kaggle live action without a current fingerprint-bound approval.
- Dataset upload and kernel push require separate approvals.
- No locked-test materialization or scoring.
- No data, output, checkpoint, Lance dataset, cache, `.env`, token, or `kaggle.json` commits.
- No LeWM detection, superiority, SIGReg benefit, temporal localization, SOTA, or neural
  locked-test claim before the documented gates pass.

## Required Checks
```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
pre-commit run --all-files
```

## Fast Workflow
- Start with the context files and task router.
- Open only the files named by the router plus files discovered with targeted `rg`.
- Update `docs/context/LAST_HANDOFF.md` after each task.
- Regenerate context cache before final verification.
- Treat `PLAYBOOK.md` as the long-form source of truth, not the default first read for every
  routine code edit.
