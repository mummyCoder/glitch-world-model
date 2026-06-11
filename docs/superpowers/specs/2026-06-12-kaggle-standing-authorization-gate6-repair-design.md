# Kaggle Standing Authorization And Gate 6 Repair Design

Status date: 2026-06-12
Status: approved design

## Objective

Replace per-action Kaggle approval artifacts with repository-wide standing authorization for
Codex-operated Kaggle workflows. The automation may create or version datasets, publish datasets
and kernels publicly, run GPU kernels, poll, download artifacts, validate results, and retry
within the policy defined here.

The locked test remains outside this authorization. Materializing or scoring locked-test data
still requires a separate, direct user command.

The first workflow migrated to this policy will repair and rerun Gate 6. The verified Gate 6 v6
failure is:

```text
shutil.ReadError: /kaggle/src/glitch_detection_src.zip is not a zip file
```

Kaggle accepted and started v6, but only the configured script and metadata were present in the
pulled kernel. The generator incorrectly assumed that an auxiliary ZIP would be available beside
`/kaggle/src/script.py`.

## Authorization Policy

Codex has standing authorization for all non-locked-test Kaggle operations in this repository:

- create and version Kaggle datasets;
- create, version, push, and rerun Kaggle kernels;
- allocate supported Kaggle accelerators;
- enable internet when the workflow requires dependency installation;
- publish datasets and kernels publicly after release validation;
- poll remote state, download logs and outputs, and ingest validated artifacts.

No request, approved, or consumed approval artifact is required. Fingerprints remain mandatory as
audit identifiers and idempotency keys, not permissions.

Standing authorization does not include:

- locked-test materialization or scoring;
- publishing credentials, private keys, tokens, `.env`, or `kaggle.json`;
- publishing data whose license or redistribution status is not recorded as allowed;
- deleting existing Kaggle resources;
- bypassing package, protocol, artifact, or claim validators;
- converting smoke, fixture, scaffold, or failed-run evidence into an experiment claim.

## Architecture

### Execution Policy

Replace approval-dependent transitions with a `KaggleExecutionPolicy`. The policy evaluates:

- action type;
- dataset and kernel visibility;
- package fingerprint;
- security and license scan results;
- locked-test flags;
- prior attempts for the same fingerprint;
- retry classification and retry budget.

The default repository policy authorizes non-locked-test Kaggle actions after all preflight
checks pass. A failed policy check stops before the external side effect and records the exact
reason.

### State Machine

The common live workflow is:

```text
preflight
  -> auth_check
  -> repo_and_security_scan
  -> package_prepare
  -> package_validate
  -> public_release_validate
  -> fingerprint
  -> dataset_create_or_version
  -> dataset_ready
  -> kernel_generate
  -> kernel_validate
  -> kernel_push
  -> kernel_poll
  -> log_and_artifact_download
  -> strict_artifact_validate
  -> artifact_ingest
  -> context_and_claim_update
  -> complete
```

Dry-run follows the same validation path but stops before dataset or kernel mutation.

### Fingerprints And Idempotency

Dataset and kernel fingerprints include the relevant source, configuration, metadata, inventory,
split, and script hashes. Audit records include:

- git branch and commit;
- dataset and kernel slugs;
- visibility;
- package inventories and SHA-256 values;
- command form;
- timestamps and remote version;
- retry and failure history;
- downloaded artifact hashes;
- validation outcome and allowed claim scope.

The same kernel fingerprint is pushed at most once. Transient command retries may repeat the same
HTTP operation up to three times only when no remote version was established. If a remote version
exists, automation polls that version instead of resubmitting it.

A runtime or package failure requires a source/package change and a new fingerprint before a new
kernel version is pushed.

## Public Publishing

Both datasets and kernels may use public visibility. Before publication, the automation must
produce a public-release inventory and verify:

- no credential or secret content;
- no `.env`, `.kaggle`, `kaggle.json`, private key, token, or credential-like file;
- no locked-test path, row, manifest, archive, flag, or derived score;
- no raw/private dataset content outside the declared release;
- recorded license and redistribution permission for every published dataset input;
- no unintended checkpoint, cache, output tree, or local absolute path;
- explicit dataset and kernel slugs owned by the authenticated account.

Failure of any check is non-retryable until package contents or metadata change.

## Gate 6 Packaging Repair

Gate 6 will use a single-file Kaggle kernel. The generated script embeds the source archive as
base64 text, writes it to a temporary ZIP, validates it with `zipfile`, extracts it under
`/tmp/gate6_code`, and adds the verified package root to `sys.path`.

The generated kernel must:

- contain no dependency on an auxiliary file beside `/kaggle/src/script.py`;
- embed only required `glitch_detection` Python source files;
- exclude `__pycache__`, bytecode, credentials, data, outputs, and checkpoints;
- fail with a precise message if the embedded archive or package root is invalid;
- use Kaggle input mounts and `/kaggle/working` or `/tmp` paths only;
- create output directories before writing artifacts;
- preserve normal-only training and validation contracts;
- keep the non-locked buggy clip limited to encoding proof;
- keep all locked-test flags false.

Embedding is preferred over a repository clone because it binds the executed source to the kernel
fingerprint and does not depend on GitHub availability or branch movement.

## Offline Preflight

Regression tests are written before the Gate 6 patch and cover:

- source archive content and cache exclusion;
- import of `glitch_detection.lewm_training` from a clean temporary extraction;
- bootstrap execution from a Kaggle-like working directory outside the repository;
- absence of auxiliary package-file assumptions;
- absence of Windows drive-letter and repository-local absolute paths;
- artifact directory initialization;
- rejection of locked-test content and true locked-test flags;
- public-release rejection of credentials, unlicensed data, and forbidden artifacts;
- no approval state or approval CLI requirement in the automatic path.

The preflight may use a bootstrap-only mode that stops before dependency installation, CUDA
training, or dataset loading. It must exercise the same archive decode, extraction, package-root,
and import logic used by the generated Kaggle script.

No live version is created until the focused regressions, full repository checks, package scan,
and fingerprint audit pass.

## Retry And Failure Handling

Transient API or network failures are retryable at most three times with exponential backoff:

- HTTP 429, 500, 502, 503, or 504;
- timeout;
- connection reset;
- temporary DNS or name-resolution failure.

Authentication, quota, accelerator availability, security, license, protocol, validator, and
runtime-code failures are not blindly retried.

After a remote runtime error, automation downloads the available log, records the failing stage,
and stops. A subsequent run is allowed only after a relevant patch changes the package
fingerprint. Automation never loops indefinitely and never disguises a retry as polling.

## Gate And Claim Rules

Gate 6 remains blocked until downloaded remote artifacts pass
`validate_lewm_gate6_artifacts`.

Gate 7 remains closed until Gate 6 passes. A Kaggle `COMPLETE` status, successful push, log, or
checkpoint alone does not pass Gate 6.

After strict validation:

- update Gate 6 research results and artifact manifest;
- synchronize the claim registry and context cache;
- register only the verified engineering/training claim supported by the artifacts;
- preserve limitations and failed v3, v5, and v6 history;
- do not claim LeWM glitch-detection performance before Gate 7.

The locked test remains closed in every execution and error branch.

## Implementation Boundaries

Primary modules:

- `src/glitch_detection/kaggle_automation.py`
- `src/glitch_detection/lewm_kaggle.py`
- `src/glitch_detection/lewm_gate6.py`

Primary CLIs and tests:

- `scripts/run_phase6e_kaggle_automation.py`
- `scripts/prepare_lewm_gate6_package.py`
- a Gate 6 automatic runner or a generalized Kaggle runner;
- `tests/test_kaggle_automation_foundation.py`
- `tests/test_kaggle_automation_orchestrator.py`
- `tests/test_kaggle_automation_validation.py`
- `tests/test_lewm_kaggle.py`
- `tests/test_lewm_gate6.py`

Governance and evidence documents must be synchronized, including `RULES.md`, `AGENTS.md`,
`PLAYBOOK.md`, the Kaggle workflow, Gate 6 reports, claim registry, and context cache.

Existing ignored outputs, consumed approvals, and failed-run evidence are preserved. Unrelated
user changes are not reverted.

## Acceptance Criteria

The implementation is complete when:

1. Repository governance consistently describes standing Kaggle authorization and the separate
   locked-test boundary.
2. The automatic path does not create, wait for, approve, or consume approval artifacts.
3. Fingerprint, idempotency, security, license, public-release, and retry controls remain active.
4. Gate 6 is a single-file kernel with clean-tempdir and Kaggle-like-cwd regression coverage.
5. All required repository checks pass before live execution.
6. A new Gate 6 fingerprint and slug are generated and published through the automatic path.
7. The remote kernel is pushed once per fingerprint, then polled and downloaded.
8. Downloaded artifacts pass the strict Gate 6 validator.
9. No credential, locked-test material, data, output, checkpoint, or cache is committed.
10. Gate and claim documents reflect only the evidence actually obtained.

If the remote run fails after the repaired package is submitted, the implementation work remains
valid but Gate 6 stays blocked. The failure log, fingerprint, and next justified patch must be
recorded before another remote version is created.
