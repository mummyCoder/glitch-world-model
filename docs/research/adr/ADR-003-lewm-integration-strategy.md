# ADR-003: LeWM Integration Strategy

## Status

Superseded by `ADR-004-mandatory-lewm-main-method.md`.

## Decision

This was the original staged decision. It is retained for history only. The current strategy
makes a verified real LeWM integration mandatory before the paper may use LeWM-based claims.

## Context

This historical ADR predates the current optional-runtime `lewm_latent` implementation. The
scorer registry still preserves the same pipeline shape, while current verified evidence is
limited to strict checkpoint loading, data conversion, and reduced CPU smokes. See ADR-004 and
the claim registry for the active policy.

## Reason

This staged approach reduces risk:

- avoids premature coupling to `external/le-wm`
- keeps current tests and CLI interfaces stable
- gives baselines a clear role before expensive model work
- allows dataset and benchmark strategy to mature first

## Consequences

- Do not implement real LeWM scoring in documentation/scaffolding tasks.
- Future LeWM work must write the same `scores.csv` schema.
- Any checkpoint or model data must stay out of git.
- LeWM results should be compared against `frame_diff`, `feature_distance`, and `mini_latent`.
