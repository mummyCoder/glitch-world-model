# Repository Instructions

Read and follow `AGENTS.md`, `RULES.md`, and `CONVENTIONS.md`. Consult `PLAYBOOK.md` for the
full roadmap, evidence map, role playbooks, and current next actions.

- Preserve the CSV/JSON interfaces and keep heavy ML dependencies optional.
- Use tests first for behavioral changes and make narrowly scoped edits.
- Keep the claim registry synchronized with paper-facing wording.
- Do not claim LeWM gameplay performance, superiority, SOTA, temporal localization, or neural
  locked-test results from current engineering/smoke evidence.
- Do not run Kaggle live actions, GPU training, or locked-test scoring without explicit approval.
- Never commit or print data, outputs, checkpoints, Lance datasets, credentials, or tokens.

Before completion run:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
```
