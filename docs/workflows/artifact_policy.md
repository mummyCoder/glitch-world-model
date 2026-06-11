# Artifact Policy

## Never Commit

- `outputs/`, `data/raw/`, `data/processed/`
- Lance datasets and converted media
- checkpoints or model weights
- caches, virtual environments, `mlruns/`, `wandb/`
- `.env`, `kaggle.json`, tokens, credentials, or private keys
- downloaded external-reference repositories

Store local artifacts only under ignored data/output paths or approved external storage.

## Hash Policy

Use SHA-256 for datasets, splits, configs, checkpoints, scores, metrics, and package inventories
that support a gate or claim. Record the hash in metadata rather than renaming source files
without provenance.

## Safe To Commit

- source code, tests, schemas, and validators
- redacted templates and dry-run configuration
- small evidence summaries without private paths or secrets
- documentation, claim registry entries, and generated paper tables whose provenance is recorded

Before commit, inspect `git status`, `git diff --check`, `git diff --name-only`, and the research
release validator output.
