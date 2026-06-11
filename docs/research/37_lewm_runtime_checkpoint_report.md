# Gate 2 LeWM Runtime And Checkpoint Report

Date: June 10, 2026

## Verified Runtime

- Python: `3.10.12`, isolated under ignored `outputs/lewm_runtime/.venv`.
- Runtime lock: `requirements/lewm-runtime.txt`.
- LeWM upstream commit: `8edfeb336732b5f3ce7b8b210d0ba370a09e2cac`.
- Stable WorldModel: `0.1.1`.
- Stable Pretraining: `0.1.7`.
- Transformers: `4.57.6`.
- Torch: `2.12.0+cpu`.

`transformers==5.11.0` was rejected because strict checkpoint loading produced incompatible ViT
state-dict keys. Pinning `4.57.6` produced an exact strict load.

## Verified Checkpoint

- Official repository: `quentinll/lewm-pusht`.
- Files downloaded outside Git: `config.json`, `weights.pt`.
- Weights SHA-256:
  `48938400ae3464c9680731287f583a9cb516f55a8ec64ea13a91be47fb15b607`.
- Model class: `stable_worldmodel.wm.lewm.lewm.LeWM`.
- Parameter count: `18,034,478`.
- Contract: image size `224`, history `3`, action dimension `10`.

A CPU inference smoke with `(1,4,3,224,224)` pixels and `(1,4,10)` actions produced finite
surprise with shape `(1,3)`.

## Claim Status

Checkpoint loading and non-gameplay inference are verified engineering results. Gameplay
training, gameplay scoring, SIGReg benefit, LeWM glitch-detection performance, and locked-test
results remain experiment-pending.

