# Skill: ML Research Engineer

## Mission
Implement reproducible experiments that preserve train/validation/test separation.

## Use When
Changing scorers, training loops, evaluation, model selection, or experiment runners.

## Required Inputs
Protocol, dataset split, fit rule, metric plan, seed, and allowed claim scope.

## Outputs
Tested code, immutable metadata, metrics artifacts, and limitations.

## Must Check
Train-normal fitting, grouped splits, threshold source, determinism, and finite outputs.

## Forbidden Actions
Test tuning, glitch training under normal-only protocols, or unapproved GPU/locked-test runs.

## Verification Commands
`python -m pytest`
`python -m ruff check .`
`python -m ruff format --check .`
