# Phase 6E Kaggle Notebook Cells

Replace every `TEN-DATASET` occurrence with the attached private Kaggle Dataset slug.

## Cell 1: Clone And Install

```bash
!git clone --branch codex/phase6e-kaggle-video-autoencoder https://github.com/thanhdicode/glitch-world-model.git
%cd glitch-world-model
!pip install -e . --no-deps
```

## Cell 2: GPU Check

```python
import platform
import torch

print("python:", platform.python_version())
print("torch:", torch.__version__)
print("cuda_available:", torch.cuda.is_available())
print("gpu:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
assert torch.cuda.is_available(), "Stop: enable a Kaggle GPU before training."
```

## Cell 3: Protocol Dry-Run

```bash
!python scripts/run_kaggle_video_autoencoder.py \
  --dry-run \
  --manifest /kaggle/input/TEN-DATASET/tempglitch_phase3b/manifest.csv \
  --split /kaggle/input/TEN-DATASET/split.csv \
  --clips-root /kaggle/input/TEN-DATASET/tempglitch_phase3b \
  --output-root /kaggle/working/tempglitch_phase6e/seed_42 \
  --device cuda
```

Stop unless output reports `1724` train-normal clips, `1071` validation clips, and
`Test clips scored: False`.

## Cell 4: Train And Score Validation

```bash
!python scripts/run_kaggle_video_autoencoder.py \
  --manifest /kaggle/input/TEN-DATASET/tempglitch_phase3b/manifest.csv \
  --split /kaggle/input/TEN-DATASET/split.csv \
  --clips-root /kaggle/input/TEN-DATASET/tempglitch_phase3b \
  --output-root /kaggle/working/tempglitch_phase6e/seed_42 \
  --device cuda \
  --image-size 64 \
  --clip-length 16 \
  --batch-size 8 \
  --epochs 10 \
  --learning-rate 0.001 \
  --seed 42
```

## Cell 5: Verify Outputs

```python
from pathlib import Path
import json
import pandas as pd

root = Path("/kaggle/working/tempglitch_phase6e/seed_42")
required = [
    "protocol_audit.json",
    "train_normal_manifest.csv",
    "validation_manifest.csv",
    "video_autoencoder.pt",
    "training_metadata.json",
    "validation_scores.csv",
    "phase6e_summary.json",
]
for name in required:
    path = root / name
    print(name, "OK" if path.exists() else "MISSING", path)
    assert path.exists(), f"Missing required artifact: {name}"

metadata = json.loads((root / "training_metadata.json").read_text())
summary = json.loads((root / "phase6e_summary.json").read_text())
print("device:", metadata.get("device"))
print("epoch_losses:", metadata.get("epoch_losses"))
print("test_materialized:", summary.get("test_materialized"))
print("test_scored:", summary.get("test_scored"))

scores = pd.read_csv(root / "validation_scores.csv")
print(scores.head())
print("rows:", len(scores))
print("nan score count:", scores["score"].isna().sum())

assert "cuda" in str(metadata.get("device", "")).lower()
assert len(scores) == 1071
assert scores["score"].isna().sum() == 0
assert summary.get("test_materialized") is False
assert summary.get("test_scored") is False
```
