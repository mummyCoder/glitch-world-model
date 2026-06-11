# Skill: Kaggle GPU Operator

## Mission
Prepare and validate reproducible Kaggle GPU runs without implicit live actions.

## Use When
Packaging datasets/kernels, requesting approvals, monitoring runs, or ingesting artifacts.

## Required Inputs
Package inventory, dataset/kernel fingerprints, explicit approval, and expected artifact list.

## Outputs
Dry-run report, approval request, downloaded artifacts, and strict validation report.

## Must Check
Credential scan, private/validation-only config, CUDA proof, resume proof, and locked-test flags.

## Forbidden Actions
Uploading or pushing without exact approval, duplicate pushes, or treating approval as run proof.

## Verification Commands
`python -m pytest tests/test_lewm_kaggle.py tests/test_kaggle_automation_validation.py`
