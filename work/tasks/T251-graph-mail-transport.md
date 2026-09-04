---
id: T251
type: task
status: planned
parent_epic: E006
parent_feature: F063
parent_story: S126
depends_on: [S126]
owned_paths: [crates/domain/src/entra/**, crates/persistence/src/entra/**, services/worker/src/entra/**, testing/features/F063/api/**, testing/features/F063/performance/**]
feature_flag: F063_FEATURE
branch: t251-graph-mail-transport
started_at: null
finished_at: null
---

# T251 — Graph mail transport

## Identity

- Parent story: `S126` Graph mail and group sync
- Owner: platform
- Branch: `t251-graph-mail-transport`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 5, 7; `docs/capability-contracts.md` row F063

## Objective

Register a `graph` delivery transport into F037's existing channel registry so a tenant with the `mail` capability sends notifications from its own Microsoft 365 mailbox, with SMTP remaining the default and the fallback, and every call logged by domain only.

## Specification

- Owned paths: `crates/domain/src/entra/{mail.rs, breaker.rs}`; `crates/persistence/src/entra/mail_log_repository.rs`; `services/worker/src/entra/{mod.rs, transport.rs}`
- Data access: `EntraMailLogRepository` owns `entra_mail_log` (`append_graph_call`, `list_recent_calls_for_tenant`, `purge_calls_older_than`) and is the only writer of that table; `mail.rs`, `breaker.rs` and `transport.rs` take it and `EntraConnectionRepository` as traits and contain no `sqlx::query*` call or pool handle, and the attempt row plus the F037 delivery update commit in one `UnitOfWork` (decision section 2.1).
- Contract/input: `send_graph_mail(connection, delivery)` takes an F037 rendered delivery — the same template output SMTP receives — and posts `POST /v1.0/users/{sender_mailbox}/sendMail` with `{ message: { subject, body: { contentType: "HTML", content }, toRecipients }, saveToSentItems: false }` through the shared `graph.rs` client.
- Output/behavior: at worker startup the transport registers into F037's channel registry for every connection whose `entra_connection_capabilities` rows include `mail`, read as one indexed join through `EntraConnectionRepository::list_capabilities` rather than a scan of an array column, exactly as F029 registers its own — no second template system, no second retry schedule, no second delivery record. Selection is per tenant and SMTP stays the default; a tenant without the capability keeps SMTP untouched. A Graph `4xx`/`5xx` or timeout falls back to the tenant's SMTP transport when one is configured and records both attempts on the same F037 delivery with their status codes; with no SMTP transport the delivery follows F037's retry and dead-letter path and the connection is set to `error` after 3 retries. Each attempt appends `entra_mail_log(connection_id, operation, status_code, duration_ms, recipient_domain, message_id, occurred_at)` through `EntraMailLogRepository::append_graph_call`, `operation` constrained to the closed set by check — recipient stored as its domain only, never the address, subject or body — and publishes `entra.mail-sent.v1` with `message_id` and `recipient_domain` only. Throttling is the shared client's: 10 s timeout, `Retry-After` on `429`/`503`, per-tenant concurrency 4, breaker open 5 minutes after 5 consecutive failures, with `entra_mail_total{result}` and `entra_graph_calls_total{operation,status}` emitted and a tracing span carrying `tenant_id` and `correlation_id`. Acknowledgement to the F037 queue is under 3 s p95.
- Dependencies: T249 connection, credential unsealing and `graph.rs`; F037 channel registry, templates, delivery records and SMTP transport; F004 job transport and metrics; F027 sweep for the 90-day `entra_mail_log` retention.
- Feature flag: `F063_FEATURE` gates registration; with the flag off the registry contains only F037's own transports.

## TDD

- Failing test first: `testing/features/F063/api/mail_tests.rs::graph_transport_registers_into_f037_registry`, `::graph_transport_absent_without_mail_capability`, `::smtp_remains_default_when_graph_not_selected`, `::send_uses_configured_sender_mailbox`, `::graph_failure_falls_back_to_smtp_and_records_both`, `::three_503s_then_smtp_delivery_succeeds`, `::no_smtp_configured_dead_letters_after_three_retries`, `::mail_log_records_domain_not_address`, `::mail_sent_event_carries_message_id_and_domain_only`, `::graph_mail_honors_retry_after_on_429`, `::breaker_open_skips_graph_and_uses_smtp`, `::templates_are_f037_templates_not_a_copy`, `::mail_capability_row_drives_registration`; `testing/features/F063/performance/mail_bench.rs::graph_mail_ack_p95_under_3s`, `::mail_log_index_used_for_tenant_recent_calls`
- Targeted command: `cargo xtask test-feature F063`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: mock Graph `sendMail` in `testing/harness/providers/entra/` with programmable `429`, `503` and `Retry-After`; in-memory F037 channel registry with an SMTP transport for tenant A and none for tenant B; `testing/fixtures/entra.rs` mail-capable connection with `sender_mailbox`, seeded through `EntraConnectionRepository` and read back through `EntraMailLogRepository` so no fixture or assertion issues SQL; fixed clock; no real Microsoft endpoint is contacted

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Transport registered in `services/worker/src/registry.rs` through the F037 channel registry behind the flag
- [ ] Redaction test proves no token, subject, body or full recipient address in `entra_mail_log` or any log line
- [ ] Fallback verified end to end with both attempts on one delivery record
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S126
- [ ] `finished_at` recorded
