# Locked-Test Release

Locked test is closed by default.

## Preconditions

- Validation evidence names exactly one model, checkpoint, scorer, aggregation, threshold, and
  preprocessing configuration.
- The decision records dataset/split/config/checkpoint hashes and allowed claim scope.
- No unresolved leakage or artifact-validation failure exists.
- The user explicitly approves release for the exact decision fingerprint.

## Approval Record

Store a local ignored approval file containing:

- decision SHA-256
- config and checkpoint SHA-256
- split SHA-256
- approval timestamp
- one-time-use flag

## Execution

1. Verify approval and hashes.
2. Materialize only the required locked-test inputs.
3. Score the frozen configuration once.
4. Apply the frozen validation threshold unchanged.
5. Hash scores and metrics and record the single execution.

Do not compare candidates, refit normalization/covariance, or tune thresholds on test. Any
post-test change invalidates the locked-test framing and must be disclosed.
