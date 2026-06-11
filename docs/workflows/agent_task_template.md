# Agent Task Template

## Objective

State the concrete deliverable and whether the task is code, documentation, experiment, or audit.

## Evidence Boundary

- Current gate:
- Allowed claim scope:
- Explicitly forbidden claims:
- Locked-test state:
- Kaggle-live state:

## Inputs

- Files and artifacts to inspect:
- Dataset/split/config/checkpoint hashes, when relevant:
- Primary sources:

## Execution

1. Record branch, SHA, Python version, and clean/dirty state.
2. Read `AGENTS.md`, `RULES.md`, and the relevant workflow.
3. Add focused tests before behavioral changes.
4. Make the smallest compatible change.
5. Update documentation and claim registry when claim scope changes.

## Verification

Run the required commands from `AGENTS.md`, plus task-specific checks. Record skipped checks and
why they were unavailable.

## Final Report

List changed files, verification evidence, safe/unsafe claims, Kaggle/locked-test status,
artifact/credential status, risks, branch/SHA, and the next gate.
