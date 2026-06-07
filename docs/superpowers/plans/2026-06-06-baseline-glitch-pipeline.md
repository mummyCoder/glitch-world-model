# Baseline Glitch Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small Python MVP that preprocesses gameplay videos or frame folders, computes frame-difference anomaly scores, evaluates scores against optional labels, and plots score timelines.

**Architecture:** The root project owns a compact `src/glitch_detection` package independent from third-party code under `external/`. CLI scripts expose preprocessing, scoring, evaluation, and plotting as separate steps so later LeWM latent scoring can reuse the same manifest and score formats.

**Tech Stack:** Python standard library, OpenCV if available for video/frame IO, Pillow fallback for frame IO, NumPy, matplotlib, pytest.

---

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/glitch_detection/__init__.py`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Add package metadata and test config**

Create `pyproject.toml` with editable package metadata, Python 3.10+, runtime dependencies, and pytest path config.

- [ ] **Step 2: Add README with MVP commands**

Create `README.md` showing where raw videos go and how to run `preprocess`, `score-frame-diff`, `evaluate`, and `plot-scores`.

- [ ] **Step 3: Add package marker**

Create `src/glitch_detection/__init__.py` with a version string.

- [ ] **Step 4: Add import smoke test**

Create `tests/test_imports.py` asserting the package imports.

### Task 2: Manifest and Label Utilities

**Files:**
- Create: `src/glitch_detection/manifest.py`
- Create: `tests/test_manifest.py`

- [ ] **Step 1: Add tests for manifest read/write and label overlap**

Test writing clips to CSV, reading them back, parsing labels, and detecting whether a clip overlaps a labeled glitch interval.

- [ ] **Step 2: Implement manifest dataclasses and CSV helpers**

Implement `ClipRecord`, `LabelInterval`, `write_manifest`, `read_manifest`, `read_labels`, and `clip_has_glitch`.

### Task 3: Preprocess CLI

**Files:**
- Create: `src/glitch_detection/preprocess.py`
- Create: `tests/test_preprocess.py`

- [ ] **Step 1: Add tests using synthetic image frames**

Test frame-folder preprocessing with generated PNG frames and verify clip folder creation plus manifest rows.

- [ ] **Step 2: Implement frame extraction and clip creation**

Support input video files or frame folders, clip length/stride, image size, and output manifest.

### Task 4: Frame-Difference Baseline

**Files:**
- Create: `src/glitch_detection/frame_diff.py`
- Create: `tests/test_frame_diff.py`

- [ ] **Step 1: Add tests for score behavior**

Create one static clip and one changing clip, assert changing clip has higher anomaly score.

- [ ] **Step 2: Implement scoring CLI**

Read manifest, compute mean absolute grayscale frame difference per clip, and write `scores.csv`.

### Task 5: Evaluation and Plotting

**Files:**
- Create: `src/glitch_detection/evaluate.py`
- Create: `src/glitch_detection/plot_scores.py`
- Create: `tests/test_evaluate.py`

- [ ] **Step 1: Add tests for threshold metrics**

Test precision, recall, F1, accuracy, and AUROC fallback on small deterministic scores.

- [ ] **Step 2: Implement evaluation**

Read scores with labels, choose threshold by best F1 unless threshold is supplied, and write JSON metrics.

- [ ] **Step 3: Implement plotting**

Plot anomaly score over clip start time and save PNG.

### Task 6: Verify MVP

**Files:**
- Modify: none unless verification finds issues.

- [ ] **Step 1: Run unit tests**

Run `python -m pytest`.

- [ ] **Step 2: Run end-to-end synthetic demo**

Generate a tiny synthetic frame sequence, preprocess it, score it, evaluate it, and plot it.

- [ ] **Step 3: Confirm outputs**

Confirm `manifest.csv`, `scores.csv`, `metrics.json`, and `scores.png` exist.
