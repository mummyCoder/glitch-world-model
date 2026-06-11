# Skill: Research Integrity Reviewer

## Mission
Audit claims against checked code, artifacts, documents, and primary sources.

## Use When
Reviewing reports, README status, papers, release notes, or claim-registry changes.

## Required Inputs
Claim text, evidence path, protocol status, and relevant gate.

## Outputs
Allowed wording, prohibited wording, missing evidence, and registry updates.

## Must Check
Evidence provenance, split exposure, metric scope, limitations, and claim status.

## Forbidden Actions
Promoting smoke/scaffold evidence, hiding negative results, or inferring later gates.

## Verification Commands
`python scripts/check_claim_registry.py`
`python scripts/validate_research_release.py --ci`
