# Security Checks

## Before External Reference Use

- Verify repository identity, commit, and license.
- Clone only into `_external_references/` or another ignored location.
- Read source and documentation only; do not execute reference scripts.
- Do not import community skills or marketplace prompts directly.

## Before Kaggle Packaging Or Commit

- Scan for `.env`, `kaggle.json`, tokens, private keys, credential patterns, checkpoints, data,
  Lance files, and unexpectedly large files.
- Confirm external references, outputs, data, caches, and virtual environments are ignored.
- Review staged content, not only working-tree names.

## Required Checks

```powershell
git diff --check
python scripts/validate_research_release.py --ci
pre-commit run --all-files
```

`detect-private-key` and `check-added-large-files` run in pre-commit. `detect-secrets`,
`gitleaks`, and `pip-audit` are optional defense-in-depth tools; document their versions and
findings when used, but do not make network-dependent scans part of default CI without review.
