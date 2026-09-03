---
id: F027
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F003, F010]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, services/api/migrations/*_compliance_*.sql, testing/features/F027/**]
feature_flag: F027_FEATURE
flag_default: off
branch: f027-governance-compliance
started_at: null
finished_at: null
---

# F027 — Governance/compliance

## 1. Identity and dates

- Branch: `f027-governance-compliance`
- Capability area: enterprise security and administration (spec 5.8 SEC-03; section 4 record rules; section 6 privacy)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F027
- Aggregate: `compliance-policy`
- Module slug: `compliance`

## 2. Requirement specification

### Problem and user outcome

A regulated tenant must prove how long it keeps records, freeze records under litigation, hand over everything it stores on request, destroy data permanently when the retention period ends, and show auditors who could access what. Today soft-deleted rows linger forever, nothing prevents a purge during a dispute, and access questions are answered by hand.

As a compliance administrator, I want to set retention policies per record kind, place legal holds, export the whole tenant, run a purge that I confirm in a second step, and generate access-review reports, so that my organization meets its retention and audit obligations without engineering help.

### Functional requirements

- **FR-F027-01:** `GET /api/v1/compliance/retention-policies` returns one policy per record kind (`rows`, `sheets`, `documents`, `files`, `comments`, `workflow_runs`, `audit_events`, `notifications`) with `soft_delete_days` (1–3650, default 30), `purge_after_days` (≥ `soft_delete_days`, ≤ 3650, or `null` for keep forever), `version`, and `updated_by`; `audit_events` may only be set to `null` or ≥ 365.
- **FR-F027-02:** `PUT /api/v1/compliance/retention-policies/{id}` replaces a policy with `If-Match`; values outside the limits return `400 invalid` with `field_errors`; a stale version returns `409 conflict`; success publishes `retention-policy.updated.v1` and writes an audit event with the before/after values.
- **FR-F027-03:** A nightly worker job `compliance.retention` deletes (soft) records past `soft_delete_days` that are not already deleted only when the kind's `auto_soft_delete` flag is true, and marks soft-deleted records past `purge_after_days` as `purge_eligible`; the job never hard-deletes on its own.
- **FR-F027-04:** `POST /api/v1/compliance/legal-holds` creates a hold with `name`, `reason` (≤ 2,000 chars), `scope` (`tenant`, `workspace:{id}`, `sheet:{id}`, `user:{id}`), and optional `expires_at`; any record within an active hold's scope is excluded from retention soft delete, purge eligibility, and hard purge; `DELETE` releases the hold; both publish `legal-hold.applied.v1` with `action: applied|released`.
- **FR-F027-05:** A restore of a soft-deleted record under hold succeeds; a purge request that intersects a hold reports the held record count and skips those records; a hold cannot be released by the actor who created it when the tenant security policy requires two-person release.
- **FR-F027-06:** `POST /api/v1/compliance/tenant-exports` with `{ include: [kinds], format: "jsonl" | "csv", since?: timestamp }` enqueues a worker job and returns `202` with `id` and `status: queued`; at most one running export per tenant, a second request returns `409 conflict`.
- **FR-F027-07:** The export worker writes one file per kind plus `manifest.json` (counts, checksums, schema version, generated_at) into a ZIP in object storage, includes files as signed download URLs valid 7 days, redacts secrets (OAuth tokens, SCIM tokens, API token hashes), and completes within 4 hours for 1 million rows; `GET /api/v1/compliance/tenant-exports/{id}` returns `status` (`queued|running|completed|failed`), `progress` per kind, and a download URL when completed; completion publishes `tenant-export.completed.v1`.
- **FR-F027-08:** `POST /api/v1/compliance/purges` with `{ scope, kinds, older_than }` creates a purge request in `status: proposed` with a preview: candidate count per kind, held count per kind, and a `confirmation_code`; it never deletes.
- **FR-F027-09:** `POST /api/v1/compliance/purges/{id}/confirm` with `{ confirmation_code }` from a different `compliance-admin` than the proposer (or the same actor when the security policy allows single-person purge) and within 24 hours of the proposal moves the request to `confirmed`, publishes `purge.confirmed.v1`, and enqueues the purge job; a wrong code returns `400 invalid`, an expired proposal `409 conflict`, and the proposer confirming under two-person policy `403 denied`.
- **FR-F027-10:** The purge worker hard-deletes confirmed, non-held, soft-deleted records in batches of 1,000 with row counts recorded per batch, removes object-storage blobs for purged files, writes one `purge.executed` audit event per kind with counts, and marks the request `completed` with `purged_count` and `skipped_held_count`; audit events themselves are never purged by a purge request.
- **FR-F027-11:** `POST /api/v1/compliance/access-reviews` with `{ scope, as_of? }` generates a report listing each user and guest with their roles, group memberships, direct shares, share links, and API tokens for the scope; the report is stored as JSON plus a CSV rendering and publishes `access-review.generated.v1`; `GET /api/v1/compliance/access-reviews` lists reports with cursor pagination and `scope` filter.
- **FR-F027-12:** An access review includes `last_login_at` and `last_activity_at` per principal, flags principals inactive for more than 90 days and guests with links older than 30 days, and records reviewer decisions (`keep`, `revoke`) submitted to `POST /api/v1/compliance/access-reviews` with `{ report_id, decisions }` instead of `scope`; `revoke` decisions call F003 ACL and F038 token revocation and are audited.
- **FR-F027-13:** Every compliance route requires the `compliance-admin` role; other roles receive `403 denied`; cross-tenant IDs return `404 not_found`; every mutation requires `Idempotency-Key` and writes an audit event.
- **FR-F027-14:** The web compliance console lists policies, holds, exports, purges, and reviews; the purge flow shows the preview counts and asks the confirmer to retype the `confirmation_code`; exports and purges show live progress from the run status.

### Non-functional requirements

- **NFR-F027-01 Performance:** policy and hold reads respond in under 500 ms p95; export and purge requests are acknowledged in under 2 s; the purge job processes 100,000 rows in under 10 minutes without exceeding 1,000-row transactions; access review for 5,000 principals generates in under 60 s.
- **NFR-F027-02 Security/privacy:** exports are encrypted at rest in object storage, download URLs expire in 7 days and are audited on each use, secrets are redacted, purges require the two-step confirmation and honor holds, and all queries carry the `tenant_id` predicate.
- **NFR-F027-03 Accessibility:** the compliance console and the purge confirmation dialog pass axe with zero serious violations; the confirmation code field is labelled and errors are announced; progress bars expose `aria-valuenow`.
- **NFR-F027-04 Reliability/observability:** export and purge jobs are idempotent per request ID, resume from the last completed kind after a worker restart, bounded to 3 retries then dead-lettered with the request marked `failed`; metrics `compliance_job_duration_seconds{kind}` and `purge_rows_total` are emitted.

### Scope

Included: retention policies, retention job, legal holds with scopes and two-person release, tenant export job and download, purge proposal, preview, confirmation, execution, access-review generation and decisions, compliance console.

Excluded: per-sheet CSV/XLSX export (F010); audit log storage and query (F003); file scanning and storage (F017); regional residency (spec section 10 reserves `region`); entitlement packaging (F048); notification delivery for job completion (F037 consumes the events).

## 3. UX specification

- Entry points: admin navigation `Compliance`; routes `/admin/compliance/retention`, `/admin/compliance/holds`, `/admin/compliance/exports`, `/admin/compliance/purges`, `/admin/compliance/access-reviews`.
- Primary flow: administrator sets `rows` soft delete to 30 days and purge to 365, saves; creates hold `Case 2026-14` on workspace `Legal`; requests a tenant export and watches progress per kind until a `Download` link appears; proposes a purge of rows older than 365 days, sees `12,400 candidates, 310 held`; a second administrator opens the request, retypes the confirmation code, confirms; the purge completes with counts; the administrator generates an access review for workspace `Finance` and marks two inactive guests `revoke`.
- Loading: table skeletons; Empty: explanatory cards with the primary action; Error: banner with `correlation_id` and retry; Success: toasts for save, hold, export queued, purge confirmed; Stale/conflict: banner with reload; Denied: non-compliance-admins see the denied page; running exports and purges show progress bars and disable duplicate actions.
- Purge confirmation dialog: shows scope, kinds, candidate and held counts, proposer, expiry countdown, and a text field for the code; the button is labelled `Permanently delete 12,090 records` and is disabled until the code matches.
- Responsive: tables collapse to cards under 768 px; the confirmation dialog fits 320 px.
- Keyboard: all tables and dialogs are keyboard operable; `Escape` cancels; focus returns to the trigger; reduced motion disables progress animation.
- Font/icon/design tokens: Inter variable; Lucide icons `Archive`, `Gavel`, `Download`, `Trash2`, `ClipboardCheck`, `AlertOctagon`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/compliance/`: `RetentionPolicy { id, tenant_id, kind: RecordKind, soft_delete_days: u16, purge_after_days: Option<u16>, auto_soft_delete: bool, version, audit fields }`, `LegalHold { id, tenant_id, name, reason, scope: HoldScope, expires_at, released_at, released_by, version, audit fields }`, `TenantExport { id, tenant_id, include: Vec<RecordKind>, format, since, status: JobStatus, progress: Map<RecordKind, Progress>, storage_key, download_expires_at, error, audit fields }`, `PurgeRequest { id, tenant_id, scope, kinds, older_than, status: Proposed|Confirmed|Running|Completed|Failed|Expired, preview: Map<RecordKind, { candidates, held }>, confirmation_code_hash, proposed_by, confirmed_by, confirmed_at, purged_count, skipped_held_count, audit fields }`, `AccessReview { id, tenant_id, scope, as_of, principal_count, flagged_count, storage_key_json, storage_key_csv, decisions: Vec<Decision>, audit fields }`.
- Use cases: `list_retention_policies`, `put_retention_policy`, `run_retention_sweep`, `create_legal_hold`, `release_legal_hold`, `is_held(record_ref)`, `request_tenant_export`, `get_tenant_export`, `run_tenant_export`, `propose_purge`, `confirm_purge`, `run_purge`, `generate_access_review`, `record_review_decisions`, `list_access_reviews`.
- API endpoints (`services/api/src/compliance/`): `GET /api/v1/compliance/retention-policies`, `PUT /api/v1/compliance/retention-policies/{id}`, `POST /api/v1/compliance/legal-holds`, `DELETE /api/v1/compliance/legal-holds/{id}`, `POST /api/v1/compliance/tenant-exports`, `GET /api/v1/compliance/tenant-exports/{id}`, `POST /api/v1/compliance/purges`, `POST /api/v1/compliance/purges/{id}/confirm`, `GET /api/v1/compliance/access-reviews`, `POST /api/v1/compliance/access-reviews`. DTOs: `RetentionPolicyResponse`, `PutRetentionPolicyRequest`, `CreateLegalHoldRequest`, `LegalHoldResponse`, `CreateTenantExportRequest`, `TenantExportResponse`, `ProposePurgeRequest`, `PurgePreviewResponse`, `ConfirmPurgeRequest`, `PurgeResponse`, `GenerateAccessReviewRequest`, `AccessReviewResponse`, `Page<AccessReviewResponse>`.
- Worker jobs (`services/worker/src/compliance/`): `retention_sweep` (nightly 02:00 tenant local), `tenant_export`, `purge_execute`, each consuming JetStream subjects `jobs.compliance.<name>` with per-tenant quota 1, timeout 4 h, 3 retries, dead letter.
- Events: `retention-policy.updated.v1`, `legal-hold.applied.v1`, `tenant-export.completed.v1`, `purge.confirmed.v1`, `access-review.generated.v1`; payload per contract conventions.
- Authorization: `compliance-admin` for every route; two-person rules read `security_policies.two_person_purge` and `two_person_hold_release` from F038; cross-tenant maps to `not_found`.
- Validation: day limits per FR-F027-01; hold `name` 1–200; `scope` parsed into `HoldScope`; export `include` non-empty subset of kinds; purge `older_than` ≥ 1 day; confirmation code 8 uppercase alphanumerics compared by SHA-256.
- Error mapping: `ComplianceError::LimitExceeded → 400 invalid`, `::StaleVersion → 409 conflict`, `::ExportRunning → 409 conflict`, `::ProposalExpired → 409 conflict`, `::WrongCode → 400 invalid`, `::SameActor → 403 denied`, `::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_compliance_*.sql` creates `retention_policies(id uuid pk, tenant_id, kind text not null, soft_delete_days smallint not null, purge_after_days smallint null, auto_soft_delete bool not null default false, version bigint, audit fields, unique (tenant_id, kind))`, `legal_holds(id, tenant_id, name text, reason text, scope_kind text, scope_id uuid null, expires_at timestamptz null, released_at timestamptz null, released_by uuid null, version, audit fields)`, `tenant_exports(id, tenant_id, include text[], format text, since timestamptz null, status text, progress jsonb not null default '{}', storage_key text null, download_expires_at timestamptz null, error jsonb null, audit fields)`, `purge_requests(id, tenant_id, scope_kind, scope_id, kinds text[], older_than timestamptz, status text, preview jsonb, confirmation_code_hash bytea, proposed_by uuid, confirmed_by uuid null, confirmed_at timestamptz null, purged_count bigint default 0, skipped_held_count bigint default 0, error jsonb null, audit fields)`, `access_reviews(id, tenant_id, scope_kind, scope_id, as_of timestamptz, principal_count int, flagged_count int, storage_key_json text, storage_key_csv text, decisions jsonb not null default '[]', audit fields)`, and `purge_batches(purge_id, batch_no, kind, deleted_count, completed_at, primary key (purge_id, batch_no))`.
- Invariants: partial unique index `tenant_exports(tenant_id) where status in ('queued','running')`; check `purge_after_days is null or purge_after_days >= soft_delete_days`; check `kind = 'audit_events' implies purge_after_days is null or >= 365`; `purge_requests.status` transitions enforced in service code and checked by a trigger that rejects `completed` without `confirmed_at`.
- Indexes: `legal_holds(tenant_id, scope_kind, scope_id) where released_at is null`, `purge_requests(tenant_id, status, created_at desc)`, `access_reviews(tenant_id, created_at desc)`, `tenant_exports(tenant_id, created_at desc)`.
- Audit events: `retention-policy.update`, `legal-hold.apply`, `legal-hold.release`, `tenant-export.request`, `tenant-export.download`, `purge.propose`, `purge.confirm`, `purge.executed`, `access-review.generate`, `access-review.decide`.
- Retention/deletion: compliance tables are never purged by purge requests; `tenant_exports` blobs expire after 7 days by object-storage lifecycle; rollback drops the six tables and the trigger.

### React/TypeScript

- Routes: `/admin/compliance/retention`, `/admin/compliance/holds`, `/admin/compliance/exports`, `/admin/compliance/purges`, `/admin/compliance/access-reviews` in `apps/web/src/features/compliance/`; components `CompliancePage`, `RetentionTable`, `LegalHoldTable`, `NewHoldDialog`, `ExportPanel`, `ExportProgress`, `PurgeWizard`, `PurgePreview`, `PurgeConfirmDialog`, `AccessReviewList`, `AccessReviewDetail`, `DecisionTable`.
- State: TanStack Query keys `['retention-policies']`, `['legal-holds']`, `['tenant-export', id]` (polls every 5 s while running), `['purge', id]`, `['access-reviews', cursor]`, `['access-review', id]`.
- API client: generated `ComplianceApi` with `listRetentionPolicies`, `putRetentionPolicy`, `createLegalHold`, `releaseLegalHold`, `requestTenantExport`, `getTenantExport`, `proposePurge`, `confirmPurge`, `listAccessReviews`, `generateAccessReview`.
- Telemetry: `retention_policy_saved`, `legal_hold_applied`, `tenant_export_requested`, `purge_proposed`, `purge_confirmed`, `access_review_generated` with `tenant_id` and kind or scope.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F027-01 through FR-F027-14 in `testing/features/F027/requirements/cases.md`
- [ ] Failure/edge-case tests: purge intersecting a hold, expired proposal, wrong confirmation code, same-actor confirm under two-person policy, second concurrent export, worker restart mid-export, audit_events policy below 365
- [ ] Permission-negative and tenant-isolation tests: tenant-admin without compliance-admin gets `denied`, foreign-tenant IDs return `not_found`, download URL from another tenant rejected
- [ ] Rust unit tests: `crates/domain/src/compliance/` hold scope matching, retention day validation, purge state machine, redaction of secrets in export
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: one running export, policy checks, purge trigger, rollback
- [ ] React component tests: `RetentionTable`, `PurgeWizard`, `PurgeConfirmDialog`, `ExportProgress`, `DecisionTable` states
- [ ] Browser E2E tests: hold then export then two-person purge then access review
- [ ] Accessibility tests: axe on all five routes and the purge dialog
- [ ] Performance/load tests: purge 100,000 rows under 10 minutes, review 5,000 principals under 60 s

### Fast fanout configuration

- Test harness path: `testing/features/F027/`
- Feature flag: `F027_FEATURE`
- Fixture/seed factory: `testing/fixtures/compliance.rs` builds tenant A and B, two compliance-admins, one tenant-admin, a workspace with 3 sheets and 12,400 soft-deleted rows of mixed ages, 310 rows under hold, 40 principals including 3 stale guests
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed confirmation code generator seed
- Mock/stub contracts: MinIO from the compose baseline for export blobs; outbox publisher recorded in memory; worker run in-process with a controllable clock
- Parallel isolation: one schema per test worker, tenant ID per test, bucket prefix per test
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F027/`

## 6. Acceptance criteria

```gherkin
Feature: Retention, legal hold, export, purge, and access review

Scenario: Legal hold protects records from purge
  Given a hold on workspace "Legal" covering 310 soft-deleted rows
  When a compliance-admin proposes a purge of rows older than 365 days
  Then the preview reports 12,400 candidates and 310 held
  And after confirmation the purge completes with purged_count 12,090 and skipped_held_count 310

Scenario: Two-person purge confirmation
  Given the tenant security policy requires two-person purge
  When the proposer posts the confirmation code
  Then the response is 403 denied and the request stays proposed

Scenario: Tenant-admin without compliance role is denied
  Given a tenant-admin who is not a compliance-admin
  When they GET /api/v1/compliance/retention-policies
  Then the response is 403 denied

Scenario: Tenant export completes with manifest
  Given 3 sheets, 40 files, and 200 comments
  When an export of all kinds is requested
  Then the job completes with a ZIP containing one file per kind and manifest.json checksums
  And tenant-export.completed.v1 is published and secrets are absent from the archive
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F003 (roles, ACLs, audit events); F010 (export job infrastructure and file writers); decisions sections 2, 3, 4, 7; contracts row F027
- Blocks: none in the plan
- Conflicts with: none (disjoint owned paths)
- External dependencies: S3-compatible object storage lifecycle rules for export expiry
- Risks and mitigations: purge of large tables can bloat and lock, mitigated by 1,000-row batches, `purge_batches` checkpoints, and off-peak scheduling; hold scope drift when records move between workspaces, mitigated by evaluating hold membership at purge time by current and historical workspace from audit events; export archives leaking secrets, mitigated by a redaction allowlist per kind tested against fixture secrets.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F003 and F010 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F027/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory with mixed-age soft-deleted rows available in `testing/fixtures/compliance.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and job completion
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F027_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Compliance administrators can set retention per record kind, apply legal holds, export the whole tenant, run a two-step verified purge that honors holds, and generate access-review reports with revoke decisions.
- Migration adds `retention_policies`, `legal_holds`, `tenant_exports`, `purge_requests`, `purge_batches`, and `access_reviews`; rollback drops them. Feature is off by default behind `F027_FEATURE`.
