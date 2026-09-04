---
id: S143
type: story
status: planned
parent_epic: E003
parent_feature: F072
depends_on: [F006, F017, F037]
owned_paths: [crates/domain/src/inbound-email/**, crates/persistence/src/inbound-email/**, services/api/src/inbound-email/**, services/worker/src/inbound-email/**, services/api/migrations/*_inbound-email_*.sql, testing/features/F072/**]
feature_flag: F072_FEATURE
branch: s143-inbound-addresses
started_at: null
finished_at: null
---

# S143 — Inbound addresses

## Identity

- Parent feature: `F072` Inbound email
- Owner: platform
- Branch: `s143-inbound-addresses`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 2.2, 3, 4, 7; `docs/capability-contracts.md` row F072; `docs/threat-model.md` sections 2.5, 3.1, 3.5

## Vertical slice

As a sheet editor, I want a per-sheet address that cannot be guessed, that I can rotate or revoke, and that refuses unauthenticated, unauthorised, oversized and looping mail without ever confirming it exists, so that putting a mailbox on the public internet does not put the sheet there with it.

This slice ends at a decided message: a verified delivery is recorded exactly once and carries a disposition of `accepted`, `rejected` or `quarantined`, with the parsed part inventory ready for S144 to apply.

## Requirements

- **SR-S143-01:** `POST /api/v1/inbound-addresses` mints a local part of 22 Crockford base32 characters over 110 CSPRNG bits, unique deployment-wide by `unique (domain, lower(local_part))` including revoked rows, never derived from sheet, tenant or counter, and caps a sheet at 5 `active` addresses through `InboundAddressRepository::count_active_for_sheet` inside the creating transaction; `mappings` and `allow_list` are written as `inbound_address_mappings` and `inbound_address_senders` rows in the same `UnitOfWork` (covers FR-F072-01, NFR-F072-02).
- **SR-S143-02:** `GET /api/v1/inbound-addresses` pages and filters by `sheet_id`, `status` and `sender_policy`, reassembles `mappings`, `allow_list` and the 30-day disposition counts from the child tables in one batched read per page, and omits the address itself from responses to actors without `sheet-editor` on the sheet (FR-F072-02, FR-F072-15).
- **SR-S143-03:** `DELETE /api/v1/inbound-addresses/{id}` revokes immediately and `POST` with `rotate_from_id` mints a successor while the predecessor keeps accepting for a 7-day grace window with each message tagged `rotated_source`; a revoked local part is never reissued and both paths write audit events (FR-F072-03).
- **SR-S143-04:** `POST /webhooks/inbound-email/{provider}` verifies an HMAC-SHA256 signature over timestamp and raw body with a previous-secret rotation window, constant-time comparison and 300-second skew before parsing anything, rejects a bad signature with `403 denied` and an audit event, and inserts one `inbound_messages` row keyed by `unique (provider, provider_message_id)` in the same transaction as its effect so a redelivery returns the first message id and creates nothing (FR-F072-04, NFR-F072-04).
- **SR-S143-05:** The `ingest` job evaluates SPF, DKIM, DMARC and header-From alignment first and records all four on the message: `pass`, or `none` with an aligned mechanism pass, continues; `fail` and unaligned `none` are `rejected` under `auth_policy = 'enforce'` and `quarantined` under `quarantine`; any `temperror` or `permerror` is `quarantined` under either policy. `sender_policy` then admits `anyone`, an active tenant user, or an `inbound_address_senders` match on address or domain-with-subdomains (FR-F072-05, FR-F072-06).
- **SR-S143-06:** Limits are enforced from `inbound_rate_windows` on one-hour tumbling windows — 60 messages per address per hour by default, 300 per address per day, 10 per sending address per inbound address per hour, 2,000 per tenant per day — and a message above `max_message_bytes` is refused before any part is parsed; loop defence refuses `Auto-Submitted`, `Precedence`, `List-Id`, `List-Unsubscribe`, `X-Loop`, a null return path, a self-addressed sender, more than 25 `Received` headers, and a reply token past 20 uses (FR-F072-08, FR-F072-09).
- **SR-S143-07:** Every refusal emits the identical `550 5.1.1 Recipient address rejected` bounce with no tenant, sheet or reason detail, behind a 250 ms constant-time floor shared with an unknown recipient, suppressed to one per sending address per inbound address per hour, and never sent to a null return path, a bounce, an auto-reply or a loop rejection; `inbound-message.received.v1` and `inbound-message.rejected.v1` are published without body text (FR-F072-07, NFR-F072-02).
- **SR-S143-08:** MIME parsing decodes RFC 2047 and RFC 2231 headers, honours a declared charset with a UTF-8 fallback, replaces invalid sequences with U+FFFD, walks `multipart/alternative`, `mixed`, `related` and `message/rfc822` to depth 5, and quarantines an unparseable structure with `rejection_reason = 'unparseable'` rather than dropping it (NFR-F072-05).
- **SR-S143-09:** The `retention` job deletes raw objects past `raw_expires_at` under the F027 `inbound_raw_message` policy, trims `inbound_rate_windows` older than 48 hours and retires expired reply tokens; a legal hold on the sheet suspends the sweep, and `from_address` reaches logs, traces and metrics only as its domain (FR-F072-16, NFR-F072-04).
- **SR-S143-10:** A viewer cannot create, rotate or revoke an address; a foreign-tenant address id returns `not_found` on read and delete; a local part minted for tenant A never resolves against tenant B; mutations require `Idempotency-Key` and `If-Match` on the address version (FR-F072-01, FR-F072-03).

## Surfaces

- Infrastructure/container: inbound domain with a wildcard MX record; deployment secrets `inbound-email/<provider>/webhook_secret` current and previous per provider; the F017 object store bucket prefix `inbound-raw/`
- Data access: `crates/persistence/src/inbound-email/{mod.rs, address_repository.rs, message_repository.rs, reply_token_repository.rs}` hold every SQL statement for this slice; `crates/domain/src/inbound-email`, the `services/api/src/inbound-email` handlers and the `services/worker/src/inbound-email` jobs depend on the repository traits and contain no `sqlx::query*` call or connection, and the webhook insert with its rate-window bump and the disposition write with its outbox event each commit in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/inbound-email/{mod.rs, address.rs, local_part.rs, authentication.rs, policy.rs, limits.rs, loop_guard.rs, mime.rs, errors.rs, service.rs, providers/{mod.rs, postmark.rs, sendgrid.rs, mailgun.rs}}`; `services/api/src/inbound-email/{mod.rs, routes.rs, handlers_address.rs, handlers_webhook.rs, dto.rs}`; `services/worker/src/inbound-email/{mod.rs, ingest.rs, bounce.rs, retention.rs}`
- Data/migration: `services/api/migrations/<ts>_inbound-email_create_tables.sql` and its `.down.sql`, creating the eight tables, checks and concurrent indexes from ticket section 4 as an expand-phase migration that touches no existing table
- React/UI: none in this slice; the address and log surfaces are S144
- Mocks/fixtures: `testing/fixtures/inbound_email.rs`; mock provider server in `testing/harness/providers/inbound-email/` signing and posting the `.eml` corpus in the three webhook formats; F037 transport stub recording bounces; fixed clock and fixed CSPRNG stream

## TDD harness

- Test path: `testing/features/F072/{api,database}/`
- Feature flag: `F072_FEATURE`
- Targeted command: `cargo xtask test-feature F072`
- Full command: `cargo xtask test-all`
- First failing tests: `local_part_is_unguessable_and_unique`, `sixth_active_address_conflicts`, `webhook_rejects_stale_signature`, `redelivered_message_creates_one_row`, `dmarc_fail_rejected_under_enforce`, `dkim_temperror_quarantined_under_enforce`, `sender_not_in_allow_list_rejected`, `hourly_limit_rejects_sixty_first`, `mailing_list_headers_rejected_without_bounce`, `refusals_are_byte_identical_and_time_bounded`, `viewer_cannot_revoke_address`

## Exit criteria

- [ ] Requirement tests SR-S143-01 through SR-S143-10 written first and failing
- [ ] Tasks T285 and T286 complete and wired through the `services/api` router and the `services/worker` registry
- [ ] Unit, API, database and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/inbound-email/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/inbound-addresses`, `/webhooks/inbound-email`); `services/worker/src/inbound-email/{ingest.rs, bounce.rs, retention.rs}` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F072 ticket
