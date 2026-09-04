---
id: S126
type: story
status: planned
parent_epic: E006
parent_feature: F063
depends_on: [F026, F037, F038]
owned_paths: [crates/domain/src/entra/**, crates/persistence/src/entra/**, services/api/src/entra/**, services/worker/src/entra/**, apps/web/src/features/entra/**, testing/features/F063/**]
feature_flag: F063_FEATURE
branch: s126-graph-mail-and-group-sync
started_at: null
finished_at: null
---

# S126 — Graph mail and group sync

## Identity

- Parent feature: `F063` Microsoft Entra integration
- Owner: platform
- Branch: `s126-graph-mail-and-group-sync`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 5, 7; `docs/capability-contracts.md` row F063

## Vertical slice

As a tenant identity administrator, I want OpsHub mail to leave from our own Microsoft 365 mailbox and our OpsHub groups to follow the Entra groups we already maintain, so that notifications pass our SPF and DMARC policy and access stays in step with the directory — with SMTP still the default and fallback, and manual group members never touched.

## Requirements

- **SR-S126-01:** With the `mail` capability — resolved by `EntraConnectionRepository::list_capabilities` reading `entra_connection_capabilities` rows, not by testing membership of an array column — F037's channel registry gains a `graph` transport that sends through `POST /v1.0/users/{sender}/sendMail` as `sender_mailbox`, reusing F037's templates, retry schedule and delivery records rather than a second template system; SMTP stays the default and `entra.mail-sent.v1` carries only `message_id` and `recipient_domain` (covers FR-F063-08).
- **SR-S126-02:** A Graph send failure falls back to the tenant's SMTP transport when one is configured, and both attempts are recorded on the same F037 delivery record with their status codes; with no SMTP transport the delivery follows F037's normal retry and dead-letter path (covers FR-F063-08, NFR-F063-04).
- **SR-S126-03:** With the `group_sync` capability, `POST /api/v1/entra/sync-groups` and the nightly worker job read `GET /v1.0/groups` with delta tokens, resolve each `entra_group_map` row through its `target_group_id` foreign key to an F002 group or its `target_role_id` foreign key to an F003 role, exactly one of which is set, add and remove members through the F002 membership and F003 role-binding repositories, skip members flagged `source: manual`, and publish `entra.group-synced.v1` with added and removed counts; a mapping targeting another tenant's group is `404 not_found` (covers FR-F063-06).
- **SR-S126-04:** Sync is bounded and reversible: at most 500 mapped groups and 50,000 members per run, a run that would remove more than 20% of a group's members ends `status: needs_review` and changes nothing until an administrator confirms, and every add and removal writes an audit event naming the directory group as the reason (covers FR-F063-07).
- **SR-S126-05:** Every Graph call goes through the one typed client with a 10 s timeout, bounded exponential-backoff retries, `Retry-After` honoured on `429` and `503`, per-tenant concurrency 4, and a breaker that opens for 5 minutes after 5 consecutive failures; each call writes an `entra_mail_log` row with operation, status code and duration through `EntraMailLogRepository::append_graph_call` — the client itself holds no SQL — and never logs a token, mail body or recipient beyond its domain (covers FR-F063-09, NFR-F063-02).
- **SR-S126-06:** The sync job is idempotent per delta token, resumes after restart, dead-letters after 3 retries with the connection set to `error`, and emits `entra_graph_calls_total`, `entra_signins_total`, `entra_group_sync_members_total` and `entra_mail_total` with a tracing span carrying `tenant_id` and `correlation_id`; an expired delta token falls back to a full read without duplicating members (covers NFR-F063-04).
- **SR-S126-07:** A 500-group, 50,000-member delta sync finishes within 10 minutes under mocked Graph throttling and a Graph mail send is acknowledged to the F037 queue in under 3 s p95 (covers NFR-F063-01).
- **SR-S126-08:** `/admin/entra#groups` shows the mapping table, an `Add mapping` picker searching directory groups, and the last sync result with `Added 24, removed 2` or the `needs_review` banner; the table scrolls in its own container and status is text plus icon, never colour alone (covers FR-F063-12, NFR-F063-03).
- **SR-S126-09:** Group sync and Graph mail are inert without their capability: a connection with no `entra_connection_capabilities` row for `group_sync` rejects `POST /api/v1/entra/sync-groups` with `409 conflict` on `field_errors.capabilities`, a connection with no `mail` row leaves SMTP selected, and a member or non-`identity-admin` is `403 denied` on both (covers FR-F063-01, FR-F063-11, FR-F063-13).

## Surfaces

- Infrastructure/container: nightly worker schedule per connection, per-tenant Graph concurrency 4, breaker state held per connection; Graph host chosen from `cloud`
- Data access: `crates/persistence/src/entra/{group_map_repository.rs, mail_log_repository.rs, connection_repository.rs}` hold every SQL statement for this slice — `EntraGroupMapRepository` owns `entra_group_map` (`list_maps_for_connection`, `find_map_by_directory_group`, `upsert_map`, `record_sync_counts`), `EntraMailLogRepository` owns `entra_mail_log` (`append_graph_call`, `list_recent_calls_for_tenant`, `purge_calls_older_than`), `EntraConnectionRepository` supplies `list_capabilities` and `advance_delta_token`; `crates/domain/src/entra/*`, `services/worker/src/entra/*` and the `graph` transport take these traits and contain no `sqlx::query*` call, and one sync run's member changes, map counts and delta-token advance commit in a single `UnitOfWork` shared with the F002 membership and F003 role-binding repositories (decision section 2.1)
- Rust service/API: `crates/domain/src/entra/{group_sync.rs, mail.rs, graph.rs, breaker.rs}`; `services/api/src/entra/{handlers_groups.rs, dto.rs}`; `services/worker/src/entra/{mod.rs, group_sync.rs, transport.rs}` registering the `graph` transport into the F037 registry at startup
- Data/migration: `entra_group_map` unique on `(connection_id, directory_group_id)`, with `target_group_id references groups(id) on delete cascade` and `target_role_id references roles(id) on delete restrict` under the check that exactly one matches `target_kind`, indexed on `(connection_id)`, `(target_group_id)` and `(target_role_id)`; `entra_mail_log` with `(tenant_id, occurred_at desc)` and `(tenant_id, status_code)` indexes and the 90-day F027 sweep
- React/UI: `apps/web/src/features/entra/{GroupMapTable.tsx, GroupPickerDialog.tsx, SyncResultBanner.tsx}` with query keys `['entra-group-map']` and `['entra-directory-groups', search]`
- Mocks/fixtures: `testing/fixtures/entra.rs` seeds 500 directory groups and 50,000 members; mock Graph in `testing/harness/providers/entra/` serves groups delta and `sendMail` with programmable `429` and `503` and an expirable delta token; no real Microsoft endpoint is contacted

## TDD harness

- Test path: `testing/features/F063/{requirements,api,database,frontend,e2e,performance}/`
- Feature flag: `F063_FEATURE`
- Targeted command: `cargo xtask test-feature F063`
- Full command: `cargo xtask test-all`
- First failing tests: `graph_transport_registers_into_f037_registry`, `graph_failure_falls_back_to_smtp_and_records_both`, `sync_adds_and_removes_mapped_members`, `sync_skips_manual_source_members`, `sync_halts_needs_review_over_twenty_percent_removal`, `graph_client_honors_retry_after_on_429`, `breaker_opens_after_five_consecutive_failures`, `sync_without_group_sync_capability_conflicts`, `expired_delta_token_falls_back_to_full_read`, `group_map_rejects_both_or_neither_target_column`

## Exit criteria

- [ ] Requirement tests SR-S126-01 through SR-S126-09 written first and observed failing
- [ ] Tasks T251 and T252 complete and wired through the `services/worker` registry and the F037 channel registry
- [ ] Unit, API, database, React, E2E, permission-negative and performance tests pass in targeted and full modes
- [ ] No token, mail body or full recipient address appears in `entra_mail_log` or any log line
- [ ] Production call path named: `services/worker/src/entra/group_sync.rs` registered in `services/worker/src/registry.rs`; `services/worker/src/entra/transport.rs` registered into F037's channel registry; `services/api/src/entra/handlers_groups.rs` mounted at `POST /api/v1/entra/sync-groups`
- [ ] Handoff evidence recorded in the F063 ticket
