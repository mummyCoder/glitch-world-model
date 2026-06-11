from __future__ import annotations

import importlib.util
import platform
import subprocess
import sys
from pathlib import Path

try:
    from update_context_cache import context_validation_errors
except ModuleNotFoundError:  # pragma: no cover - exercised by package imports in tests.
    from scripts.update_context_cache import context_validation_errors

CORE_IMPORTS = {
    "numpy": "numpy",
    "PIL": "Pillow",
    "pytest": "pytest",
}
OPTIONAL_IMPORTS = {
    "ruff": "ruff",
    "pre_commit": "pre-commit",
}
REQUIRED_PATHS = [
    "README.md",
    "AGENTS.md",
    "PLAYBOOK.md",
    "RULES.md",
    "CLAUDE.md",
    "CONVENTIONS.md",
    ".github/copilot-instructions.md",
    ".codex/skills",
    "pyproject.toml",
    "docs/context",
    "docs/research",
]
GITIGNORE_PROBES = [
    "data/raw/probe.file",
    "data/processed/probe.file",
    "outputs/probe.file",
    "checkpoints/probe.ckpt",
    ".test-tmp/probe.file",
    "_external_references/probe.file",
    "probe.lance/data.bin",
    "kaggle.json",
]


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def check_gitignored(repo_root: Path, path: str) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=repo_root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
    return result.returncode == 0


def collect_report(repo_root: Path) -> dict[str, object]:
    core_imports = {name: module_available(name) for name in CORE_IMPORTS}
    optional_imports = {name: module_available(name) for name in OPTIONAL_IMPORTS}
    required_paths = {path: (repo_root / path).exists() for path in REQUIRED_PATHS}
    gitignore_checks = {path: check_gitignored(repo_root, path) for path in GITIGNORE_PROBES}
    context_errors = context_validation_errors(repo_root)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "repo_root": str(repo_root),
        "core_imports": core_imports,
        "optional_imports": optional_imports,
        "required_paths": required_paths,
        "gitignore_checks": gitignore_checks,
        "context_cache_errors": context_errors,
    }


def print_report(report: dict[str, object]) -> None:
    print("Glitch World Model Doctor")
    print(f"Python: {report['python']}")
    print(f"Platform: {report['platform']}")
    print(f"Repo root: {report['repo_root']}")

    print("\nCore imports:")
    for module_name, ok in dict(report["core_imports"]).items():
        package_name = CORE_IMPORTS[module_name]
        print(f"- {package_name}: {'OK' if ok else 'MISSING'}")

    print("\nOptional tooling imports:")
    for module_name, ok in dict(report["optional_imports"]).items():
        package_name = OPTIONAL_IMPORTS[module_name]
        print(f"- {package_name}: {'OK' if ok else 'not installed'}")

    print("\nRequired paths:")
    for path, ok in dict(report["required_paths"]).items():
        print(f"- {path}: {'OK' if ok else 'MISSING'}")

    print("\nContext cache:")
    context_errors = list(report["context_cache_errors"])
    if context_errors:
        print("- status: FAIL")
        for error in context_errors:
            print(f"  - {error}")
    else:
        print("- status: OK")

    print("\nGitignore probes:")
    for path, ok in dict(report["gitignore_checks"]).items():
        if ok is None:
            status = "not checked"
        else:
            status = "OK" if ok else "NOT IGNORED"
        print(f"- {path}: {status}")


def core_requirements_satisfied(report: dict[str, object]) -> bool:
    return (
        all(dict(report["core_imports"]).values())
        and all(dict(report["required_paths"]).values())
        and not list(report["context_cache_errors"])
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    report = collect_report(repo_root)
    print_report(report)
    return 0 if core_requirements_satisfied(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
