# Coding Conventions

- Use Python type hints for public functions and non-obvious internal contracts.
- Keep core modules importable without PyTorch, OpenCV, Kaggle, or LeWM dependencies.
- Preserve `manifest.csv`, labels CSV, `scores.csv`, and `metrics.json` interfaces.
- Keep scorers registered through `src/glitch_detection/score_clips.py`.
- Add or update focused tests before behavioral implementation.
- Prefer `pathlib`, dataclasses, structured JSON/CSV parsing, and explicit validation.
- Keep commands dry-run and validation-only by default when external state is involved.
- Do not commit data, outputs, checkpoints, Lance datasets, credentials, or caches.
- Keep comments concise and explain only non-obvious scientific or safety constraints.
- Do not turn proxies, fixtures, smoke runs, or scaffolding into scientific claims.
