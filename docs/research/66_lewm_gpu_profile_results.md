# LeWM Research MVP GPU Profile Results

Date: 2026-06-13

Evidence class: engineering-profile-only

## Scope

This record covers the non-locked, research-MVP LeWM GPU profile only. It measures runtime,
throughput, VRAM, and checkpoint/artifact integrity for an exact 500 optimizer-update profile.
It does not report AUROC, AUPRC, detection performance, paper conclusions, or locked-test results.

## Final Validated Run

- Run root: `outputs/lewm_gpu_profile_live_6`
- Artifact root: `outputs/lewm_gpu_profile_live_6/attempts/694390b59b874dfc11e16c6ed7774d847c944485f09b655fd3c019b200a2596d/downloaded`
- Kernel slug: `huynhdieuthanh/lewm-profile-b8-694390b59b`
- Git SHA: `ff372c9ec50edbd517024e92ef058cafadfd4abc`
- Branch: `main`
- Fingerprint: `694390b59b874dfc11e16c6ed7774d847c944485f09b655fd3c019b200a2596d`
- Dataset manifest hash: `3389b6cca04429da689aa75032907bf002fa2ca0ff2891ebe002fbdf88d7ef45`
- Config hash: `c97e0a4313992b65818197bea5f9d6ccc7a84b6a0632285809b049dbc9c11765`
- Batch size: 8
- AMP: true
- Device: CUDA
- Updates completed: 500
- Validation-normal batches completed: 8
- Wall-clock runtime: 39.31089395899994 seconds
- Training runtime: 38.275576467000064 seconds
- Throughput: 13.063160536094955 updates/sec
- Peak VRAM: 512040448 bytes
- Average VRAM: 313221003.264 bytes
- Checkpoint SHA256: `cc26f5cf3f41af4ad4c49bd6f53997aeb23bc6af3d048420e2348ce3a57bf3ea`

## Integrity Checks

The final downloaded artifact set includes:

- `PROFILE_REPORT.md`
- `profile_metadata.json`
- `artifact_manifest.json`
- `environment_snapshot.json`
- `checkpoint_hashes.json`
- `retry_history.json`
- `validator_report.json`
- `checkpoint.pt`
- `profile.log`
- `loss_history.json`
- Kaggle execution log

The validator report confirms:

- weights reload verified
- optimizer reload verified
- scheduler absence/presence handling verified
- reloaded global step equals 500
- no buggy validation materialization
- no locked-test materialization or scoring
- no performance claims reported

The artifact manifest hashes `validator_report.json`, metadata, checkpoint hashes, retry history,
checkpoint, profile report, and logs.

## Attempt History

- `outputs/lewm_gpu_profile_live_4`: completed the 500-update engineering profile but predated the
  `validator_report.json` artifact contract, so it is not the final deliverable set.
- `outputs/lewm_gpu_profile_live_5`: exposed a stale-source/artifact-contract failure where the
  Kaggle runtime reused an old `/tmp/glitch-world-model` source tree. Commit `ff372c9` now clears
  the Kaggle `/tmp` code/input roots, disables bytecode writes, and self-checks the project snapshot
  before import.
- `outputs/lewm_gpu_profile_live_6`: final validated 500-update profile with complete artifact set.

## Claim Boundary

This is engineering evidence that the research-MVP profile can complete 500 CUDA optimizer updates
with strict checkpoint and artifact validation on the non-locked normal-only profile path. It is not
evidence of glitch detection quality, baseline superiority, temporal localization, SIGReg benefit,
or locked-test performance.
