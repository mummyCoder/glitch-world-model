# Experiment Tracking

Every executed run must record:

- git SHA and dirty-state flag
- UTC timestamp, command, host/runtime, Python and package versions
- device/GPU model and deterministic limitations
- dataset identity/revision and dataset hash
- split seed, grouping policy, exposure history, and split hash
- full config and config hash
- checkpoint source and checkpoint hash
- score file hash and metrics file hash
- action mode, fit split, threshold source, and locked-test flags
- allowed claim scope and known limitations

Store the canonical metadata beside ignored run artifacts. Paper tables must trace back to these
records.

MLflow, Weights & Biases, DVC, and Hydra are optional tools. They may index or reproduce
artifacts, but they do not replace the repository interfaces, hashes, release gates, or claim
registry. Do not make network tracking mandatory in default CI.
