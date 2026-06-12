# Gate 7-9 LeWM Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Use
> `superpowers:test-driven-development` for behavioral code and
> `superpowers:verification-before-completion` before every completion claim.

**Goal:** Produce real frozen-checkpoint LeWM scores, compare baselines on the identical
non-locked Lance windows, and report validation-only pilot metrics without opening locked test.

**Architecture:** Build one fingerprinted canonical window manifest from the Gate 6 normal
validation and non-locked buggy Lance datasets. Gate 7, Gate 8, and Gate 9 consume the same
ordered `window_id` rows. Two deterministically selected normal episodes calibrate per-scorer
P95 thresholds; the remaining normal episodes and the single buggy episode form the evaluation
rows.

**Tech Stack:** Python, NumPy, PyTorch, stable-worldmodel `LanceDataset`, pytest, Kaggle only as
a scoring fallback.

---

## Task 1: Canonical Lance Manifest

**Files:**
- Create: `src/glitch_detection/lewm_lance_eval.py`
- Test: `tests/test_lewm_lance_eval.py`

- [ ] Define the canonical manifest fields: `window_id`, dataset identity and fingerprint,
  dataset window index, source, source episode, pair, category, label, split, and evaluation
  role.
- [ ] Select exactly two normal calibration episodes by sorting a SHA-256 key derived from
  seed `42` and episode ID. Mark all other normal and all buggy rows as `evaluation`.
- [ ] Read windows through `stable_worldmodel.data.LanceDataset`; do not add a manual Lance
  parser or cross episode boundaries.
- [ ] Validate row order, uniqueness, labels, fingerprints, expected roles, and locked-test
  absence.

## Task 2: Gate 7 Real LeWM Scoring

**Files:**
- Create: `scripts/run_gate7_lance_scoring.py`
- Test: `tests/test_gate7_lance_scoring.py`

- [ ] Validate the frozen `best_weights.pt` SHA-256
  `3feefb1d1001f53ec659b45e7f47cfbc6418f56ea763513f970ec5b333119dbe`.
- [ ] Use the exact Gate 6 image normalization and the checkpoint's four-frame window contract.
- [ ] Emit finite per-transition MSE and L2 scores for every canonical row.
- [ ] Write manifest, scores, and metadata hashes with `locked_test_scored=false`.
- [ ] Run first with `outputs/lewm_runtime/.venv/Scripts/python.exe` on CPU.
- [ ] If and only if local scoring fails for runtime, memory, or device reasons, add a minimal
  scoring-only Kaggle package using the existing Gate 6 dataset and v8 kernel output as sources.
  Do not retrain or publish a new checkpoint dataset.

## Task 3: Gate 8 Same-Manifest Baselines

**Files:**
- Create: `scripts/run_gate8_baselines_from_lance.py`
- Test: `tests/test_gate8_baselines.py`

- [ ] Score exactly the ordered Gate 7 `window_id` rows.
- [ ] Compute grayscale adjacent-frame mean absolute difference.
- [ ] Compute the existing six-dimensional RGB mean/std feature and fit its centroid only from
  the Gate 6 train-normal Lance dataset.
- [ ] Reject missing, duplicate, extra, reordered, fingerprint-mismatched, or metadata-mismatched
  rows.
- [ ] Save score and provenance hashes with `locked_test_scored=false`.

## Task 4: Gate 9 Metrics And Minimal Ablations

**Files:**
- Create: `scripts/run_gate9_ablations.py`
- Modify only if required: `src/glitch_detection/evaluate.py`
- Test: `tests/test_gate9_ablations.py`

- [ ] Evaluate LeWM MSE and L2 with mean, max, and top-two-mean transition aggregation.
- [ ] Evaluate frame-difference and feature-distance baselines on the same evaluation rows.
- [ ] Report AUROC and AUPRC as primary metrics; preserve `pr_auc` as an AUPRC compatibility
  alias.
- [ ] Set each scorer's F1 threshold to its P95 score on the two calibration-normal episodes.
- [ ] Record threshold value/source, calibration episode IDs, class prevalence, dataset/manifest
  hashes, and the one-buggy-episode pilot limitation.

## Task 5: Evidence And Release

**Files:**
- Update: `docs/research/47_gate7_lewm_surprise_scoring_results.md`
- Create: `docs/research/48_gate8_same_manifest_baseline_comparison.md`
- Create: `docs/research/49_gate9_minimal_ablation_results.md`
- Create: `docs/research/50_results_claim_boundary.md`
- Update: `docs/research/16_claim_registry.md`
- Update: `docs/research/62_artifact_manifest.md`
- Update generated context and `docs/context/LAST_HANDOFF.md`

- [ ] Register only the narrow claim that the frozen pilot checkpoint and named baselines were
  evaluated on one identical non-locked Lance window manifest.
- [ ] Keep locked-test, temporal-localization, broad-superiority, SIGReg-benefit, and
  state-of-the-art claims forbidden.
- [ ] Keep all outputs, checkpoints, Lance data, caches, and Kaggle downloads uncommitted.
- [ ] Run the full repository verification suite, commit Gate 7, Gate 8, Gate 9, and docs
  separately, then push `main`.
