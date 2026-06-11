from pathlib import Path

from scripts.doctor import collect_report, core_requirements_satisfied


def test_doctor_core_requirements_are_available():
    repo_root = Path(__file__).resolve().parents[1]
    report = collect_report(repo_root)

    assert core_requirements_satisfied(report)
    assert report["required_paths"]["README.md"]
    assert report["required_paths"]["AGENTS.md"]
    assert report["required_paths"]["RULES.md"]
    assert report["required_paths"]["CLAUDE.md"]
    assert report["required_paths"]["CONVENTIONS.md"]
    assert report["required_paths"][".github/copilot-instructions.md"]
    assert report["required_paths"][".codex/skills"]
    assert report["gitignore_checks"]["_external_references/probe.file"]
    assert report["gitignore_checks"]["probe.lance/data.bin"]
    assert report["gitignore_checks"]["kaggle.json"]
