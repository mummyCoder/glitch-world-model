# Gate 3-4 LeWM Data Contract

## Split Contract

`dataset_protocols.py` assigns deterministic category-stratified splits at the pair or episode
group level. Previously exposed groups are restricted to train or validation and cannot enter
locked test. Episodes are split before temporal windows are generated.

The frozen intermediate split columns are:

```text
dataset_id,source,episode_id,pair_id,category,label,split,action_mode,use_for_training,materialize
```

## Installed Writer And Reader

The verified runtime uses `stable_worldmodel.data.LanceWriter` and `LanceDataset`.

- Writer-managed columns: `episode_idx`, `step_idx`.
- Required model columns: `pixels`, `action`.
- Provenance columns: dataset, source episode, label, category, split, pair, action mode.
- Pixel storage: RGB uint8 frames encoded by the upstream writer.
- Action storage: float32 vectors synchronized one per frame.

TempGlitch uses explicit one-dimensional zero actions. WOB scalar discrete navigation actions are
validated and converted to four-dimensional one-hot real-action vectors. Missing, invalid, or
length-mismatched actions are rejected. Optional WOB `info` object arrays are never unpickled.

## Verification Evidence

A generated five-episode fixture first verified the installed writer contract. Real-data Gate 4
then loaded five train and five validation episodes from each primary dataset. TempGlitch produced
65 windows per partition with pixels `(4,3,112,112)` and zero actions `(4,1)`. WOB produced 65
windows per partition with pixels `(4,3,84,84)` and real one-hot actions `(4,4)`. The reader
generated windows within writer-managed episode boundaries.

Locked test remains unmaterialized and unscored.
