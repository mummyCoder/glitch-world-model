# Agent Governance Source Notes

Reviewed on June 11, 2026. These references informed the repository's agent-facing files. No
code from the references was executed.

| Source | Primary reference | Applied lesson |
| --- | --- | --- |
| AGENTS.md | `https://github.com/agentsmd/agents.md` at commit `d1ac7f063d20e70015ed6732664049ae4ba9d74e` | Keep repository instructions discoverable, scoped, and operational. The read-only review clone lives under ignored `_external_references/agent_governance/agents.md`. |
| GitHub Copilot | `https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions` | Use `.github/copilot-instructions.md` for repository-wide context and `.github/instructions/*.instructions.md` with `applyTo` for path-specific rules. |
| Claude Code | `https://code.claude.com/docs/en/memory` | Keep `CLAUDE.md` concise and import the canonical repository guidance with `@AGENTS.md`. |
| Aider | `https://aider.chat/docs/usage/conventions.html` and `https://aider.chat/docs/config/aider_conf.html` | Keep shared conventions in `CONVENTIONS.md` and load policy files read-only through `.aider.conf.yml`. |
| pre-commit | `https://pre-commit.com/` | Define repository hooks in `.pre-commit-config.yaml` and verify all tracked files with `pre-commit run --all-files`. |

## Security Review

- Reference material was read as documentation only.
- No downloaded scripts, hooks, binaries, or package installers were executed.
- `_external_references/` is ignored and must never become a source of executable trust.
- Local hooks call only repository-owned validators or pinned standard hook repositories.
