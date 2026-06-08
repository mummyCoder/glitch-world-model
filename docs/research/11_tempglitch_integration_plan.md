# TempGlitch Integration Plan

## 1. Purpose

Plan a safe Phase 2 integration path for TempGlitch without downloading data in Phase 0. The goal is to prepare the repo to evaluate temporal gameplay glitches using the existing preprocess -> score -> evaluate -> report pipeline.

## 2. Current status

- TempGlitch is a target benchmark for later phases.
- TempGlitch data has not been downloaded in this repo.
- TempGlitch file format, annotation format, split protocol, and license are still `TBD / verify`.
- Current Phase 0 verification uses only the synthetic demo and unit tests.
- Raw TempGlitch files must remain under gitignored data paths and must not be committed.

## 3. What must be verified before download

- Official project page or data source URL.
- License and allowed research use.
- Whether data is video files, frame folders, or another format.
- Annotation schema and whether temporal spans are provided.
- Whether labels are binary, categorical, open-ended text, or mixed.
- Train/validation/test split protocol.
- Dataset size and expected disk requirements.
- Whether a small subset can be used for pipeline smoke testing.

## 4. Expected dataset questions

- Does each sample map to one video, one clip, or multiple event segments?
- Are normal paired videos included?
- Are glitch categories available?
- Are start/end frame indices available, or only timestamps?
- If timestamps are used, what FPS should be used for frame conversion?
- Are annotations per-video, per-event, or per-frame?
- Is there an official evaluation script?
- Are there scene cuts or camera transitions that could bias simple frame-difference baselines?

## 5. Target local layout

Target layout for Phase 2, not created by this plan:

```text
data/raw/tempglitch/
  videos/              # or frames/, depending on verified format
  annotations/         # original annotations, if available
  README_SOURCE.txt    # source URL, access date, and license notes

data/raw/tempglitch_labels.csv
data/processed/tempglitch_subset/
outputs/tempglitch_*.csv
outputs/tempglitch_*.json
outputs/tempglitch_*.png
```

`data/` and `outputs/` are gitignored. Raw videos, generated clips, scores, metrics, plots, and checkpoints must not be committed unless a later task explicitly creates tiny documentation fixtures.

## 6. Label conversion target

All TempGlitch labels should be converted into the existing labels CSV schema:

```text
source,start_frame,end_frame,label
```

Conversion rules to verify later:

- `source` should match the manifest `source` value produced by preprocessing.
- `start_frame` and `end_frame` should be integer frame indices.
- `label` should be `1` for glitch intervals.
- Non-glitch intervals are usually implicit unless the verified dataset requires explicit negative labels.
- If source annotations use timestamps, conversion must document FPS and rounding.

## 7. Pipeline commands planned for Phase 2

These commands are planned examples only. They should not be run until TempGlitch access and format are verified.

```powershell
python scripts\convert_tempglitch_labels.py --input data\raw\tempglitch\annotations --output data\raw\tempglitch_labels.csv

python -m glitch_detection.run_baseline --input data\raw\tempglitch\frames --labels data\raw\tempglitch_labels.csv --name tempglitch_frame_diff --clip-length 16 --stride 8 --size 128 --scorer frame_diff

python -m glitch_detection.run_baseline --input data\raw\tempglitch\frames --labels data\raw\tempglitch_labels.csv --name tempglitch_feature_distance --clip-length 16 --stride 8 --size 128 --scorer feature_distance

python -m glitch_detection.run_baseline --input data\raw\tempglitch\frames --labels data\raw\tempglitch_labels.csv --name tempglitch_mini_latent --clip-length 16 --stride 8 --size 128 --scorer mini_latent
```

## 8. Acceptance criteria for Phase 2

- TempGlitch source URL, license, and access date are documented.
- Dataset format is verified instead of guessed.
- A small subset can be preprocessed into `manifest.csv`.
- Converted labels use `source,start_frame,end_frame,label`.
- At least one baseline writes `scores.csv` and `metrics.json`.
- Evaluation results are marked as actual only after commands are run.
- No raw data, generated outputs, or checkpoints are committed.

## 9. Fallback plan

If TempGlitch cannot be accessed or converted safely:

- Use the existing GlitchBench subset script for an image-oriented fallback.
- Use the World of Bugs asset demo for controlled visual glitch examples.
- Consider VideoGlitchBench later if accessible and aligned with temporal annotations.
- Keep synthetic dynamics data as sanity check only, not publishable benchmark evidence.

## 10. Evidence policy

- Do not claim TempGlitch is downloaded until files exist locally.
- Do not claim TempGlitch format is known until annotations are inspected.
- Do not report metrics until `metrics.json` is produced by the pipeline.
- Mark unavailable or unverified facts as `TBD / verify`.
- Separate synthetic sanity checks from public benchmark evidence in reports and paper text.
