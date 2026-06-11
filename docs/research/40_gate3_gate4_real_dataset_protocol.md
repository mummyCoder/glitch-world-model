# Gates 3-4 Real Dataset Protocol Report

## Status

- Gate 3 dataset protocol: verified on 2026-06-11.
- Gate 4 conversion and upstream-loader proof: verified on 2026-06-11.
- Locked test: metadata-only, unmaterialized, and unscored.
- Gameplay LeWM training and scoring: experiment-pending.

Generated split, provenance, audit, tar, video, and Lance artifacts remain under ignored `data/`
and `outputs/` paths.

## TempGlitch Frozen Protocol

- Public source: `asgaardlab/TempGlitch`.
- Locked Hugging Face revision: `1d46a63c31ebfe3b675b51a2231d547da372eff9`.
- Metadata rows: 1,500 videos.
- Pairing: 750 conservative category/source-name heuristic pairs.
- Previously exposed groups: 65 groups from the existing 100-video Phase 3B slice; none enter
  locked test.
- Per category: 90 normal train videos, 60 validation videos, 60 locked-test metadata videos,
  and 90 buggy videos excluded from train.
- Aggregate: 450 train-normal, 300 validation, 300 locked-test metadata, 450 excluded buggy
  train-pair members.

Audit results: zero cross-split groups, duplicate sources, duplicate episodes, non-normal train
rows, exposed test groups, or materialized test rows.

## World Of Bugs Frozen Protocol

- Public Kaggle sources:
  - `benedictwilkinsai/world-of-bugs-normal`
  - `benedictwilkinsai/world-of-bugs-test`
- License: ODC Attribution License (ODC-By).
- Main normal inventory: 60 episodes. The duplicate `NORMAL-TRAIN-SMALL` subset is excluded.
- Bug inventory: 119 episodes across 10 bug categories.
- Frozen split: 48 normal train, 12 normal validation, 60 bug validation, and 59 locked-test
  metadata episodes.

The tar audit reads numeric fields with `allow_pickle=False`. Each inspected timestep contains
`state`, `action`, `reward`, and `done`; state is float32 CHW RGB `(3,84,84)` and action is a
scalar discrete value. The converter maps the four navigation actions to one-hot vectors. The
upstream writer contract associates `state_t` and `action_t`, and the public dataset description
states that observations and actions were collected together. A tar-only audit cannot independently
prove the physical semantics of every action, so that limitation remains explicit.

## Upstream Loader Proof

The isolated Python 3.10 LeWM runtime converted and loaded:

| Dataset | Partition | Episodes | Windows | Pixels | Action |
| --- | --- | ---: | ---: | --- | --- |
| TempGlitch | train | 5 | 65 | `(4,3,112,112)` | `(4,1)` zero-action |
| TempGlitch | validation | 5 | 65 | `(4,3,112,112)` | `(4,1)` zero-action |
| World of Bugs | train | 5 | 65 | `(4,3,84,84)` | `(4,4)` real one-hot |
| World of Bugs | validation | 5 | 65 | `(4,3,84,84)` | `(4,4)` real one-hot |

All samples were loaded by `stable_worldmodel.data.LanceDataset`. Windows remain inside
writer-managed episode boundaries. Conversion commands do not accept a test partition.

## Remaining Risks

- TempGlitch pair IDs are conservative filename heuristics, not official pair annotations.
- Full TempGlitch and WOB train/validation materialization must run as Kaggle shards.
- WOB action semantics are supported by the upstream writer contract and structural tar audit,
  but not by a replay-based synchronization test.
- No Gate 5 CUDA smoke, gameplay checkpoint, validation surprise score, or LeWM paper result
  exists yet.
