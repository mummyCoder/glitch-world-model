# Runtime Management

## Default Development Runtime

- Python 3.10+ with `.[dev]`
- lightweight core dependencies only
- no PyTorch, LeWM, OpenCV, Kaggle, or tracking requirement in default CI

Create with:

```powershell
uv venv
uv pip install -e ".[dev]"
```

Pip is an accepted fallback. Record the installer and Python version used.

## LeWM Runtime

Use an isolated Python 3.10 environment with `requirements/lewm-runtime.txt`. Do not install the
LeWM stack into the default CI environment. Preserve strict checkpoint/runtime compatibility.

## Lock And Upgrade Policy

- Pin audited LeWM dependencies exactly.
- Use `uv pip compile`/frozen lock workflows when introducing a maintained lock file.
- Change one dependency boundary at a time and rerun checkpoint-load and interface tests.
- Keep optional imports fail-closed with actionable errors.
- Do not silently upgrade model runtimes for an existing checkpoint artifact.
