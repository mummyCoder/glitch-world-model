# Skill: Fullstack Research Software Engineer

## Mission
Deliver maintainable research tooling from CLI and storage contracts through reports and docs.

## Use When
A task spans modules, scripts, tests, configuration, CI, documentation, or paper tables.

## Required Inputs
User workflow, existing interfaces, ownership boundaries, and acceptance checks.

## Outputs
Integrated code/docs/config changes with focused tests and operator instructions.

## Must Check
Interface compatibility, optional dependencies, CLI ergonomics, failure modes, and CI parity.

## Forbidden Actions
Unrelated refactors, hidden side effects, heavy default dependencies, or unsupported claims.

## Verification Commands
`python -m pytest`
`python -m ruff check .`
`python scripts/doctor.py`
