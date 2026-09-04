---
id: T286
type: task
status: planned
parent_epic: E003
parent_feature: F072
parent_story: S143
depends_on: [S143, T285]
owned_paths: [crates/domain/src/inbound-email/**, crates/persistence/src/inbound-email/**, services/api/src/inbound-email/**, services/worker/src/inbound-email/**, testing/features/F072/api/**, testing/features/F072/performance/**]
feature_flag: F072_FEATURE
branch: t286-mail-ingestion
started_at: null
finished_at: null
---

# T286 — Mail ingestion

## Identity

- Parent story: `S143` Inbound addresses
- Owner: platform
- Branch: `t286-mail-ingestion`
- Decision references: `docs/architecture-decisions.md` sections 2.1, 3, 7, 9; `docs/capability-contracts.md` row F072; `docs/threat-model.md` sections 3.1, 3.5

## Objective

Implement the provider webhook and the ingestion gate: signature verification, replay-proof recording, sender authentication, sender policy, rate, size, chain and loop limits, MIME parsing, the uniform refusal bounce, and the retention sweep.

## Specification

- Owned paths: `crates/domain/src/inbound-email/{authentication.rs, limits.rs, loop_guard.rs, mime.rs, providers/{mod.rs, postmark.rs, sendgrid.rs, mailgun.rs}}`, `services/api/src/inbound-email/handlers_webhook.rs`, `services/worker/src/inbound-email/{mod.rs, ingest.rs, bounce.rs, retention.rs}`
- Contract/input: `POST /webhooks/inbound-email/{provider}` for `postmark`, `sendgrid` and `mailgun` with the provider's signature and timestamp headers and the raw body; deployment secrets `inbound-email/<provider>/webhook_secret` current and previous.
- Output/behavior: `InboundProvider::verify` computes HMAC-SHA256 over `timestamp || "\n" || raw_body`, compares in constant time against the current and previous secret, bounds skew at 300 seconds, and returns `403 denied` with audit `inbound-webhook.signature-rejected` before any parsing; a verified delivery resolves the recipient local part, inserts one `inbound_messages` row with `provider_snapshot`, `spf`, `dkim`, `dmarc` and `aligned` under `unique (provider, provider_message_id)` and bumps the `inbound_rate_windows` counters in the same `UnitOfWork`, publishes `inbound-message.received.v1`, and answers a redelivery with `200` and the first message id. `ingest.rs` then decides the disposition in order: `authentication.rs` maps `pass`, aligned `none`, `fail`, unaligned `none`, `temperror` and `permerror` onto `accepted`, `rejected` with `dmarc_fail` or `unauthenticated_sender`, or `quarantined`, honouring `auth_policy` and never skipping for `sender_policy = 'anyone'`; `policy.rs` admits `anyone`, an active tenant user, or an `inbound_address_senders` match on address or domain-with-subdomains; `limits.rs` enforces 60 per address per hour by default, 300 per address per day, 10 per sending address per inbound address per hour, 2,000 per tenant per day and `max_message_bytes` before parsing; `loop_guard.rs` refuses `Auto-Submitted` other than `no`, `Precedence` of `bulk`, `junk` or `list`, `List-Id`, `List-Unsubscribe`, a matching `X-Loop`, a null return path, a self-addressed sender, more than 25 `Received` headers and a token past 20 uses; `mime.rs` decodes RFC 2047 and RFC 2231 headers, honours the declared charset with a UTF-8 fallback, replaces invalid sequences with U+FFFD, walks `multipart/alternative`, `mixed`, `related` and `message/rfc822` to depth 5, and quarantines an unparseable tree as `unparseable`. Every refusal writes the disposition, publishes `inbound-message.rejected.v1`, and enqueues `bounce.rs`, which emits the identical `550 5.1.1 Recipient address rejected` through the F037 transport behind a 250 ms constant-time floor shared with an unknown recipient, at most one per sending address per inbound address per hour, and never to a null return path, a bounce, an auto-reply or a loop rejection. The raw message is written to `inbound-raw/<tenant_id>/<message_id>.eml` with `raw_expires_at`; `retention.rs` deletes expired objects under the F027 `inbound_raw_message` policy, trims rate windows older than 48 hours, retires expired tokens, and skips a sheet under legal hold. Metrics `inbound_messages_total{provider,disposition}`, `inbound_auth_results_total{mechanism,result}`, `inbound_bounces_suppressed_total` and `inbound_apply_duration_seconds`; spans carry `tenant_id`, `address_id`, `message_id` and `correlation_id`, and `from_address` is redacted to its domain.
- Data access: the webhook handler, the four gate modules, the provider adapters and the three jobs hold no SQL; they use `InboundAddressRepository::{find_active_by_local_part, match_allow_list, bump_window, count_in_window}`, `InboundMessageRepository::{insert_message_once, find_by_provider_message_id, record_disposition, list_raw_expiring_before, clear_raw_key}` and `InboundReplyTokenRepository::{claim_token, retire_token}` with no generic query escape hatch (decision section 2.1).
- Dependencies: T285 schema and repositories; F037 transport for bounces; F017 object store for the raw message; F004 job transport, dead-letter and secret manager; F027 retention policy key.
- Feature flag: `F072_FEATURE` gates the webhook route and the three jobs.

## TDD

- Failing test first: `testing/features/F072/api/webhook_tests.rs::webhook_rejects_stale_signature`, `::webhook_rejects_forged_signature_in_constant_time`, `::webhook_accepts_previous_secret_during_rotation`, `::redelivered_message_creates_one_row`, `::unknown_recipient_recorded_and_uniformly_refused`; `testing/features/F072/api/authentication_tests.rs::dmarc_fail_rejected_under_enforce`, `::dmarc_fail_quarantined_under_quarantine`, `::dmarc_none_with_aligned_spf_accepted`, `::dmarc_none_unaligned_rejected`, `::dkim_temperror_quarantined_under_enforce`, `::anyone_policy_still_requires_authentication`; `testing/features/F072/api/policy_tests.rs::sender_not_in_allow_list_rejected`, `::allow_list_domain_matches_subdomain`, `::tenant_members_policy_rejects_outsider`; `testing/features/F072/api/limit_tests.rs::hourly_limit_rejects_sixty_first`, `::per_sender_limit_rejects_eleventh`, `::oversize_message_rejected_before_parsing`, `::mailing_list_headers_rejected_without_bounce`, `::twenty_six_received_headers_rejected`, `::bounce_suppressed_after_first_per_hour`, `::refusals_are_byte_identical_and_time_bounded`; `testing/features/F072/api/mime_tests.rs::rfc2047_subject_decoded`, `::nested_forward_parsed_to_depth_five`, `::unparseable_mime_quarantined`
- Targeted command: `cargo xtask test-feature F072`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: mock provider server in `testing/harness/providers/inbound-email/` signing the `.eml` corpus in the three webhook formats with programmable authentication results; F037 transport stub recording bounces and suppression; F017 object-store stub; fixed clock and fixed secrets

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Webhook route and the `ingest`, `bounce` and `retention` jobs registered behind the flag; OpenAPI regenerated without drift
- [ ] Refusal corpus proves identical body and bounded timing across every refusal reason
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S143
- [ ] `finished_at` recorded
