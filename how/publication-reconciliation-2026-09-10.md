# Publication reconciliation — 10 September 2026

Owner instruction: “please push all items to github and reconcile it”.

## Preserved work and authority

Pending PM documents, requirement migration, Python implementation and tests were captured on `requirements-register`. Newer `origin/main` work through `5c58e6b` was merged without dropping the accepted product contract, programme manifest, reconciliation script or PM operating contract. This publication does not rewrite historical approval records.

The requirement register is `pm/03-requirements.md`; the older campaign views preserve provenance. Product intent/constraints remain in `what/context/product-contract.md`. `STATE.md` is the current status and next-action entry; PM status and mission-next pages now link to it. The programme describes phase sequencing, while the T-series file preserves proposed task details. Mapping those tasks to phase/task identities is an outstanding dispatch prerequisite, not completed reconciliation evidence.

The reusable PM system belongs in `DeveloperAlly/agent-governance`. Approval covers its Sliplane/Cloudflare/Herdr/Desktop Commander design. The Career OS product baseline, UI and runtime have their own acceptance requirements. The existing Python slices are preserved work, not proof that those gates passed.

## Validation performed

- `python3 tools/run_tests.py`: 16 files, 206 tests, 0 skipped, 0 failed files on this workspace.
- The runner executes every nested test script and fails if no files or no executed tests are found. This fixes the misleading top-level unittest discovery path, which returned success after running zero tests.
- Some checks inspect the ignored local evidence/job-ad store. This result is not a clean-checkout or CI portability claim; a checkout without that data may report skips. Real personal source data is not published to make those checks pass.
- Credential/private-key pattern review found no matching secrets in publishable text. Reviewed render fixtures identify a fictitious persona and use `example.invalid` addresses. This scan is not a comprehensive security review.
- Personal store data, local Claude configuration, worktrees and caches remain excluded.

## Remaining acceptance gaps

Hosted coordinator dispatch/recovery, protected authority, usage accounting, task/programme mapping, clean-checkout test fixtures, complete product outcomes and the integrated user journey remain unverified. Historical local coordinator setup instructions are explicitly superseded; publication does not start them.

The publication branch is a reviewable snapshot. Default-branch promotion and deployment are separate actions; no runtime is enabled by this commit.
