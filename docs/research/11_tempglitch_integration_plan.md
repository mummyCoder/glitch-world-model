# TempGlitch Integration Plan

## 1. Purpose

Plan a safe Phase 2 integration path for TempGlitch without downloading data in Phase 0. The goal is to prepare the repo to evaluate temporal gameplay glitches using the existing preprocess -> score -> evaluate -> report pipeline.

## 2. Current status

- TempGlitch is a target benchmark for later phases.
- TempGlitch public access is now verified at <https://huggingface.co/datasets/asgaardlab/TempGlitch>.
- License is MIT on the public dataset page.
- The public dataset page shows `1,500` videos and `60.3 GB`.
- The public artifact exposes one `train` split and binary per-video labels.
- The public file tree is grouped into five categories with paired `Buggy` / `Normal` folders.
- A public label quirk exists: one class name appears as `Buggy ` with a trailing space.
- Current Phase 0 verification uses only the synthetic demo and unit tests.
- Raw TempGlitch files must remain under gitignored data paths and must not be committed.

## 3. What must be verified before download

- Official public source URL.
- Whether the repo can fetch a tiny subset without downloading the full dataset.
- Whether the current public artifact exposes only binary clip labels or richer temporal spans.
- Whether the repo should treat the public split as a smoke subset only or define a local split for broader experiments.
- Expected disk requirements for a tiny subset vs the full dataset.

## 4. Verified public-artifact answers

- Each public row maps to one video clip.
- Paired normal videos are included.
- Glitch categories are visible in the public file paths:
  - `Blinking`
  - `Frozen Animation`
  - `Shooting Error`
  - `Stuck in Place`
  - `Velocity Bug`
- The public Hugging Face artifact exposes binary per-video labels, not verified start/end span annotations.
- The public dataset page currently exposes one `train` split only.
- A tiny subset is operationally feasible because each row has a direct MP4 download URL.

## 5. Target local layout

Target layout for Phase 2, not created by this plan:

```text
data/raw/tempglitch/
  videos/
  metadata.csv
  README_SOURCE.txt    # source URL, access date, and license notes

data/raw/tempglitch_smoke_labels.csv
data/processed/tempglitch_smoke/
outputs/tempglitch_smoke_*.csv
outputs/tempglitch_smoke_*.json
outputs/tempglitch_smoke_*.png
```

`data/` and `outputs/` are gitignored. Raw videos, generated clips, scores, metrics, plots, and checkpoints must not be committed unless a later task explicitly creates tiny documentation fixtures.

## 6. Label conversion target

TempGlitch smoke labels should be converted into the existing labels CSV schema:

```text
source,start_frame,end_frame,label
```

Phase 2 smoke conversion rule:

- `source` should match the manifest `source` value produced by preprocessing.
- `start_frame` should be `0` for buggy videos.
- `end_frame` should be the last frame covered by the merged manifest for that video.
- `label` should be `1` for buggy videos.
- Normal videos should remain implicit negatives.

This preserves the repo's interfaces without inventing finer-grained spans that are not present in the verified public artifact.

## 7. Pipeline commands planned for Phase 2

These commands are planned examples only. They should be updated to match the real Phase 2 smoke scripts.

```powershell
python scripts\download_tempglitch.py --output-dir data\raw\tempglitch_smoke --categories Blinking --limit-per-group 1

python scripts\run_tempglitch_smoke_test.py --raw-dir data\raw\tempglitch_smoke --clip-length 16 --stride 16 --size 128 --scorer frame_diff

python scripts\run_tempglitch_smoke_test.py --raw-dir data\raw\tempglitch_smoke --clip-length 16 --stride 16 --size 128 --scorer feature_distance
```

## 8. Acceptance criteria for Phase 2

- TempGlitch source URL, license, and access date are documented.
- Dataset format is verified instead of guessed.
- A small subset can be downloaded without pulling the full `60.3 GB`.
- Per-video manifests can be merged into one `manifest.csv`.
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
- Do not imply verified temporal span annotations when the public artifact only exposes binary per-video labels.
- Do not report metrics until `metrics.json` is produced by the pipeline.
- Mark unavailable or unverified facts as `TBD / verify`.
- Separate synthetic sanity checks from public benchmark evidence in reports and paper text.
