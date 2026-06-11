# Skill: Dataset Protocol Engineer

## Mission
Freeze leakage-safe, provenance-rich train/validation/locked-test metadata.

## Use When
Adding datasets, converters, grouping rules, split logic, or label mappings.

## Required Inputs
Dataset revision/license, source IDs, pair/episode IDs, labels, and exposure history.

## Outputs
Split CSV, provenance JSON, audit JSON, hashes, and conversion report.

## Must Check
Zero cross-split groups, duplicate sources, train-normal rule, and test materialization state.

## Forbidden Actions
Window-level random splitting, pickle loading from untrusted data, or implicit test access.

## Verification Commands
`python -m pytest tests/test_dataset_protocols.py tests/test_lewm_data.py`
