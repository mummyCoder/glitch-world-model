# Kaggle GPU Protocol

1. Keep `kaggle.json` outside the repository and never print credentials.
2. Dry-run data/package/protocol checks locally.
3. Scan the upload package for credentials and prohibited files.
4. Use standing authorization for non-locked-test dataset and kernel actions after validation.
5. Record content fingerprints as audit and idempotency keys.
6. Poll without duplicate pushes; download only required artifacts.
7. Validate artifacts locally before making claims.
8. Public release additionally requires a license, redistribution permission, and locked-test scan.
9. Never touch locked test without a separate direct user command.

## R3 LeWM Seed Runs

- R3 seed 42 must run on a GPU with CUDA compute capability `sm_70` or newer for the current
  Kaggle PyTorch container.
- Tesla P100 is compute capability `sm_60` and is unsupported by the observed Kaggle PyTorch
  `2.10.0+cu128` build.
- Acceptable accelerators are T4 or newer. If Kaggle assigns P100, stop before training and relaunch
  only after selecting or obtaining a compatible accelerator.
- Seed 43/44 must not launch until seed 42 produces valid non-locked R3 artifacts.

Remote deletion, credential publication, unlicensed public data, and validator bypass are not
authorized.
