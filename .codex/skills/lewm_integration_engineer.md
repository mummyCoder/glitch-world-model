# Skill: LeWM Integration Engineer

## Mission
Integrate audited LeWM runtime, data, checkpoint, training, and surprise contracts.

## Use When
Working on `lewm_*` modules, isolated runtime, checkpoint loading, or Gate 2-7 artifacts.

## Required Inputs
Upstream commit/license, runtime lock, checkpoint hash, action mode, and data contract.

## Outputs
Fail-closed adapters, shape/provenance checks, tests, and qualified engineering evidence.

## Must Check
Optional imports, strict load, normalization, temporal shape, action dimensions, and hashes.

## Forbidden Actions
Calling zero-action original action-conditioned LeWM, modifying upstream silently, or claiming
gameplay performance before Gate 7.

## Verification Commands
`python -m pytest tests/test_lewm_adapter.py tests/test_lewm_data.py tests/test_lewm_training.py`
