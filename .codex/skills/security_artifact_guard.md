# Skill: Security And Artifact Guard

## Mission
Prevent credentials, private data, checkpoints, and generated artifacts from entering Git.

## Use When
Packaging, committing, downloading artifacts, changing ignores, or handling external sources.

## Required Inputs
Changed-file list, package inventory, ignore rules, and artifact policy.

## Outputs
Safety findings, blocked files, hashes, and remediation steps.

## Must Check
Tracked files, large files, private keys, tokens, `.env`, Kaggle credentials, and Lance data.

## Forbidden Actions
Printing secrets, executing reference code, bypassing scans, or deleting user artifacts.

## Verification Commands
`git diff --check`
`python scripts/validate_research_release.py --ci`
`pre-commit run --all-files`
