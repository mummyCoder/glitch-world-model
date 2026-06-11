# Skill: Locked Test Release Officer

## Mission
Enforce one-time evaluation of one frozen validation-selected configuration.

## Use When
A task proposes materializing, scoring, reporting, or reopening locked test.

## Required Inputs
Validation decision, config/checkpoint/split hashes, claim scope, and explicit approval.

## Outputs
Release decision, approval record, one-time score record, and invalidation disclosure.

## Must Check
No prior access, one configuration, fixed threshold, approval hash, and score count.

## Forbidden Actions
Test tuning, candidate comparison on test, repeated scoring, or silent post-test changes.

## Verification Commands
`python -m pytest tests/test_locked_test_gate.py`
`python scripts/check_claim_registry.py`
