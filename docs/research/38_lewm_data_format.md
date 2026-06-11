# Gate 3-4 LeWM Data Contract

## Split Contract

`lewm_protocol.py` assigns deterministic hash-based splits at the pair or episode group level.
Previously exposed groups are restricted to train or validation and cannot enter locked test.
Episodes are split before temporal windows are generated.

The frozen intermediate split columns are:

```text
dataset_id,source,episode_id,category,label,split,pair_id,action_mode
```

## Installed Writer And Reader

The verified runtime uses `stable_worldmodel.data.LanceWriter` and `LanceDataset`.

- Writer-managed columns: `episode_idx`, `step_idx`.
- Required model columns: `pixels`, `action`.
- Provenance columns: dataset, source episode, label, category, split, pair, action mode.
- Pixel storage: RGB uint8 frames encoded by the upstream writer.
- Action storage: float32 vectors synchronized one per frame.

TempGlitch uses explicit one-dimensional zero actions. WOB must provide synchronized real action
arrays; missing or length-mismatched actions are rejected.

## Verification Evidence

A generated five-episode dataset, six frames per episode, loaded through the installed upstream
reader with `num_steps=4`. It produced 15 windows with pixels shaped `(4,3,32,32)` and actions
shaped `(4,1)`. The reader generated windows within writer-managed episode boundaries.

Locked test remains unmaterialized and unscored.

