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
owned_paths: [crates/domain/src/compliance/**, crates/persistence/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, services/api/migrations/*_compliance_*.sql, testing/features/F027/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F027
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
- **FR-F027-06:** `POST /api/v1/compliance/tenant-exports` with `{ include: [kinds], format: "jsonl" | "csv", since?: timestamp }` enqueues a worker job and returns `202` with `id` and `status: queued`; each requested kind is written as one `tenant_export_kinds` row with `status: 'pending'`, so an unknown kind fails the row `check` rather than being accepted into an array; at most one running export per tenant, a second request returns `409 conflict`.
- **FR-F027-07:** The export worker writes one file per kind plus `manifest.json` (counts, checksums, schema version, generated_at) into a ZIP in object storage, includes files as signed download URLs valid 7 days, redacts secrets (OAuth tokens, SCIM tokens, API token hashes), and completes within 4 hours for 1 million rows; per-kind `status`, `rows_written`, `bytes_written`, `checksum_sha256`, and `completed_at` are updated on the kind's own `tenant_export_kinds` row as it finishes; `GET /api/v1/compliance/tenant-exports/{id}` returns `status` (`queued|running|completed|failed`) and reassembles those rows into the `progress` object keyed by kind, plus a download URL when completed; completion publishes `tenant-export.completed.v1`.
- **FR-F027-08:** `POST /api/v1/compliance/purges` with `{ scope, kinds, older_than }` creates a purge request in `status: proposed` and writes one `purge_request_kinds` row per kind holding `candidate_count` and `held_count`; the response reassembles those rows into the `preview` object and returns a `confirmation_code`; it never deletes.
- **FR-F027-09:** `POST /api/v1/compliance/purges/{id}/confirm` with `{ confirmation_code }` from a different `compliance-admin` than the proposer (or the same actor when the security policy allows single-person purge) and within 24 hours of the proposal moves the request to `confirmed`, publishes `purge.confirmed.v1`, and enqueues the purge job; a wrong code returns `400 invalid`, an expired proposal `409 conflict`, and the proposer confirming under two-person policy `403 denied`.
- **FR-F027-10:** The purge worker hard-deletes confirmed, non-held, soft-deleted records in batches of 1,000 with row counts recorded per batch in `purge_batches`, removes object-storage blobs for purged files, accumulates `purged_count` and `skipped_held_count` on the kind's `purge_request_kinds` row, writes one `purge.executed` audit event per kind with those counts, and marks the request `completed` with the summed `purged_count` and `skipped_held_count`; audit events themselves are never purged by a purge request.
- **FR-F027-11:** `POST /api/v1/compliance/access-reviews` with `{ scope, as_of? }` generates a report writing one `access_review_principals` row per user and guest in scope with `role_count`, `group_count`, `share_count`, `link_count`, and `token_count`; the report is also rendered to JSON and CSV blobs in object storage for download and publishes `access-review.generated.v1`; `GET /api/v1/compliance/access-reviews` lists reports with cursor pagination and `scope` filter.
- **FR-F027-12:** Each `access_review_principals` row carries `last_login_at` and `last_activity_at` and a `flag_reason` of `inactive_90d`, `stale_guest_link`, or `none`, so flagged principals are indexed rather than scanned out of a document; reviewer decisions (`keep`, `revoke`) submitted to `POST /api/v1/compliance/access-reviews` with `{ report_id, decisions }` instead of `scope` are written as `access_review_decisions` rows keyed by `(review_id, principal_id)`, which makes a second decision for the same principal an update rather than a duplicate; `revoke` decisions call F003 ACL and F038 token revocation, record the `outcome` on the row, and are audited.
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
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Archive`, `Gavel`, `Download`, `Trash2`, `ClipboardCheck`, `AlertOctagon`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Governance.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/compliance/` holds `RetentionPolicyRepository` (owns `retention_policies`), `LegalHoldRepository` (`legal_holds`), `TenantExportRepository` (`tenant_exports`, `tenant_export_kinds`), `PurgeRequestRepository` (`purge_requests`, `purge_request_kinds`, `purge_batches`), and `AccessReviewRepository` (`access_reviews`, `access_review_principals`, `access_review_decisions`). Each child table is written only by the repository of its parent object type, so no two classes write the same table. Named queries: `seed_defaults_for_tenant`, `list_policies`, `find_policy_by_kind`, `put_policy_under_version`; `list_active_holds`, `find_holds_covering`, `count_held_by_kind`, `mark_released`; `find_running_export_for_tenant`, `insert_export_with_kinds`, `list_export_kinds`, `claim_next_pending_kind`, `complete_export_kind`, `set_download_target`, `fail_export`; `insert_proposal_with_preview`, `load_purge_with_kinds`, `confirm_with_code_hash`, `record_purge_batch`, `last_completed_batch`, `accumulate_kind_counts`, `finish_purge_with_counts`; `insert_review_with_principals`, `list_reviews_by_scope`, `list_principals_flagged_first`, `upsert_decisions`, `count_decided`. No generic query escape hatch is exposed. The use cases below depend on these repository traits and contain no SQL; the API handlers, the `retention_sweep`, `tenant_export`, `purge_execute`, and `access_review` workers, and the fixtures all reach PostgreSQL through them. The retention sweep and the purge worker never touch another feature's tables directly: they call `soft_delete` and `purge` on the owning repositories of F006, F045, F017, F016, and F019 through a `RetentionTarget` port resolved per `RecordKind`. Multi-table writes run in one `UnitOfWork`: proposal insert plus its preview rows, confirmation plus the outbox enqueue, a purge batch plus its counter update, and report insert plus principal rows.
- Domain entities in `crates/domain/src/compliance/`: `RetentionPolicy { id, tenant_id, kind: RecordKind, soft_delete_days: u16, purge_after_days: Option<u16>, auto_soft_delete: bool, version, audit fields }`, `LegalHold { id, tenant_id, name, reason, scope: HoldScope, expires_at, released_at, released_by, version, audit fields }`, `TenantExport { id, tenant_id, format, since, status: JobStatus, storage_key, download_expires_at, error_code, error_message, audit fields }` with `ExportKind { export_id, kind: RecordKind, status, rows_written, bytes_written, checksum_sha256, completed_at }` loaded alongside it, `PurgeRequest { id, tenant_id, scope, older_than, status: Proposed|Confirmed|Running|Completed|Failed|Expired, confirmation_code_hash, proposed_by, confirmed_by, confirmed_at, purged_count, skipped_held_count, error_code, error_message, audit fields }` with `PurgeKind { purge_id, kind, candidate_count, held_count, purged_count, skipped_held_count, completed_at }`, `AccessReview { id, tenant_id, scope, as_of, principal_count, flagged_count, storage_key_json, storage_key_csv, audit fields }` with `ReviewPrincipal { review_id, principal_id, principal_kind, display_name, role_count, group_count, share_count, link_count, token_count, last_login_at, last_activity_at, flag_reason }` and `ReviewDecision { review_id, principal_id, decision, note, decided_by, decided_at, outcome }`. `TenantExport::progress`, `PurgeRequest::preview`, and `AccessReview::decisions` remain map- and vector-shaped in the DTO layer; the repositories build them from the child rows.
- Use cases: `list_retention_policies`, `put_retention_policy`, `run_retention_sweep`, `create_legal_hold`, `release_legal_hold`, `is_held(record_ref)`, `request_tenant_export`, `get_tenant_export`, `run_tenant_export`, `propose_purge`, `confirm_purge`, `run_purge`, `generate_access_review`, `record_review_decisions`, `list_access_reviews`.
- API endpoints (`services/api/src/compliance/`): `GET /api/v1/compliance/retention-policies`, `PUT /api/v1/compliance/retention-policies/{id}`, `POST /api/v1/compliance/legal-holds`, `DELETE /api/v1/compliance/legal-holds/{id}`, `POST /api/v1/compliance/tenant-exports`, `GET /api/v1/compliance/tenant-exports/{id}`, `POST /api/v1/compliance/purges`, `POST /api/v1/compliance/purges/{id}/confirm`, `GET /api/v1/compliance/access-reviews`, `POST /api/v1/compliance/access-reviews`. DTOs: `RetentionPolicyResponse`, `PutRetentionPolicyRequest`, `CreateLegalHoldRequest`, `LegalHoldResponse`, `CreateTenantExportRequest`, `TenantExportResponse`, `ProposePurgeRequest`, `PurgePreviewResponse`, `ConfirmPurgeRequest`, `PurgeResponse`, `GenerateAccessReviewRequest`, `AccessReviewResponse`, `Page<AccessReviewResponse>`.
- Worker jobs (`services/worker/src/compliance/`): `retention_sweep` (nightly 02:00 tenant local), `tenant_export`, `purge_execute`, each consuming JetStream subjects `jobs.compliance.<name>` with per-tenant quota 1, timeout 4 h, 3 retries, dead letter.
- Events: `retention-policy.updated.v1`, `legal-hold.applied.v1`, `tenant-export.completed.v1`, `purge.confirmed.v1`, `access-review.generated.v1`; payload per contract conventions.
- Authorization: `compliance-admin` for every route; two-person rules read `security_policies.two_person_purge` and `two_person_hold_release` from F038; cross-tenant maps to `not_found`.
- Validation: day limits per FR-F027-01; hold `name` 1–200; `scope` parsed into `HoldScope`; export `include` non-empty subset of kinds; purge `older_than` ≥ 1 day; confirmation code 8 uppercase alphanumerics compared by SHA-256.
- Error mapping: `ComplianceError::LimitExceeded → 400 invalid`, `::StaleVersion → 409 conflict`, `::ExportRunning → 409 conflict`, `::ProposalExpired → 409 conflict`, `::WrongCode → 400 invalid`, `::SameActor → 403 denied`, `::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### Interface

Ids are UUIDv7 strings, timestamps RFC 3339 UTC, `version` increments by one per write. `T?` is
nullable and an absent optional field equals an explicit `null`. Unlisted fields are rejected with
`400 invalid`. `Page<T>`, the opaque cursor and the error body `{ code, message, field_errors,
correlation_id }` are F028's. Every route requires `compliance-admin`; every mutation requires
`Idempotency-Key`.

**`RecordKind`** — the closed set every policy, export, purge and batch is keyed by:
`rows | sheets | documents | files | comments | workflow_runs | audit_events | notifications`. It is
the same list as the `check` constraint on `retention_policies.kind`, and a value outside it is
`400 invalid` with `field_errors.<field> = "enum"`.

**`GET /api/v1/compliance/retention-policies`** returns `{ policies: RetentionPolicyResponse[] }`,
exactly one entry per `RecordKind` in that order. It takes no cursor and no filter: the collection is
closed at eight rows, seeded per tenant, and neither grows nor shrinks.

**`RetentionPolicyResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | stable per `(tenant, kind)`; this is the `{id}` of the `PUT` |
| `kind` | RecordKind | immutable |
| `soft_delete_days` | integer | |
| `purge_after_days` | integer? | null means keep forever |
| `auto_soft_delete` | bool | when false the nightly sweep only marks eligibility and deletes nothing |
| `version`, `updated_at`, `updated_by`, `created_at`, `created_by` | | |

**`PutRetentionPolicyRequest`** — `PUT /api/v1/compliance/retention-policies/{id}`, a whole
replacement, `If-Match` required. `kind` is not in the body: the path identifies it.

| Field | Type | Required | Constraint |
|---|---|---|---|
| `soft_delete_days` | integer | yes | `1..=3650` |
| `purge_after_days` | integer? | yes | null, or `soft_delete_days..=3650`; smaller → `field_errors.purge_after_days = "below_soft_delete"` |
| `auto_soft_delete` | bool | yes | |

For `kind = audit_events`, `purge_after_days` must be null or `>= 365`, else `400 invalid` with
`field_errors.purge_after_days = "audit_floor"`.

**`CreateLegalHoldRequest`** — `POST /api/v1/compliance/legal-holds`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | yes | 1–200 chars after trim |
| `reason` | string | yes | 1–2,000 chars |
| `scope` | string | yes | `"tenant"`, or `"workspace:{uuid}"`, `"sheet:{uuid}"`, `"user:{uuid}"`; the referenced object must exist in this tenant, else `404 not_found`; a malformed prefix is `400 invalid` with `field_errors.scope = "format"` |
| `expires_at` | timestamp? | no | strictly in the future; null means until released |

**`LegalHoldResponse`**: `{ id, name, reason, scope, expires_at?, released_at?, released_by?, active: bool, version, created_at, created_by, updated_at, updated_by }`. `active` is `released_at is null and (expires_at is null or expires_at > now)`, computed on read.

`DELETE /api/v1/compliance/legal-holds/{id}` releases the hold and returns `200` with the updated
`LegalHoldResponse`; it does not remove the row, because the release itself is evidence. Releasing an
already-released hold is `409 conflict` with `field_errors.released_at = "already_released"`. Under
`security_policies.two_person_hold_release`, release by the hold's `created_by` is `403 denied`.

**`CreateTenantExportRequest`** — `POST /api/v1/compliance/tenant-exports`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `include` | RecordKind[] | yes | 1–8 distinct entries; each becomes one `tenant_export_kinds` row |
| `format` | `"jsonl" \| "csv"` | yes | |
| `since` | timestamp? | no | not in the future; null exports everything |

Returns `202` with `TenantExportResponse` in `queued`. A second request while one is `queued` or
`running` is `409 conflict` with `field_errors.tenant_id = "export_running"`.

**`TenantExportResponse`** — `GET /api/v1/compliance/tenant-exports/{id}`

| Field | Type | Notes |
|---|---|---|
| `id`, `format`, `since?` | | |
| `status` | `"queued"\|"running"\|"completed"\|"failed"` | |
| `progress` | map<RecordKind, ExportKindProgress> | reassembled from `tenant_export_kinds`, one entry per requested kind |
| `download_url` | string? | signed URL, present only while `status` is `completed` and `download_expires_at` is in the future |
| `download_expires_at` | timestamp? | present under the same condition; 7 days after completion |
| `error_code` / `error_message` | string? | present only when `failed`; `error_code` is one of `storage_unavailable`, `source_read_failed`, `timeout`, `cancelled` |
| `created_at`, `created_by`, `updated_at` | | |

**`ExportKindProgress`**: `{ status: "pending"|"running"|"completed"|"failed", rows_written, bytes_written, checksum_sha256: string?, completed_at: timestamp? }`, `checksum_sha256` lowercase hex and null until the kind completes.

**`ProposePurgeRequest`** — `POST /api/v1/compliance/purges`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `scope` | string | yes | same grammar as a hold's `scope` |
| `kinds` | RecordKind[] | yes | 1–8 distinct entries; `audit_events` is rejected with `field_errors.kinds = "not_purgeable"`, because a purge never removes its own evidence |
| `older_than` | timestamp | yes | at least 1 day in the past, else `field_errors.older_than = "too_recent"` |

**`PurgePreviewResponse`** — the `201` body of the proposal

| Field | Type | Notes |
|---|---|---|
| `id`, `scope`, `older_than` | | |
| `status` | `"proposed"` | |
| `preview` | map<RecordKind, { candidate_count, held_count }> | reassembled from `purge_request_kinds`; counts are a point-in-time estimate and are recomputed at execution |
| `confirmation_code` | string | 8 uppercase alphanumerics, returned **once** here and never stored in plain form or returned again |
| `expires_at` | timestamp | proposal time plus 24 hours |
| `proposed_by`, `created_at`, `version` | | |

**`ConfirmPurgeRequest`** — `POST /api/v1/compliance/purges/{id}/confirm`: `{ confirmation_code: string }`, compared by SHA-256 against `confirmation_code_hash`.

**`PurgeResponse`** — the confirm body and the purge read

| Field | Type | Notes |
|---|---|---|
| `id`, `scope`, `older_than`, `preview` | | as above |
| `status` | `"proposed"\|"confirmed"\|"running"\|"completed"\|"failed"\|"expired"` | |
| `results` | map<RecordKind, { purged_count, skipped_held_count, completed_at: timestamp? }> | from `purge_request_kinds`; zeroed until the worker runs |
| `purged_count` / `skipped_held_count` | integer | the sums over `results`, maintained on the request row |
| `proposed_by`, `confirmed_by?`, `confirmed_at?` | uuid / timestamp | |
| `error_code` / `error_message` | string? | only when `failed`; `error_code` is `storage_unavailable`, `delete_failed`, `timeout` or `cancelled` |

**`GenerateAccessReviewRequest`** — `POST /api/v1/compliance/access-reviews` carries **either** a
generation body or a decision body, discriminated by the presence of `report_id`. Both in one request
is `400 invalid` with `field_errors.report_id = "exclusive"`.

| Field | Type | Required | Constraint |
|---|---|---|---|
| `scope` | string | generation | `"tenant"` or `"workspace:{uuid}"`; holds' `sheet:` and `user:` forms are not review scopes |
| `as_of` | timestamp? | no | not in the future; null means now |
| `report_id` | uuid? | decision | an `access_reviews` row of this tenant |
| `decisions` | ReviewDecision[] | decision | 1–5,000 entries, `principal_id` distinct, each already present in `access_review_principals` for that review, else `400 invalid` with `field_errors.decisions[i].principal_id = "not_in_review"` |

**`ReviewDecision`** (request): `{ principal_id: uuid, decision: "keep"|"revoke", note: string? (≤ 1,000) }`. Re-deciding a principal replaces the prior row rather than adding one; the composite primary key is what makes that true.

**`AccessReviewResponse`**: `{ id, scope, as_of, principal_count, flagged_count, decided_count, download_url_json: string?, download_url_csv: string?, principals: ReviewPrincipal[]?, version, created_at, created_by }`. `principals` is present only on the single-report read and is ordered flagged-first then by `display_name`; the list route omits it. **`ReviewPrincipal`**: `{ principal_id, principal_kind: "user"|"guest", display_name, role_count, group_count, share_count, link_count, token_count, last_login_at?, last_activity_at?, flag_reason: "none"|"inactive_90d"|"stale_guest_link", decision: "keep"|"revoke"|null, outcome: "pending"|"applied"|"partial"|"failed"|null }` — `decision` and `outcome` are null until a decision row exists.

**`GET /api/v1/compliance/access-reviews`** returns `Page<AccessReviewResponse>` sorted `created_at desc`, filtered by `scope`, with F028's `cursor`, `limit` (1–100, default 50) and `include_total`.

Status codes:

| Code | Produced by |
|---|---|
| `200` | reads, `PUT` of a policy, hold release, purge confirm, decision submission |
| `201` | legal hold, purge proposal, access-review generation |
| `202` | tenant export request |
| `400 invalid` | day bounds, `audit_floor`, `below_soft_delete`, scope format, `not_purgeable`, `too_recent`, wrong `confirmation_code`, `not_in_review`, `exclusive` |
| `403 denied` | any actor without `compliance-admin`; the proposer confirming under `two_person_purge`; the hold creator releasing under `two_person_hold_release` |
| `404 not_found` | a policy, hold, export, purge, review or scope target in another tenant, or a scope object the caller cannot read |
| `409 conflict` | stale `If-Match`, `export_running`, `already_released`, an expired proposal, confirming a request not in `proposed`, `Idempotency-Key` replayed with a different body |
| `429 rate_limited` | tenant export or purge quota exceeded |
| `503 unavailable` | object storage or the JetStream work stream refuses the job; nothing is written |

### Use case signatures

In `crates/domain/src/compliance/`; workers in `services/worker/src/compliance/`. `Ctx` is F038's
`ActorContext`.

```rust
fn list_retention_policies(ctx: &Ctx, repo: &dyn RetentionPolicyRepository) -> Result<Vec<RetentionPolicy>, DomainError>;
fn put_retention_policy(ctx: &Ctx, uow: &mut UnitOfWork, id: PolicyId, expected: Version, req: PutRetentionPolicy) -> Result<RetentionPolicy, DomainError>;
fn run_retention_sweep(ctx: &Ctx, uow: &mut UnitOfWork, kind: RecordKind, batch: usize) -> Result<SweepReport, DomainError>;
fn create_legal_hold(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateLegalHold) -> Result<LegalHold, DomainError>;
fn release_legal_hold(ctx: &Ctx, uow: &mut UnitOfWork, id: HoldId, expected: Version) -> Result<LegalHold, DomainError>;
fn request_tenant_export(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateTenantExport) -> Result<TenantExport, DomainError>;
fn get_tenant_export(ctx: &Ctx, repo: &dyn TenantExportRepository, id: ExportId) -> Result<TenantExport, DomainError>;
fn run_tenant_export(ctx: &Ctx, uow: &mut UnitOfWork, id: ExportId, store: &dyn BlobStore) -> Result<TenantExport, DomainError>;
fn propose_purge(ctx: &Ctx, uow: &mut UnitOfWork, req: ProposePurge) -> Result<(PurgeRequest, PlaintextCode), DomainError>;
fn confirm_purge(ctx: &Ctx, uow: &mut UnitOfWork, id: PurgeId, code: &str, clock: &dyn Clock) -> Result<PurgeRequest, DomainError>;
fn run_purge(ctx: &Ctx, uow: &mut UnitOfWork, id: PurgeId, batch: usize) -> Result<PurgeRequest, DomainError>;
fn generate_access_review(ctx: &Ctx, uow: &mut UnitOfWork, req: GenerateAccessReview) -> Result<AccessReview, DomainError>;
fn record_review_decisions(ctx: &Ctx, uow: &mut UnitOfWork, review: ReviewId, decisions: Vec<ReviewDecision>) -> Result<AccessReview, DomainError>;
fn list_access_reviews(ctx: &Ctx, repo: &dyn AccessReviewRepository, filter: ReviewFilter, page: Cursor) -> Result<Page<AccessReview>, DomainError>;
```

#### Ports other features implement or call

These three traits are the whole surface F027 exposes to other modules — F070's trash calls all three
— so they are defined here in full rather than described. They live in `crates/domain/src/compliance/ports.rs`.

```rust
/// Answers "how long does this kind live?" without exposing the policy table.
/// F070's trash uses it to compute `expires_at = deleted_at + purge_after_days`.
pub trait RetentionPolicyPort: Send + Sync {
    fn policy_for(&self, ctx: &Ctx, kind: RecordKind) -> Result<RetentionPolicy, DomainError>;
    /// `None` means keep forever: either `purge_after_days` is null, or the tenant has no
    /// policy row for this kind. Callers must render no countdown, never a zero one.
    fn purge_after(&self, ctx: &Ctx, kind: RecordKind) -> Result<Option<Days>, DomainError>;
    fn expires_at(&self, ctx: &Ctx, kind: RecordKind, deleted_at: Timestamp) -> Result<Option<Timestamp>, DomainError>;
}

/// The single audited hard-delete path. Nothing outside this trait may hard-delete tenant data,
/// which is why `DELETE /api/v1/trash/{kind}/{id}` routes through it rather than deleting directly.
pub trait PurgeExecutorPort: Send + Sync {
    /// Purge one item. Consults `LegalHoldPort` first and returns `Skipped` when held —
    /// a hold is not an error, and the caller records the skip.
    fn purge_item(&self, ctx: &Ctx, uow: &mut UnitOfWork, kind: RecordKind, item: ItemId) -> Result<PurgeOutcome, DomainError>;
    /// Purge a batch under one transaction, capped at 1,000 items, writing one `purge_batches`
    /// row and one `purge.executed` audit event for the batch.
    fn purge_batch(&self, ctx: &Ctx, uow: &mut UnitOfWork, kind: RecordKind, items: &[ItemId], request: Option<PurgeId>) -> Result<PurgeBatchReport, DomainError>;
}

/// A hold always beats a policy, so every purge path consults this before deleting anything.
pub trait LegalHoldPort: Send + Sync {
    fn is_held(&self, ctx: &Ctx, kind: RecordKind, item: ItemId) -> Result<Option<HoldRef>, DomainError>;
    fn count_held(&self, ctx: &Ctx, kind: RecordKind, scope: &HoldScope, older_than: Timestamp) -> Result<u64, DomainError>;
}
```

`PurgeOutcome` is `Purged { blobs_removed: u32 } | Skipped { hold: HoldRef } | Absent`;
`PurgeBatchReport` is `{ purged_count, skipped_held_count, batch_no }`; `HoldRef` is
`{ hold_id, name }` and is what a `409 conflict` names when a caller tries to purge a held item.
`purge_batch` takes `request: Option<PurgeId>` so a governance purge attributes its batch to the
request while a trash purge-now attributes to none, and both write the same audit event.

Transaction boundaries:

- `put_retention_policy` writes the policy row, its audit row and the outbox event in one
  `UnitOfWork` under `If-Match`.
- `request_tenant_export` writes the `tenant_exports` row, every `tenant_export_kinds` row and the
  JetStream message through the outbox in one boundary. The partial unique index enforcing one
  running export per tenant is only meaningful if the row and its kinds appear atomically.
- `propose_purge` writes the request row, every `purge_request_kinds` row with its preview counts, and
  the audit row in one boundary; `confirm_purge` writes the status transition, `confirmed_by`,
  `confirmed_at`, the audit row and the `purge.confirmed.v1` outbox row in another. They are separate
  transactions on purpose: the proposal and the confirmation are two acts by two people.
- `run_purge` opens **one `UnitOfWork` per batch of 1,000**, covering that batch's hard deletes, its
  `purge_batches` row and the `purge_request_kinds` counter update. Per batch, not per request: a
  million-row purge in one transaction would hold locks for minutes, and the `purge_batches` row is
  the resume checkpoint that makes a restarted worker skip what it already deleted.
- `run_tenant_export` opens one `UnitOfWork` per kind, completing that kind's row after its file is
  written, so a restarted worker resumes at the first `pending` kind instead of rewriting the ZIP.
- `generate_access_review` writes the `access_reviews` row and every `access_review_principals` row in
  one boundary — `flagged_count` is derived from those rows and would be wrong against a partial set.
  `record_review_decisions` writes every decision row, the F003 ACL revocations and F038 token
  revocations they imply, each row's `outcome`, and the audit rows in one boundary, so a `revoke`
  recorded as applied always corresponds to access actually removed.

### PostgreSQL/SQLx

- Migration `*_compliance_*.sql` creates: `retention_policies(id uuid pk, tenant_id uuid not null, kind text not null check (kind in ('rows','sheets','documents','files','comments','workflow_runs','audit_events','notifications')), soft_delete_days smallint not null, purge_after_days smallint null, auto_soft_delete bool not null default false, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, updated_by uuid not null references users(id) on delete restrict, created_at, updated_at, deleted_at, unique (tenant_id, kind))`; `legal_holds(id, tenant_id, name text not null, reason text not null, scope_kind text not null check (scope_kind in ('tenant','workspace','sheet','user')), scope_id uuid null, expires_at timestamptz null, released_at timestamptz null, released_by uuid null references users(id) on delete restrict, version, audit fields, check ((scope_kind = 'tenant') = (scope_id is null)))`; `tenant_exports(id, tenant_id, format text not null check (format in ('jsonl','csv')), since timestamptz null, status text not null check (status in ('queued','running','completed','failed')), storage_key text null, download_expires_at timestamptz null, error_code text null check (error_code in ('storage_unavailable','source_read_failed','timeout','cancelled')), error_message text null, audit fields)`; `purge_requests(id, tenant_id, scope_kind text not null check (scope_kind in ('tenant','workspace','sheet','user')), scope_id uuid null, older_than timestamptz not null, status text not null check (status in ('proposed','confirmed','running','completed','failed','expired')), confirmation_code_hash bytea not null, proposed_by uuid not null references users(id) on delete restrict, confirmed_by uuid null references users(id) on delete restrict, confirmed_at timestamptz null, purged_count bigint not null default 0, skipped_held_count bigint not null default 0, error_code text null check (error_code in ('storage_unavailable','delete_failed','timeout','cancelled')), error_message text null, audit fields)`; `access_reviews(id, tenant_id, scope_kind text not null check (scope_kind in ('tenant','workspace')), scope_id uuid null, as_of timestamptz not null, principal_count int not null default 0, flagged_count int not null default 0, storage_key_json text null, storage_key_csv text null, audit fields)`; and `purge_batches(purge_id uuid not null references purge_requests(id) on delete cascade, batch_no int not null, tenant_id, kind text not null check (kind in ('rows','sheets','documents','files','comments','workflow_runs','audit_events','notifications')), deleted_count int not null, completed_at timestamptz not null, primary key (purge_id, batch_no))`.
- Normalized sets (decision section 2, no array columns): `tenant_export_kinds(export_id uuid not null references tenant_exports(id) on delete cascade, tenant_id, kind text not null check (kind in ('rows','sheets','documents','files','comments','workflow_runs','audit_events','notifications')), status text not null default 'pending' check (status in ('pending','running','completed','failed')), rows_written bigint not null default 0, bytes_written bigint not null default 0, checksum_sha256 bytea null, completed_at timestamptz null, primary key (export_id, kind))` replaces both `tenant_exports.include text[]` and `tenant_exports.progress jsonb`; `purge_request_kinds(purge_id uuid not null references purge_requests(id) on delete cascade, tenant_id, kind text not null check (kind in ('rows','sheets','documents','files','comments','workflow_runs','audit_events','notifications')), candidate_count bigint not null default 0, held_count bigint not null default 0, purged_count bigint not null default 0, skipped_held_count bigint not null default 0, completed_at timestamptz null, primary key (purge_id, kind))` replaces both `purge_requests.kinds text[]` and `purge_requests.preview jsonb`; `access_review_principals(review_id uuid not null references access_reviews(id) on delete cascade, tenant_id, principal_id uuid not null, principal_kind text not null check (principal_kind in ('user','guest')), display_name text not null, role_count int not null default 0, group_count int not null default 0, share_count int not null default 0, link_count int not null default 0, token_count int not null default 0, last_login_at timestamptz null, last_activity_at timestamptz null, flag_reason text not null default 'none' check (flag_reason in ('none','inactive_90d','stale_guest_link')), primary key (review_id, principal_id))`; `access_review_decisions(review_id uuid not null, principal_id uuid not null, tenant_id, decision text not null check (decision in ('keep','revoke')), note text null, decided_by uuid not null references users(id) on delete restrict, decided_at timestamptz not null, outcome text not null default 'pending' check (outcome in ('pending','applied','partial','failed')), primary key (review_id, principal_id), foreign key (review_id, principal_id) references access_review_principals(review_id, principal_id) on delete cascade)` replaces `access_reviews.decisions jsonb`. The API is unchanged: `CreateTenantExportRequest.include`, `ProposePurgeRequest.kinds`, `TenantExportResponse.progress`, `PurgePreviewResponse.preview`, and the review decision list keep their JSON array and object shapes; `TenantExportRepository`, `PurgeRequestRepository`, and `AccessReviewRepository` fan them out to rows on write (`insert ... on conflict (…) do update`) and reassemble them on read inside the request's `UnitOfWork`.
- `jsonb` audit: no `jsonb` column remains in this module. `tenant_exports.progress` and `purge_requests.preview` were read by known key (per-kind progress bars, resume-from-last-completed-kind, preview counts) and are now rows; `access_reviews.decisions` was filtered and counted (`decided_count`, bulk revoke of flagged guests) and is now `access_review_decisions`; `tenant_exports.error` and `purge_requests.error` carried a fixed `{code, message}` pair that error mapping branches on, so they became the typed `error_code`/`error_message` columns with a closed `check`. The only free-form artifacts in the feature — the export ZIP with its `manifest.json` and the access-review `report.json`/`report.csv` renderings — stay object-storage blobs referenced by `storage_key`, `storage_key_json`, and `storage_key_csv`; the database never parses them.
- Invariants: partial unique index `tenant_exports(tenant_id) where status in ('queued','running')`; check `purge_after_days is null or purge_after_days >= soft_delete_days`; check `kind <> 'audit_events' or purge_after_days is null or purge_after_days >= 365`; a `tenant_exports` row must have at least one `tenant_export_kinds` row and a `purge_requests` row at least one `purge_request_kinds` row, both inserted in the same `UnitOfWork` and asserted by `TenantExportRepository::insert_export_with_kinds` and `PurgeRequestRepository::insert_proposal_with_preview`; the composite primary keys on `tenant_export_kinds`, `purge_request_kinds`, and `access_review_decisions` make a repeated kind or a duplicate decision impossible where the array form allowed it; `access_reviews.flagged_count` equals the count of `access_review_principals` with `flag_reason <> 'none'` and is rebuilt from those rows by `insert_review_with_principals`; `purge_requests.purged_count` and `skipped_held_count` equal the sums over `purge_request_kinds` and are recomputed by `finish_purge_with_counts`; `purge_requests.status` transitions are enforced in service code and checked by a trigger that rejects `completed` without `confirmed_at`.
- Indexes: `legal_holds(tenant_id, scope_kind, scope_id) where released_at is null`, `purge_requests(tenant_id, status, created_at desc)`, `access_reviews(tenant_id, scope_kind, scope_id, created_at desc)`, `tenant_exports(tenant_id, created_at desc)`, `tenant_export_kinds(export_id, status)` for claiming the next pending kind on resume, `purge_request_kinds(purge_id)` and `purge_request_kinds(tenant_id, kind)` for the per-kind candidate and held rollups, `purge_batches(purge_id, kind, batch_no desc)` for the resume checkpoint, `access_review_principals(review_id, flag_reason, principal_kind)` for the flagged-rows-first detail table and the bulk guest revoke, `access_review_decisions(review_id, outcome)` for decision progress, and `access_review_decisions(decided_by)` for the reviewer audit.
- Audit events: `retention-policy.update`, `legal-hold.apply`, `legal-hold.release`, `tenant-export.request`, `tenant-export.download`, `purge.propose`, `purge.confirm`, `purge.executed`, `access-review.generate`, `access-review.decide`.
- Retention/deletion: compliance tables are never purged by purge requests; `tenant_exports` blobs expire after 7 days by object-storage lifecycle; rollback drops the ten tables children before parents (`access_review_decisions`, `access_review_principals`, `purge_batches`, `purge_request_kinds`, `tenant_export_kinds`, then `access_reviews`, `purge_requests`, `tenant_exports`, `legal_holds`, `retention_policies`) and the trigger.

### React/TypeScript

- Routes: `/admin/compliance/retention`, `/admin/compliance/holds`, `/admin/compliance/exports`, `/admin/compliance/purges`, `/admin/compliance/access-reviews` in `apps/web/src/features/compliance/`; components `CompliancePage`, `RetentionTable`, `LegalHoldTable`, `NewHoldDialog`, `ExportPanel`, `ExportProgress`, `PurgeWizard`, `PurgePreview`, `PurgeConfirmDialog`, `AccessReviewList`, `AccessReviewDetail`, `DecisionTable`.
- State: TanStack Query keys `['retention-policies']`, `['legal-holds']`, `['tenant-export', id]` (polls every 5 s while running), `['purge', id]`, `['access-reviews', cursor]`, `['access-review', id]`.
- API client: generated `ComplianceApi` with `listRetentionPolicies`, `putRetentionPolicy`, `createLegalHold`, `releaseLegalHold`, `requestTenantExport`, `getTenantExport`, `proposePurge`, `confirmPurge`, `listAccessReviews`, `generateAccessReview`.
- Telemetry: `retention_policy_saved`, `legal_hold_applied`, `tenant_export_requested`, `purge_proposed`, `purge_confirmed`, `access_review_generated` with `tenant_id` and kind or scope.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F027-01 through FR-F027-14 in `testing/features/F027/requirements/cases.md`
- [ ] Failure/edge-case tests: purge intersecting a hold, expired proposal, wrong confirmation code, same-actor confirm under two-person policy, second concurrent export, worker restart mid-export, audit_events policy below 365
- [ ] Permission-negative and tenant-isolation tests: tenant-admin without compliance-admin gets `denied`, foreign-tenant IDs return `not_found`, download URL from another tenant rejected
- [ ] Rust unit tests: `crates/domain/src/compliance/` hold scope matching, retention day validation, purge state machine, redaction of secrets in export, and progress/preview/decision reassembly from child rows; `cargo xtask check-persistence` proves no SQL outside `crates/persistence/src/compliance/`
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: one running export, policy checks including the `audit_events` 365-day floor, purge trigger, duplicate `tenant_export_kinds` kind rejected, duplicate `purge_request_kinds` kind rejected, duplicate `access_review_decisions` principal rejected, a decision for a principal absent from `access_review_principals` rejected, cascade of child rows when a parent is deleted, rollback ordering
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
- Migration adds `retention_policies`, `legal_holds`, `tenant_exports`, `tenant_export_kinds`, `purge_requests`, `purge_request_kinds`, `purge_batches`, `access_reviews`, `access_review_principals`, and `access_review_decisions`; rollback drops them children first. Feature is off by default behind `F027_FEATURE`.
