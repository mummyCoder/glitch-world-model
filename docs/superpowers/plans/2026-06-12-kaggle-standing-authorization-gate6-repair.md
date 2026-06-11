# Kaggle Standing Authorization And Gate 6 Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace per-action Kaggle approvals with audited standing authorization, repair Gate 6 as a single-file Kaggle kernel, and automatically publish, run, download, and strictly validate one fresh Gate 6 version while keeping locked test closed.

**Architecture:** Add a reusable `KaggleExecutionPolicy` and public-release validator to the existing Kaggle automation foundation, then remove approval states from the resumable orchestrator. Keep Gate 6 packaging in `lewm_gate6.py`, add Gate 6-specific handlers in a focused automation module, and expose a thin dry-run/live CLI. Fingerprints remain audit and idempotency keys; locked-test flags, release licensing, credentials, retries, and one-push-per-fingerprint remain fail-closed.

**Tech Stack:** Python 3.14 default environment, Python standard library, existing Kaggle CLI 2.2.1 module invocation, pytest, Ruff, pre-commit, existing LeWM Python 3.10/Kaggle runtime contracts.

---

## File Structure

### Governance And Context

- Modify: `RULES.md`
- Modify: `AGENTS.md`
- Modify: `PLAYBOOK.md`
- Rename: `docs/workflows/kaggle_live_approval.md` to `docs/workflows/kaggle_automation_policy.md`
- Modify: `docs/workflows/kaggle_gpu_protocol.md`
- Modify: `README.md`
- Modify: `scripts/update_context_cache.py`
- Modify: `tests/test_research_release_tools.py`
- Create: `tests/test_kaggle_governance.py`

### Reusable Kaggle Automation

- Modify: `src/glitch_detection/kaggle_automation.py`
- Modify: `scripts/run_phase6e_kaggle_automation.py`
- Modify: `tests/test_kaggle_automation_foundation.py`
- Modify: `tests/test_kaggle_automation_orchestrator.py`
- Modify: `tests/test_kaggle_automation_validation.py`
- Modify: `tests/test_phase6e_kaggle_docs.py`

`kaggle_automation.py` remains the shared home for state persistence, fingerprints, command
execution, release validation, retry classification, policy decisions, and the generic
orchestrator. Do not move LeWM-specific package construction into it.

### LeWM Package Audit

- Modify: `src/glitch_detection/lewm_kaggle.py`
- Delete: `scripts/request_lewm_kaggle_approvals.py`
- Modify: `tests/test_lewm_kaggle.py`

`lewm_kaggle.py` keeps Gate 5 package generation and strict artifact validation, but replaces
approval requests with immutable audit manifests.

### Gate 6 Packaging And Execution

- Modify: `src/glitch_detection/lewm_gate6.py`
- Create: `src/glitch_detection/lewm_gate6_automation.py`
- Modify: `scripts/prepare_lewm_gate6_package.py`
- Create: `scripts/run_lewm_gate6_automation.py`
- Modify: `tests/test_lewm_gate6.py`
- Create: `tests/test_lewm_gate6_automation.py`

`lewm_gate6.py` owns deterministic source embedding and strict package/artifact validation.
`lewm_gate6_automation.py` owns remote lifecycle handling and audit files.

### Evidence And Release

- Modify: `configs/lewm_gate6_pilot.yaml`
- Modify: `docs/research/45_gate6_lewm_normal_training_plan.md`
- Modify: `docs/research/46_gate6_lewm_training_pilot_results.md`
- Modify: `docs/research/62_artifact_manifest.md`
- Modify: `docs/research/64_kaggle_kernel_write_path_repair.md`
- Modify: `docs/research/16_claim_registry.md` only after strict validation passes
- Modify: `docs/context/LAST_HANDOFF.md`

Preserve the current unrelated or pre-existing worktree changes. In particular, review and build
on the existing modifications in `tests/test_lewm_gate6.py`,
`tests/test_kaggle_submission_diagnostics.py`, `scripts/repair_kaggle_kernel_write_path.py`, and
`docs/research/64_kaggle_kernel_write_path_repair.md`; do not revert them.

---

### Task 1: Encode Standing Authorization In Governance

**Files:**
- Create: `tests/test_kaggle_governance.py`
- Modify: `RULES.md`
- Modify: `AGENTS.md`
- Modify: `PLAYBOOK.md`
- Rename: `docs/workflows/kaggle_live_approval.md` to `docs/workflows/kaggle_automation_policy.md`
- Modify: `docs/workflows/kaggle_gpu_protocol.md`
- Modify: `README.md`
- Modify: `scripts/update_context_cache.py`
- Modify: `tests/test_research_release_tools.py`

- [ ] **Step 1: Write the failing governance test**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_kaggle_governance_uses_standing_authorization_and_keeps_locked_test_separate():
    rules = (ROOT / "RULES.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    playbook = (ROOT / "PLAYBOOK.md").read_text(encoding="utf-8")
    workflow = (ROOT / "docs/workflows/kaggle_automation_policy.md").read_text(
        encoding="utf-8"
    )
    combined = "\n".join([rules, agents, playbook, workflow]).lower()

    assert "standing authorization" in combined
    assert "dataset upload and kernel push require separate" not in combined
    assert "fingerprint-bound approval" not in combined
    assert "locked test" in combined
    assert "separate direct user command" in combined
    assert "public" in workflow
    assert "delete" in workflow
    assert "not authorized" in workflow


def test_context_generator_emits_standing_authorization_policy():
    generator = (ROOT / "scripts/update_context_cache.py").read_text(encoding="utf-8")

    assert "standing Kaggle authorization" in generator
    assert "fingerprint-bound approval" not in generator
    assert "kaggle_automation_policy.md" in generator
```

- [ ] **Step 2: Run the governance test and verify it fails**

Run:

```powershell
python -m pytest tests/test_kaggle_governance.py -v
```

Expected: FAIL because the workflow still has the old filename and the current rules require
per-action approval.

- [ ] **Step 3: Rename the workflow and replace the policy text**

Rename the file with `Move-Item`, then make the new workflow contain these exact policy sections:

```markdown
# Kaggle Automation Policy

## Standing Authorization

Codex may perform all non-locked-test Kaggle actions without a per-action approval artifact:
dataset create/version, kernel push/version, GPU execution, polling, artifact download, and
public publication after validation.

Fingerprints are audit identifiers and idempotency keys. They are not permissions.

## Locked-Test Boundary

Locked-test materialization or scoring is not covered by standing authorization and requires a
separate direct user command naming the frozen configuration and claim scope.

## Public Release Gate

Public datasets and kernels require credential scanning, locked-test scanning, an inventory,
recorded license and redistribution permission, explicit owner/slug metadata, and false
locked-test flags.

## Prohibited Actions

Automation is not authorized to delete remote Kaggle resources, publish credentials or private
data, weaken validators, bypass gate order, or retry a runtime failure without a changed
fingerprint.

## Retry And Audit

Transient network failures may retry at most three times. A remote version is pushed once per
kernel fingerprint; established versions are polled rather than resubmitted. Commands, hashes,
visibility, remote versions, outcomes, and downloaded artifact hashes are recorded under ignored
outputs.
```

- [ ] **Step 4: Update governance source text and generated context templates**

Use these exact policy statements in `RULES.md` and mirror them in `AGENTS.md` and `PLAYBOOK.md`:

```markdown
- Kaggle dataset upload/version, kernel push/version, GPU execution, polling, artifact download,
  and validated public publication operate under repository standing authorization.
- Kaggle fingerprints remain mandatory audit and idempotency records; no request/approved/
  consumed approval artifact is required.
- Locked-test materialization or scoring still requires a separate direct user command.
- Remote deletion, credential publication, unlicensed public data, and validator bypass remain
  prohibited.
```

In `scripts/update_context_cache.py`, replace every generated approval requirement with:

```python
- Non-locked-test Kaggle actions use standing authorization after security, license, protocol,
  and package validation.
- Fingerprints are audit/idempotency records, not approval artifacts.
- Locked-test materialization or scoring requires a separate direct user command.
```

Update the task router template to reference
`docs/workflows/kaggle_automation_policy.md` and remove
`scripts/request_lewm_kaggle_approvals.py`.

- [ ] **Step 5: Update release-validator expectations**

Change `tests/test_research_release_tools.py` so the required workflow path is:

```python
"docs/workflows/kaggle_automation_policy.md",
```

and no longer expects `docs/workflows/kaggle_live_approval.md`.

- [ ] **Step 6: Regenerate and validate context**

Run:

```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
python -m pytest tests/test_kaggle_governance.py tests/test_research_release_tools.py -v
```

Expected: all commands PASS, and generated context describes v6 as a runtime packaging failure,
not a write-path blocker.

- [ ] **Step 7: Commit governance**

```powershell
git add RULES.md AGENTS.md PLAYBOOK.md README.md scripts/update_context_cache.py tests/test_kaggle_governance.py tests/test_research_release_tools.py docs/workflows/kaggle_automation_policy.md docs/workflows/kaggle_gpu_protocol.md docs/context
git add -u docs/workflows/kaggle_live_approval.md
git commit -m "docs(kaggle): adopt standing automation authorization"
```

---

### Task 2: Replace Approval Storage With Execution Policy

**Files:**
- Modify: `src/glitch_detection/kaggle_automation.py`
- Modify: `tests/test_kaggle_automation_foundation.py`
- Modify: `tests/test_kaggle_automation_validation.py`

- [ ] **Step 1: Replace approval tests with policy and public-release tests**

Remove `ApprovalStore` imports and its one-time approval test. Add:

```python
from glitch_detection.kaggle_automation import (
    KaggleAction,
    KaggleExecutionPolicy,
    PublicReleaseSpec,
)


def test_execution_policy_authorizes_public_nonlocked_kaggle_actions():
    policy = KaggleExecutionPolicy()
    result = policy.authorize(
        KaggleAction(
            action="kernel_push",
            fingerprint="kernel-fp",
            visibility="public",
            locked_test_materialized=False,
            locked_test_scored=False,
            redistribution_allowed=True,
        )
    )

    assert result["authorized"] is True
    assert result["authorization"] == "standing"
    assert result["fingerprint"] == "kernel-fp"


@pytest.mark.parametrize("flag", ["locked_test_materialized", "locked_test_scored"])
def test_execution_policy_rejects_locked_test_without_separate_release(flag: str):
    values = {
        "action": "kernel_push",
        "fingerprint": "kernel-fp",
        "visibility": "public",
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "redistribution_allowed": True,
    }
    values[flag] = True

    with pytest.raises(SecurityViolation, match="locked test"):
        KaggleExecutionPolicy().authorize(KaggleAction(**values))


def test_execution_policy_rejects_public_dataset_without_redistribution_permission():
    with pytest.raises(SecurityViolation, match="redistribution"):
        KaggleExecutionPolicy().authorize(
            KaggleAction(
                action="dataset_create_or_version",
                fingerprint="dataset-fp",
                visibility="public",
                locked_test_materialized=False,
                locked_test_scored=False,
                redistribution_allowed=False,
            )
        )
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_kaggle_automation_foundation.py -v
```

Expected: FAIL because `KaggleAction`, `KaggleExecutionPolicy`, and `PublicReleaseSpec` do not
exist.

- [ ] **Step 3: Implement the policy types and remove `ApprovalStore`**

Add these definitions after `StateStore`:

```python
from typing import Any, Literal

KaggleVisibility = Literal["private", "public"]
KaggleActionName = Literal["dataset_create_or_version", "kernel_push"]


@dataclass(frozen=True)
class PublicReleaseSpec:
    visibility: KaggleVisibility
    license_name: str
    redistribution_allowed: bool
    locked_test_materialized: bool = False
    locked_test_scored: bool = False


@dataclass(frozen=True)
class KaggleAction:
    action: KaggleActionName
    fingerprint: str
    visibility: KaggleVisibility
    locked_test_materialized: bool
    locked_test_scored: bool
    redistribution_allowed: bool


class KaggleExecutionPolicy:
    def authorize(self, action: KaggleAction) -> dict[str, Any]:
        if action.locked_test_materialized or action.locked_test_scored:
            raise SecurityViolation(
                "Kaggle standing authorization does not include locked test access."
            )
        if (
            action.action == "dataset_create_or_version"
            and action.visibility == "public"
            and not action.redistribution_allowed
        ):
            raise SecurityViolation(
                "Public Kaggle dataset publication requires redistribution permission."
            )
        return {
            "authorized": True,
            "authorization": "standing",
            "action": action.action,
            "fingerprint": action.fingerprint,
            "visibility": action.visibility,
        }
```

Delete the `ApprovalStore` class entirely. Keep `FingerprintBuilder` unchanged.

- [ ] **Step 4: Add locked-path and public-release scanning**

Add to `SecurityGuard`:

```python
LOCKED_TEST_PATH_PATTERN = re.compile(
    r"(?i)(^|[/_.-])locked([_-]?test)?([/_.-]|$)"
)

def scan_public_release(
    self,
    root: Path,
    *,
    package_kind: str,
    spec: PublicReleaseSpec,
) -> dict[str, Any]:
    self.scan_package(root, package_kind=package_kind)
    if spec.locked_test_materialized or spec.locked_test_scored:
        raise SecurityViolation("Public release indicates locked test access.")
    for path in root.rglob("*"):
        if path.is_file() and self.LOCKED_TEST_PATH_PATTERN.search(
            path.relative_to(root).as_posix()
        ):
            raise SecurityViolation(
                f"Public release contains a locked-test path: {path.relative_to(root)}"
            )
    if spec.visibility == "public":
        if not spec.license_name.strip():
            raise SecurityViolation("Public release requires a recorded license.")
        if not spec.redistribution_allowed:
            raise SecurityViolation(
                "Public release requires recorded redistribution permission."
            )
    return {
        "visibility": spec.visibility,
        "license": spec.license_name,
        "redistribution_allowed": spec.redistribution_allowed,
        "inventory_sha256": FingerprintBuilder.inventory_sha256(root),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
```

Do not reject source text containing the literal keys `locked_test_materialized` and
`locked_test_scored`; only reject true structured flags and forbidden path names.

- [ ] **Step 5: Add public-release tests**

Add to `tests/test_kaggle_automation_validation.py`:

```python
def test_public_release_scan_requires_license_and_redistribution(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    (root / "manifest.csv").write_text("source\nclip-a\n", encoding="utf-8")

    with pytest.raises(SecurityViolation, match="license"):
        SecurityGuard().scan_public_release(
            root,
            package_kind="dataset",
            spec=PublicReleaseSpec(
                visibility="public",
                license_name="",
                redistribution_allowed=True,
            ),
        )

    with pytest.raises(SecurityViolation, match="redistribution"):
        SecurityGuard().scan_public_release(
            root,
            package_kind="dataset",
            spec=PublicReleaseSpec(
                visibility="public",
                license_name="MIT",
                redistribution_allowed=False,
            ),
        )


def test_public_release_scan_rejects_locked_test_path(tmp_path: Path):
    root = tmp_path / "dataset"
    path = root / "locked_test" / "manifest.csv"
    path.parent.mkdir(parents=True)
    path.write_text("source\nclip-a\n", encoding="utf-8")

    with pytest.raises(SecurityViolation, match="locked-test path"):
        SecurityGuard().scan_public_release(
            root,
            package_kind="dataset",
            spec=PublicReleaseSpec(
                visibility="public",
                license_name="MIT",
                redistribution_allowed=True,
            ),
        )
```

- [ ] **Step 6: Run focused tests**

Run:

```powershell
python -m pytest tests/test_kaggle_automation_foundation.py tests/test_kaggle_automation_validation.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit the policy engine**

```powershell
git add src/glitch_detection/kaggle_automation.py tests/test_kaggle_automation_foundation.py tests/test_kaggle_automation_validation.py
git commit -m "feat(kaggle): add standing execution policy"
```

---

### Task 3: Remove Approval Stops From The Resumable Orchestrator

**Files:**
- Modify: `src/glitch_detection/kaggle_automation.py`
- Modify: `scripts/run_phase6e_kaggle_automation.py`
- Modify: `tests/test_kaggle_automation_orchestrator.py`
- Modify: `tests/test_kaggle_automation_validation.py`
- Modify: `tests/test_phase6e_kaggle_docs.py`

- [ ] **Step 1: Rewrite orchestrator tests for direct standing authorization**

Replace approval-specific tests with:

```python
def test_live_orchestrator_runs_dataset_and_kernel_without_approval_stop(tmp_path: Path):
    calls: list[str] = []
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=False,
    )

    state = orchestrator.run()

    assert state.current_step == "complete"
    assert state.requires_approval is None
    assert "dataset_create_or_version" in calls
    assert "kernel_push_once" in calls
    assert not (tmp_path / "approvals").exists()


def test_dry_run_stops_before_first_live_action(tmp_path: Path):
    calls: list[str] = []
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=_handlers(calls),
        dry_run=True,
    )

    state = orchestrator.run()

    assert state.current_step == "dataset_create_or_version"
    assert state.blocked_reason == "dry-run: live action not executed"
    assert "dataset_create_or_version" not in calls


def test_changed_dataset_fingerprint_resets_to_dataset_live_action(tmp_path: Path):
    calls: list[str] = []
    handlers = _handlers(calls)
    handlers["refresh_dataset_fingerprint"] = lambda _state: {
        "dataset_fingerprint": "dataset-fp-new"
    }
    orchestrator = Phase6EKaggleOrchestrator(
        root=tmp_path,
        handlers=handlers,
        dry_run=False,
    )
    orchestrator.state_store.save(
        AutomationState(
            current_step="kernel_package_generate",
            completed_steps=[
                "preflight",
                "auth_check_or_request_login",
                "repo_and_security_scan",
                "dataset_dry_run",
                "dataset_prepare",
                "dataset_validate_package",
                "dataset_fingerprint",
                "dataset_create_or_version",
            ],
            dataset_fingerprint="dataset-fp-old",
        )
    )

    result = orchestrator.run()

    assert result.dataset_fingerprint == "dataset-fp-new"
    assert "dataset_create_or_version" in calls
```

- [ ] **Step 2: Run orchestrator tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_kaggle_automation_orchestrator.py -v
```

Expected: FAIL because approval steps still interrupt the state machine.

- [ ] **Step 3: Remove approval state and transitions**

Change `AutomationState` to:

```python
@dataclass
class AutomationState:
    current_step: str = "preflight"
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str | None = None
    blocked_reason: str | None = None
    last_error_summary: str | None = None
    requires_approval: str | None = None
    attempts: dict[str, int] = field(default_factory=dict)
    dataset_fingerprint: str | None = None
    kernel_fingerprint: str | None = None
    kernel_status: str | None = None
    artifact_paths: dict[str, str] = field(default_factory=dict)
    pushed_kernel_fingerprints: list[str] = field(default_factory=list)
    dataset_uploaded_fingerprint: str | None = None
    dataset_uploaded_inventory_sha256: str | None = None
    execution_mode: str | None = None
```

Keep `requires_approval` only for backward-compatible state loading during one migration release;
always write it as `None`. Rename `gpu_push_fingerprints` to `pushed_kernel_fingerprints` and add
a migration in `StateStore.load()`:

```python
payload = json.loads(self.path.read_text(encoding="utf-8-sig"))
payload["pushed_kernel_fingerprints"] = payload.pop(
    "gpu_push_fingerprints", payload.get("pushed_kernel_fingerprints", [])
)
payload["requires_approval"] = None
return AutomationState(**payload)
```

Set the Phase 6E state machine to:

```python
PHASE6E_AUTOMATION_STEPS = (
    "preflight",
    "auth_check_or_request_login",
    "repo_and_security_scan",
    "dataset_dry_run",
    "dataset_prepare",
    "dataset_validate_package",
    "dataset_fingerprint",
    "dataset_create_or_version",
    "kernel_package_generate",
    "kernel_validate_package",
    "kernel_push_once",
    "kernel_poll",
    "artifact_download",
    "artifact_validate",
    "artifact_ingest",
    "complete",
)
PHASE6E_LIVE_ACTION_FINGERPRINTS = {
    "dataset_create_or_version": "dataset_fingerprint",
    "kernel_push_once": "kernel_fingerprint",
}
```

Delete `APPROVAL_STEPS`, `LIVE_ACTION_APPROVALS`, `approve_step()`, `_handle_approval()`, and all
`ApprovalStore` use.

- [ ] **Step 4: Make the orchestrator accept a workflow-specific step graph**

Replace the hard-coded class with:

```python
class KaggleOrchestrator:
    def __init__(
        self,
        *,
        root: Path,
        handlers: dict[str, Callable[[AutomationState], dict[str, Any]]],
        steps: tuple[str, ...],
        live_action_fingerprints: dict[str, str],
        dry_run: bool,
        security_guard: SecurityGuard | None = None,
    ) -> None:
        if not steps or steps[-1] != "complete":
            raise ValueError("Kaggle workflow steps must end with complete.")
        self.root = root
        self.handlers = handlers
        self.steps = steps
        self.live_action_fingerprints = live_action_fingerprints
        self.dry_run = dry_run
        self.security_guard = security_guard or SecurityGuard()
        self.state_store = StateStore(root / "state.json")

    def _next_step(self, step: str) -> str:
        index = self.steps.index(step)
        return self.steps[min(index + 1, len(self.steps) - 1)]
```

Change all internal `AUTOMATION_STEPS` references to `self.steps` and all live-action-map
references to `self.live_action_fingerprints`.

Keep the current public API through:

```python
class Phase6EKaggleOrchestrator(KaggleOrchestrator):
    def __init__(
        self,
        *,
        root: Path,
        handlers: dict[str, Callable[[AutomationState], dict[str, Any]]],
        dry_run: bool,
        security_guard: SecurityGuard | None = None,
    ) -> None:
        super().__init__(
            root=root,
            handlers=handlers,
            steps=PHASE6E_AUTOMATION_STEPS,
            live_action_fingerprints=PHASE6E_LIVE_ACTION_FINGERPRINTS,
            dry_run=dry_run,
            security_guard=security_guard,
        )
```

- [ ] **Step 5: Preserve dry-run and one-push idempotency**

Replace `_before_live_action` with:

```python
def _before_live_action(self, state: AutomationState, step: str) -> None:
    if self.dry_run:
        state.current_step = step
        state.blocked_reason = "dry-run: live action not executed"
        self.state_store.save(state)
        raise AutomationBlockedError(state.blocked_reason)
    fingerprint_field = self.live_action_fingerprints[step]
    fingerprint = self._fingerprint_for_step(state, fingerprint_field)
    if step == "kernel_push_once" and fingerprint in state.pushed_kernel_fingerprints:
        if state.kernel_status in {"running", "success"}:
            self._complete_step(state, step)
            self.state_store.save(state)
            return
        raise AutomationBlockedError(
            f"Kernel fingerprint already pushed and requires a changed package: {fingerprint}"
        )
    if step == "kernel_push_once":
        state.pushed_kernel_fingerprints.append(fingerprint)
        self.state_store.save(state)
```

Fingerprint changes reset to `dataset_create_or_version` or `kernel_push_once`, not to an approval
step.

- [ ] **Step 6: Simplify the Phase 6E CLI**

Remove `APPROVAL_STEPS`, `--approve-step`, and all approval output. Use:

```python
mode.add_argument(
    "--dry-run",
    action="store_true",
    help="Run all validation and packaging steps, then stop before the first Kaggle mutation.",
)
mode.add_argument(
    "--live",
    action="store_true",
    help="Run the standing-authorized Kaggle workflow through artifact ingestion.",
)
```

Print:

```python
print(f"Execution mode: {state.execution_mode}")
print(f"Current step: {state.current_step}")
print(f"Kernel status: {state.kernel_status}")
print(f"Blocked reason: {state.blocked_reason}")
```

- [ ] **Step 7: Update Phase 6E package validation for configurable visibility**

Add `dataset_visibility` and `kernel_visibility` to `AutomationConfig`, defaulting to `"private"`
for historical Phase 6E compatibility. Change metadata and validators to compare against the
configured visibility:

```python
"is_private": self.config.kernel_visibility == "private",
```

For a new public dataset create, append `--public`:

```python
if self.config.dataset_visibility == "public":
    command.append("--public")
```

Do not add `--delete-old-versions`.

- [ ] **Step 8: Run focused tests**

Run:

```powershell
python -m pytest tests/test_kaggle_automation_orchestrator.py tests/test_kaggle_automation_validation.py tests/test_phase6e_kaggle_docs.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit the approval-free orchestrator**

```powershell
git add src/glitch_detection/kaggle_automation.py scripts/run_phase6e_kaggle_automation.py tests/test_kaggle_automation_orchestrator.py tests/test_kaggle_automation_validation.py tests/test_phase6e_kaggle_docs.py
git commit -m "refactor(kaggle): remove per-action approval stops"
```

---

### Task 4: Replace LeWM Approval Requests With Audit Manifests

**Files:**
- Modify: `src/glitch_detection/lewm_kaggle.py`
- Delete: `scripts/request_lewm_kaggle_approvals.py`
- Modify: `tests/test_lewm_kaggle.py`

- [ ] **Step 1: Write the failing audit-manifest tests**

Replace `request_package_approvals` imports and tests with:

```python
from glitch_detection.lewm_kaggle import build_package_audit


def test_kaggle_package_builds_dataset_and_kernel_audit_without_approval_files(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)

    audit = build_package_audit(package, tmp_path / "audit.json")

    assert audit["authorization"] == "standing"
    assert audit["dataset_inventory_sha256"]
    assert audit["kernel_fingerprint"]
    assert audit["locked_test_materialized"] is False
    assert audit["locked_test_scored"] is False
    assert (tmp_path / "audit.json").is_file()
    assert not list(tmp_path.rglob("*.approved.json"))
    assert not list(tmp_path.rglob("*.request.json"))


def test_kernel_push_preflight_has_no_approval_status(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "train.lance").mkdir()
    (source / "validation.lance").mkdir()
    package = tmp_path / "package"
    prepare_lewm_kaggle_package(source, package, _config(), dry_run=False)

    result = validate_kernel_push_preflight(package)

    assert result["authorization"] == "standing"
    assert "approval_status" not in result
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_lewm_kaggle.py -v
```

Expected: FAIL because `build_package_audit` does not exist and approval APIs remain.

- [ ] **Step 3: Implement immutable audit generation**

Remove the `ApprovalStore` import and delete `request_package_approvals`. Implement:

```python
def validate_kernel_push_preflight(package_root: Path) -> dict[str, Any]:
    kernel_payload = _kernel_fingerprint_payload(package_root)
    return {
        **kernel_payload,
        "kernel_fingerprint": _sha256_json(kernel_payload),
        "authorization": "standing",
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_package_audit(package_root: Path, output_path: Path) -> dict[str, Any]:
    validation = validate_lewm_kaggle_package(package_root)
    preflight = validate_kernel_push_preflight(package_root)
    payload = {
        **validation,
        **preflight,
        "dataset_inventory_sha256": validation["dataset_inventory_sha256"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "live_actions_performed": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
```

Add `datetime` and `timezone` imports. Audit files remain under ignored `outputs/`.

- [ ] **Step 4: Delete the obsolete approval CLI and references**

Delete `scripts/request_lewm_kaggle_approvals.py`. Remove it from docs, context routing, and help
examples. Historical reports may retain statements about approvals actually used by v3/v5/v6;
do not rewrite history.

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest tests/test_lewm_kaggle.py tests/test_imports.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit LeWM audit migration**

```powershell
git add src/glitch_detection/lewm_kaggle.py tests/test_lewm_kaggle.py
git add -u scripts/request_lewm_kaggle_approvals.py
git commit -m "refactor(lewm): replace Kaggle approvals with audits"
```

---

### Task 5: Build A Single-File Gate 6 Kernel

**Files:**
- Modify: `src/glitch_detection/lewm_gate6.py`
- Modify: `scripts/prepare_lewm_gate6_package.py`
- Modify: `tests/test_lewm_gate6.py`

- [ ] **Step 1: Complete the existing failing source-archive regressions**

Keep the current `build_source_archive` tests and add:

```python
import os
import subprocess
import sys


def test_gate6_embedded_bootstrap_runs_from_kaggle_like_cwd(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    archive = build_source_archive(repo_root / "src")
    kernel = render_gate6_kernel(
        _config(),
        base64.b64encode(archive).decode("ascii"),
    )
    script = tmp_path / "kaggle_src" / "script.py"
    script.parent.mkdir()
    script.write_text(kernel, encoding="utf-8")
    work = tmp_path / "kaggle_working"
    work.mkdir()
    environment = dict(os.environ)
    environment["GATE6_BOOTSTRAP_ONLY"] = "1"
    environment["GATE6_CODE_ROOT"] = str(tmp_path / "gate6_code")

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=work,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "GATE6_BOOTSTRAP_OK" in completed.stdout


def test_gate6_generated_kernel_has_no_local_windows_path_or_auxiliary_source_file():
    kernel = render_gate6_kernel(_config(), "c291cmNl")

    assert not re.search(r"[A-Za-z]:\\\\", kernel)
    assert "glitch_detection_src.zip" not in kernel
    assert "SOURCE_ARCHIVE_B64" in kernel
```

Add imports for `base64` and `re`.

- [ ] **Step 2: Run Gate 6 tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_lewm_gate6.py -v
```

Expected: collection FAIL because `build_source_archive` is not implemented, then behavior tests
FAIL until source embedding is added.

- [ ] **Step 3: Implement deterministic archive construction**

Add imports:

```python
import base64
import io
import zipfile
```

Implement:

```python
def build_source_archive(source_root: Path) -> bytes:
    package_root = source_root / "glitch_detection"
    if not (package_root / "__init__.py").is_file():
        raise FileNotFoundError(f"Missing glitch_detection package: {package_root}")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(package_root.rglob("*.py")):
            relative = path.relative_to(source_root)
            if "__pycache__" in relative.parts:
                continue
            info = zipfile.ZipInfo(relative.as_posix())
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
    return buffer.getvalue()
```

This produces stable bytes and excludes bytecode/caches.

- [ ] **Step 4: Render the embedded bootstrap**

Change the signature to:

```python
def render_gate6_kernel(config: Gate6KaggleConfig, source_archive_b64: str) -> str:
```

Use this exact bootstrap before dependency installation:

```python
SOURCE_ARCHIVE_B64 = {source_archive_b64!r}
CODE_ROOT = Path(os.environ.get("GATE6_CODE_ROOT", "/tmp/gate6_code"))
SOURCE_ZIP = CODE_ROOT.parent / "gate6_source.zip"
CODE_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ZIP.write_bytes(base64.b64decode(SOURCE_ARCHIVE_B64, validate=True))
if not zipfile.is_zipfile(SOURCE_ZIP):
    raise RuntimeError("Embedded Gate 6 source archive is invalid.")
with zipfile.ZipFile(SOURCE_ZIP) as bundle:
    names = set(bundle.namelist())
    if "glitch_detection/__init__.py" not in names:
        raise RuntimeError("Embedded Gate 6 source archive lacks the package root.")
    bundle.extractall(CODE_ROOT)
sys.path.insert(0, str(CODE_ROOT))

from glitch_detection.lewm_training import LeWMTrainConfig, score_lance_probe, train_lewm

if os.environ.get("GATE6_BOOTSTRAP_ONLY") == "1":
    print("GATE6_BOOTSTRAP_OK")
    raise SystemExit(0)
```

The generated script imports `base64`, `os`, and `zipfile`. Import `torch` and install optional
dependencies only after the bootstrap-only exit.

- [ ] **Step 5: Embed source during package preparation**

Replace `shutil.make_archive(...glitch_detection_src...)` with:

```python
repo_root = Path(__file__).resolve().parents[2]
source_archive = build_source_archive(repo_root / "src")
source_archive_b64 = base64.b64encode(source_archive).decode("ascii")
kernel_script.write_text(
    render_gate6_kernel(config, source_archive_b64),
    encoding="utf-8",
)
```

Write no auxiliary source ZIP to the kernel directory.

- [ ] **Step 6: Add public visibility and license fields to Gate 6 config**

Extend `Gate6KaggleConfig`:

```python
dataset_visibility: str = "public"
kernel_visibility: str = "public"
dataset_license: str = "MIT"
redistribution_allowed: bool = True
```

Validate visibility against `{"private", "public"}` and reject public datasets when
`redistribution_allowed` is false. Write:

```python
"licenses": [{"name": config.dataset_license}],
```

and:

```python
"is_private": config.kernel_visibility == "private",
```

Add CLI choices `--dataset-visibility`, `--kernel-visibility`, `--dataset-license`, and
`--redistribution-allowed`; set the Gate 6 defaults shown above.

- [ ] **Step 7: Add strict Gate 6 package validation**

Add:

```python
def validate_gate6_kaggle_package(package_root: Path) -> dict[str, Any]:
    dataset_root = package_root / "dataset"
    kernel_root = package_root / "kernel"
    dataset_metadata = _load_json(dataset_root / "dataset-metadata.json")
    kernel_metadata = _load_json(kernel_root / "kernel-metadata.json")
    code_file = kernel_root / str(kernel_metadata.get("code_file", ""))
    if not code_file.is_file():
        raise FileNotFoundError(f"Missing Gate 6 kernel code file: {code_file}")
    extra_kernel_files = sorted(
        path.name
        for path in kernel_root.iterdir()
        if path.is_file()
        and path.name not in {"kernel-metadata.json", code_file.name}
    )
    if extra_kernel_files:
        raise ValueError(
            f"Gate 6 kernel package contains auxiliary files: {extra_kernel_files}"
        )
    kernel_text = code_file.read_text(encoding="utf-8")
    if "SOURCE_ARCHIVE_B64" not in kernel_text:
        raise ValueError("Gate 6 kernel does not embed its source archive.")
    if re.search(r"[A-Za-z]:\\\\", kernel_text):
        raise ValueError("Gate 6 kernel contains a Windows absolute path.")
    if kernel_metadata.get("dataset_sources") != [dataset_metadata.get("id")]:
        raise ValueError("Gate 6 kernel dataset_sources do not match dataset metadata.")
    SecurityGuard().scan_package(dataset_root, "dataset")
    SecurityGuard().scan_package(kernel_root, "kernel")
    return {
        "dataset_slug": dataset_metadata["id"],
        "kernel_slug": kernel_metadata["id"],
        "dataset_inventory_sha256": FingerprintBuilder.inventory_sha256(dataset_root),
        "kernel_inventory_sha256": FingerprintBuilder.inventory_sha256(kernel_root),
        "kernel_code_sha256": FingerprintBuilder.sha256_file(code_file),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
```

Add `re` and `SecurityGuard`/`FingerprintBuilder` imports if not already present. Add tests that
an auxiliary ZIP and a Windows path are rejected.

- [ ] **Step 8: Run focused tests**

Run:

```powershell
python -m pytest tests/test_lewm_gate6.py tests/test_lewm_training.py -v
python -m ruff check src/glitch_detection/lewm_gate6.py scripts/prepare_lewm_gate6_package.py tests/test_lewm_gate6.py
python -m ruff format --check src/glitch_detection/lewm_gate6.py scripts/prepare_lewm_gate6_package.py tests/test_lewm_gate6.py
```

Expected: PASS.

- [ ] **Step 9: Commit single-file packaging**

```powershell
git add src/glitch_detection/lewm_gate6.py scripts/prepare_lewm_gate6_package.py tests/test_lewm_gate6.py
git commit -m "fix(gate6): embed source in single-file Kaggle kernel"
```

---

### Task 6: Add Gate 6 Automatic Remote Lifecycle

**Files:**
- Create: `src/glitch_detection/lewm_gate6_automation.py`
- Create: `scripts/run_lewm_gate6_automation.py`
- Create: `tests/test_lewm_gate6_automation.py`
- Modify: `src/glitch_detection/__init__.py` only if an export is required

- [ ] **Step 1: Write fake-runner lifecycle tests**

Create:

```python
import json
from pathlib import Path

from glitch_detection.lewm_gate6_automation import (
    GATE6_AUTOMATION_STEPS,
    GATE6_LIVE_ACTION_FINGERPRINTS,
    Gate6AutomationConfig,
    Gate6AutomationHandlers,
)
from glitch_detection.kaggle_automation import (
    AutomationBlockedError,
    AutomationState,
    CommandResult,
    KaggleOrchestrator,
)
import pytest


class FakeRunner:
    def __init__(self, responses: list[CommandResult]):
        self.responses = list(responses)
        self.commands: list[list[str]] = []

    def run(self, _step: str, command: list[str], _log_path: Path) -> CommandResult:
        self.commands.append(command)
        return self.responses.pop(0)


def _config(tmp_path: Path) -> Gate6AutomationConfig:
    return Gate6AutomationConfig(
        repo_root=Path(__file__).resolve().parents[1],
        source_root=tmp_path / "datasets",
        run_root=tmp_path / "run",
        dataset_slug="huynhdieuthanh/lewm-tempglitch-gate6-public-v7",
        kernel_slug="huynhdieuthanh/lewm-gate6-pilot-v7",
        dataset_visibility="public",
        kernel_visibility="public",
        live=True,
    )


def test_public_dataset_create_uses_public_flag(tmp_path: Path):
    runner = FakeRunner(
        [
            CommandResult(
                returncode=0,
                stdout="not found",
                stderr="",
                attempts=1,
            ),
            CommandResult(returncode=0, stdout="created", stderr="", attempts=1),
        ]
    )
    handlers = Gate6AutomationHandlers(_config(tmp_path), command_runner=runner)
    state = AutomationState(dataset_fingerprint="dataset-fp")

    updates = handlers.dataset_create_or_version(state)

    create = runner.commands[-1]
    assert "datasets" in create
    assert "create" in create
    assert "--public" in create
    assert updates["dataset_uploaded_fingerprint"] == "dataset-fp"


def test_kernel_push_uses_python_module_invocation_and_public_metadata(tmp_path: Path):
    runner = FakeRunner(
        [CommandResult(returncode=0, stdout="pushed", stderr="", attempts=1)]
    )
    config = _config(tmp_path)
    kernel_root = config.run_root / "package" / "kernel"
    kernel_root.mkdir(parents=True)
    (kernel_root / "kernel-metadata.json").write_text(
        json.dumps({"is_private": False}),
        encoding="utf-8",
    )
    handlers = Gate6AutomationHandlers(config, command_runner=runner)

    updates = handlers.kernel_push_once(AutomationState(kernel_fingerprint="kernel-fp"))

    assert runner.commands[0][:3] == [
        str(config.python_executable),
        "-c",
        "from kaggle.cli import main; main()",
    ]
    assert updates["kernel_status"] == "running"


def test_error_status_downloads_logs_and_blocks_without_resubmit(tmp_path: Path):
    runner = FakeRunner(
        [
            CommandResult(
                returncode=0,
                stdout='status "KernelWorkerStatus.ERROR"',
                stderr="",
                attempts=1,
            ),
            CommandResult(returncode=0, stdout="downloaded", stderr="", attempts=1),
        ]
    )
    handlers = Gate6AutomationHandlers(_config(tmp_path), command_runner=runner)

    with pytest.raises(AutomationBlockedError, match="runtime failed"):
        handlers.kernel_poll(AutomationState(kernel_fingerprint="kernel-fp"))

    assert sum("push" in command for command in runner.commands) == 0
    assert any("output" in command for command in runner.commands)


def test_ambiguous_push_error_checks_remote_before_failing(tmp_path: Path):
    class AmbiguousRunner(FakeRunner):
        def run(self, step: str, command: list[str], log_path: Path) -> CommandResult:
            self.commands.append(command)
            if step == "kernel_push_once":
                raise AutomationCommandError(
                    "Expecting value: line 1 column 1 (char 0)"
                )
            return CommandResult(
                returncode=0,
                stdout='status "KernelWorkerStatus.RUNNING"',
                stderr="",
                attempts=1,
            )

    runner = AmbiguousRunner([])
    handlers = Gate6AutomationHandlers(_config(tmp_path), command_runner=runner)

    updates = handlers.kernel_push_once(
        AutomationState(kernel_fingerprint="kernel-fp")
    )

    assert updates["kernel_status"] == "running"
    assert any("status" in command for command in runner.commands)
```

- Add `AutomationCommandError` to the imports used by this test module.

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_lewm_gate6_automation.py -v
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement Gate 6 automation configuration**

Create:

```python
@dataclass(frozen=True)
class Gate6AutomationConfig:
    repo_root: Path
    source_root: Path
    run_root: Path
    dataset_slug: str
    kernel_slug: str
    dataset_visibility: str = "public"
    kernel_visibility: str = "public"
    dataset_license: str = "MIT"
    redistribution_allowed: bool = True
    accelerator: str = "NvidiaTeslaT4"
    poll_interval_seconds: int = 60
    poll_timeout_seconds: int = 6 * 60 * 60
    live: bool = False
    python_executable: Path = Path(sys.executable)

    @property
    def package_root(self) -> Path:
        return self.run_root / "package"

    @property
    def downloaded_root(self) -> Path:
        return self.run_root / "downloaded"
```

The module imports and reuses `AutomationBlockedError`, `AutomationState`, `CommandRunner`,
`FingerprintBuilder`, `KaggleAction`, `KaggleExecutionPolicy`, `KaggleOrchestrator`,
`PublicReleaseSpec`, and `SecurityGuard`.

Define the Gate 6 workflow:

```python
GATE6_AUTOMATION_STEPS = (
    "preflight",
    "package_prepare",
    "package_validate",
    "dataset_fingerprint",
    "dataset_create_or_version",
    "dataset_ready",
    "kernel_package_generate",
    "kernel_validate_package",
    "kernel_push_once",
    "kernel_poll",
    "artifact_download",
    "artifact_validate",
    "complete",
)
GATE6_LIVE_ACTION_FINGERPRINTS = {
    "dataset_create_or_version": "dataset_fingerprint",
    "kernel_push_once": "kernel_fingerprint",
}
```

- [ ] **Step 4: Implement package preparation, policy checks, and audit**

`Gate6AutomationHandlers.package_prepare()` calls `prepare_gate6_kaggle_package` with the three
fixed dataset names:

```python
tempglitch_train_zero_action.lance
tempglitch_validation_zero_action.lance
tempglitch_nonlocked_buggy_encoding.lance
```

An automation dry-run still materializes the ignored package; `dry_run` controls remote mutation,
not package creation. Implement resumability as:

```python
if self.config.package_root.exists():
    validate_gate6_kaggle_package(self.config.package_root)
    return {}
prepare_gate6_kaggle_package(
    self.config.source_root,
    self.config.package_root,
    gate6_config,
    dry_run=False,
)
return {}
```

Add `validate_gate6_kaggle_package()` to `lewm_gate6.py`; it validates metadata, the single code
file, public/private expectation, exact dataset source, source embedding, package security, and
returns dataset/kernel inventory hashes.

`package_validate()` performs:

```python
dataset_release = self.security_guard.scan_public_release(
    self.config.package_root / "dataset",
    package_kind="dataset",
    spec=PublicReleaseSpec(
        visibility=self.config.dataset_visibility,
        license_name=self.config.dataset_license,
        redistribution_allowed=self.config.redistribution_allowed,
    ),
)
kernel_release = self.security_guard.scan_public_release(
    self.config.package_root / "kernel",
    package_kind="kernel",
    spec=PublicReleaseSpec(
        visibility=self.config.kernel_visibility,
        license_name="repository-source",
        redistribution_allowed=True,
    ),
)
```

Write `run_root/audit/preflight.json` containing both inventories, git SHA, slugs, visibility,
false locked-test flags, and `"authorization": "standing"`.

- [ ] **Step 5: Implement dataset publication**

Use the Python module invocation:

```python
def _kaggle(self, *args: str) -> list[str]:
    return [
        str(self.config.python_executable),
        "-c",
        "from kaggle.cli import main; main()",
        *args,
    ]
```

Authorize before mutation:

```python
self.policy.authorize(
    KaggleAction(
        action="dataset_create_or_version",
        fingerprint=state.dataset_fingerprint or "",
        visibility=self.config.dataset_visibility,
        locked_test_materialized=False,
        locked_test_scored=False,
        redistribution_allowed=self.config.redistribution_allowed,
    )
)
```

For a missing dataset, run:

```python
command = self._kaggle(
    "datasets",
    "create",
    "-p",
    str(self.config.package_root / "dataset"),
    "-r",
    "zip",
)
if self.config.dataset_visibility == "public":
    command.append("--public")
```

For an existing dataset, run `datasets version` without `--delete-old-versions`.

- [ ] **Step 6: Implement kernel push, poll, error capture, and strict validation**

Before push, authorize with `action="kernel_push"`. Implement `kernel_push_once()` and push
exactly once with:

```python
self._kaggle(
    "kernels",
    "push",
    "-p",
    str(self.config.package_root / "kernel"),
    "--accelerator",
    self.config.accelerator,
)
```

Catch `AutomationCommandError` around the push. For any ambiguous CLI failure, immediately run
`kernels status <slug>`. If the slug is `RUNNING`, `COMPLETE`, or `ERROR`, treat the remote
version as established and return that status without another push. Re-raise only when exact-slug
status confirms no remote version. This check must not consume another retry or call `push`
again.

Poll `kernels status`. On `ERROR`, call:

```python
self._kaggle(
    "kernels",
    "output",
    self.config.kernel_slug,
    "-p",
    str(self.config.downloaded_root),
    "-o",
)
```

then raise:

```python
AutomationBlockedError(
    "Gate 6 runtime failed; downloaded evidence requires a changed package fingerprint."
)
```

On `COMPLETE`, download output and call:

```python
validate_gate6_artifacts(self.config.downloaded_root)
```

If artifacts are nested one level below the download root, locate the unique directory containing
`run_config.json`; reject zero or multiple matches.

- [ ] **Step 7: Implement the thin CLI**

Required CLI defaults:

```python
--source-root outputs/gate6/datasets
--run-root outputs/gate6/automation/lewm_gate6_pilot_v7
--dataset-slug huynhdieuthanh/lewm-tempglitch-gate6-public-v7
--kernel-slug huynhdieuthanh/lewm-gate6-pilot-v7
--dataset-visibility public
--kernel-visibility public
--dataset-license MIT
```

Support mutually exclusive `--dry-run` and `--live`. Neither mode asks for approval. `--live`
runs through strict validation or exits nonzero with a recorded blocker.

Construct the orchestrator with:

```python
orchestrator = KaggleOrchestrator(
    root=config.run_root,
    handlers=handlers.as_mapping(),
    steps=GATE6_AUTOMATION_STEPS,
    live_action_fingerprints=GATE6_LIVE_ACTION_FINGERPRINTS,
    dry_run=not args.live,
)
state = orchestrator.run()
```

- [ ] **Step 8: Run focused tests**

Run:

```powershell
python -m pytest tests/test_lewm_gate6_automation.py tests/test_lewm_gate6.py tests/test_kaggle_automation_orchestrator.py -v
python -m ruff check src/glitch_detection/lewm_gate6_automation.py scripts/run_lewm_gate6_automation.py tests/test_lewm_gate6_automation.py
python -m ruff format --check src/glitch_detection/lewm_gate6_automation.py scripts/run_lewm_gate6_automation.py tests/test_lewm_gate6_automation.py
```

Expected: PASS.

- [ ] **Step 9: Commit Gate 6 automation**

```powershell
git add src/glitch_detection/lewm_gate6_automation.py scripts/run_lewm_gate6_automation.py tests/test_lewm_gate6_automation.py
git commit -m "feat(gate6): automate Kaggle lifecycle and validation"
```

---

### Task 7: Update Gate 6 Protocol And Pre-Live Evidence

**Files:**
- Modify: `configs/lewm_gate6_pilot.yaml`
- Modify: `docs/research/45_gate6_lewm_normal_training_plan.md`
- Modify: `docs/research/46_gate6_lewm_training_pilot_results.md`
- Modify: `docs/research/62_artifact_manifest.md`
- Modify: `docs/research/64_kaggle_kernel_write_path_repair.md`
- Modify: `docs/context/LAST_HANDOFF.md`
- Modify: `tests/test_kaggle_governance.py`

- [ ] **Step 1: Freeze v7 execution metadata**

Add to `configs/lewm_gate6_pilot.yaml`:

```yaml
kaggle:
  dataset_slug: huynhdieuthanh/lewm-tempglitch-gate6-public-v7
  kernel_slug: huynhdieuthanh/lewm-gate6-pilot-v7
  dataset_visibility: public
  kernel_visibility: public
  dataset_license: MIT
  redistribution_allowed: true
  standing_authorization: true
  max_transient_attempts: 3
  delete_remote_resources: false
```

Keep `locked_test_enabled: false`.

- [ ] **Step 2: Record verified v6 failure without rewriting history**

Update report 46 with:

```markdown
The later Canary A completed, proving the Python-module Kaggle write path worked. Gate 6 v6 was
accepted as remote version 1 and failed at runtime before dependency installation:
`shutil.ReadError: /kaggle/src/glitch_detection_src.zip is not a zip file`.
The local ZIP was valid, but Kaggle did not place that auxiliary file beside
`/kaggle/src/script.py`. This narrows v6 to a packaging-contract failure, not training evidence.
```

Report 64 must distinguish the successful canary from v6's later execution failure.

- [ ] **Step 3: Record the planned v7 artifact contract**

Update the artifact manifest:

```markdown
| Gate 6 v6 kernel | ignored run log | accepted, runtime packaging failure |
| Gate 6 v7 package/audit | ignored `outputs/gate6/automation/` | pre-live validation pending |
| Gate 6 v7 remote artifacts | none | not run |
```

Do not mark Gate 6 passed and do not add a performance claim.

- [ ] **Step 4: Run the complete local pre-live gate**

Run:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
pre-commit run --all-files
git diff --check
```

Expected: every command PASS. Do not continue to Task 8 if any command fails.

- [ ] **Step 5: Run the Gate 6 automation dry-run**

Run:

```powershell
python scripts/run_lewm_gate6_automation.py --dry-run
```

Expected:

- package generated under ignored `outputs/gate6/automation/lewm_gate6_pilot_v7/`;
- kernel directory contains only `lewm_gate6_kernel.py` and `kernel-metadata.json`;
- bootstrap-only subprocess passes;
- public-release scans pass;
- audit contains standing authorization, MIT license, public visibility, fingerprints, and false
  locked-test flags;
- no Kaggle dataset or kernel mutation occurs.

- [ ] **Step 6: Inspect the exact pre-live inventory**

Run:

```powershell
Get-ChildItem outputs/gate6/automation/lewm_gate6_pilot_v7/package/kernel -File |
  Select-Object Name,Length
Get-Content outputs/gate6/automation/lewm_gate6_pilot_v7/audit/preflight.json
git status --short
```

Expected kernel files:

```text
kernel-metadata.json
lewm_gate6_kernel.py
```

The audit must not contain secret values or Windows source paths. Git status must not show data,
outputs, checkpoints, credentials, or caches.

- [ ] **Step 7: Commit protocol and pre-live evidence**

```powershell
git add configs/lewm_gate6_pilot.yaml docs/research/45_gate6_lewm_normal_training_plan.md docs/research/46_gate6_lewm_training_pilot_results.md docs/research/62_artifact_manifest.md docs/research/64_kaggle_kernel_write_path_repair.md docs/context
git commit -m "docs(gate6): freeze automatic v7 execution"
```

---

### Task 8: Execute One Automatic Public Gate 6 Run

**Files:**
- No tracked code changes before execution
- Generate ignored artifacts under `outputs/gate6/automation/lewm_gate6_pilot_v7/`

- [ ] **Step 1: Capture the clean execution identity**

Run:

```powershell
git status --short
git rev-parse HEAD
git branch --show-current
```

Expected: no uncommitted implementation changes. Preserve unrelated user changes if they still
exist, but do not include them in the run fingerprint; if implementation files are dirty, stop
and resolve them before live execution.

- [ ] **Step 2: Run the standing-authorized workflow**

Run:

```powershell
python scripts/run_lewm_gate6_automation.py --live
```

The command must automatically:

1. re-run security, license, locked-test, bootstrap, and package validation;
2. create the public dataset
   `huynhdieuthanh/lewm-tempglitch-gate6-public-v7` with `--public`, or version it if the exact
   audited dataset already exists;
3. wait for dataset readiness;
4. push public kernel `huynhdieuthanh/lewm-gate6-pilot-v7` once through
   `python -c "from kaggle.cli import main; main()"`;
5. poll only that slug/version;
6. download logs/output;
7. run the strict Gate 6 validator.

No approval file or prompt is permitted.

- [ ] **Step 3: Handle the terminal result**

If the kernel reaches `ERROR`:

- verify logs were downloaded;
- verify no second push occurred for the same fingerprint;
- record the exact traceback and failing stage;
- leave Gate 6 blocked;
- stop this plan before claim updates;
- create a new repair spec only if the failure requires a materially different design.

If the kernel reaches `COMPLETE` but strict validation fails:

- preserve downloaded artifacts;
- record validator output;
- leave Gate 6 blocked;
- do not open Gate 7.

Only continue when the strict validator returns:

```json
{
  "status": "gate6_passed",
  "normal_only_training": true,
  "normal_only_validation": true,
  "locked_test_materialized": false,
  "locked_test_scored": false
}
```

- [ ] **Step 4: Independently re-run strict artifact validation**

Run:

```powershell
python scripts/validate_lewm_gate6_artifacts.py `
  --artifacts-root outputs/gate6/automation/lewm_gate6_pilot_v7/downloaded `
  --output outputs/gate6/automation/lewm_gate6_pilot_v7/audit/strict_validation.json
```

If the download has a unique nested artifact directory, pass that directory instead. Expected:
exit code 0 and `"status": "gate6_passed"`.

- [ ] **Step 5: Verify credential and artifact hygiene**

Run:

```powershell
git status --short
git ls-files | Select-String -Pattern 'outputs/|data/|\.lance|\.pt$|\.pth$|\.ckpt$|kaggle\.json|\.env'
```

Expected: no newly tracked generated artifact or credential.

---

### Task 9: Register Verified Gate 6 Evidence And Open Gate 7

**Condition:** Execute this task only if Task 8 strict validation passed.

**Files:**
- Modify: `docs/research/46_gate6_lewm_training_pilot_results.md`
- Modify: `docs/research/47_gate7_lewm_surprise_scoring_results.md`
- Modify: `docs/research/62_artifact_manifest.md`
- Modify: `docs/research/16_claim_registry.md`
- Modify: `PLAYBOOK.md`
- Modify: `AGENTS.md`
- Modify: `scripts/update_context_cache.py`
- Modify: `docs/context/LAST_HANDOFF.md`

- [ ] **Step 1: Add a narrow verified claim**

Append the next sequential claim ID to the registry:

```markdown
| C-055 | A public Gate 6 Kaggle run completed normal-only TempGlitch LeWM training on CUDA and passed strict local artifact validation, including finite losses and diagnostics, checkpoint reload, normal validation encoding, non-locked buggy validation encoding, and false locked-test flags. | reproducibility | [Gate 6 results](46_gate6_lewm_training_pilot_results.md), ignored downloaded artifacts and strict validation report | verified | Method / Reproducibility | Gameplay-training engineering evidence only; it does not establish glitch-detection performance, superiority, temporal localization, or a locked-test result. |
```

Use a different ID only if another claim was added first.

- [ ] **Step 2: Update Gate 6 results with exact evidence**

Record:

- git SHA and branch;
- dataset and kernel slugs/versions;
- public visibility;
- dataset/kernel fingerprints;
- config, dataset, checkpoint, and artifact hashes;
- device and completed epoch;
- finite loss and collapse summary;
- reload and encoding-proof outcomes;
- strict validator result;
- locked-test flags false;
- no detection metric or superiority claim.

Do not copy values from the plan. Read every value from the downloaded artifacts and audit files.

- [ ] **Step 3: Open Gate 7 without running it**

Change Gate 7 status from `infrastructure only / blocked on Gate 6` to `ready for validation
scoring`. Do not run Gate 7 in this plan.

- [ ] **Step 4: Regenerate context and run final verification**

Run:

```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
pre-commit run --all-files
git diff --check
```

Expected: all PASS.

- [ ] **Step 5: Commit evidence and gate transition**

```powershell
git add AGENTS.md PLAYBOOK.md scripts/update_context_cache.py docs/context docs/research/16_claim_registry.md docs/research/46_gate6_lewm_training_pilot_results.md docs/research/47_gate7_lewm_surprise_scoring_results.md docs/research/62_artifact_manifest.md
git commit -m "docs(gate6): record validated public training run"
```

- [ ] **Step 6: Final report**

Report:

- branch and final SHA;
- commits created by Tasks 1-9;
- tracked files changed;
- all verification commands and results;
- Gate 6 strict validation evidence;
- allowed and forbidden scientific claims;
- Kaggle dataset/kernel slugs and public visibility;
- locked test unmaterialized and unscored;
- artifact/credential hygiene;
- residual risks;
- next gate: Gate 7 validation scoring.

If Task 8 did not strict-pass, report Gate 6 as blocked and do not claim or imply completion.
