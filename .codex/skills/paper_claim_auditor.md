# Skill: Paper Claim Auditor

## Mission
Keep manuscript wording within the strongest evidence actually available.

## Use When
Editing abstracts, titles, tables, captions, conclusions, submissions, or presentations.

## Required Inputs
Claim registry, source log, metric artifact, split protocol, and venue requirements.

## Outputs
Approved wording, citation/provenance notes, and blocked claims.

## Must Check
Gate level, validation/test labeling, primary citation, uncertainty, and format requirements.

## Forbidden Actions
SOTA claims, LeWM title before Gate 7, locked-test metrics before Gate 10, or temporal claims
without spans.

## Verification Commands
`python scripts/make_paper_tables.py`
`python scripts/check_claim_registry.py`
