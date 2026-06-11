---
applyTo: "kaggle/**,scripts/*kaggle*.py,src/glitch_detection/*kaggle*.py,configs/*kaggle*.yaml"
---

# Kaggle And GPU

- Default to dry-run, private, validation-only, and locked-test fail-closed.
- Require separate fingerprint-bound approvals for dataset upload and kernel push.
- Never embed or print credentials.
- Treat only locally validated downloaded artifacts as execution evidence.
- Do not perform live actions unless the user explicitly approves the exact fingerprinted step.
