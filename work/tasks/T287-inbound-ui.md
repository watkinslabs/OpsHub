---
id: T287
type: task
status: planned
parent_epic: E003
parent_feature: F072
parent_story: S144
depends_on: [S144, T286]
owned_paths: [crates/domain/src/inbound-email/**, crates/persistence/src/inbound-email/**, services/api/src/inbound-email/**, apps/web/src/features/inbound-email/**, testing/features/F072/frontend/**, testing/features/F072/accessibility/**]
feature_flag: F072_FEATURE
branch: t287-inbound-ui
started_at: null
finished_at: null
---

# T287 — Inbound UI

## Identity

- Parent story: `S144` Message to row
- Owner: platform
- Branch: `t287-inbound-ui`
- Decision references: `docs/architecture-decisions.md` sections 2.1, 3, 5, 6; `docs/capability-contracts.md` row F072

## Objective

Turn an accepted message into a row or a comment and give the result a surface: sanitisation, column mapping with issues, attachments through F017, reply-token threading, the `GET /api/v1/inbound-messages` log route, and the settings and log screens.

## Specification

- Owned paths: `crates/domain/src/inbound-email/{sanitize.rs, apply.rs, threading.rs}`, `services/api/src/inbound-email/handlers_message.rs`, `apps/web/src/features/inbound-email/{InboundEmailPage.tsx, AddressCard.tsx, AddressDialog.tsx, SenderPolicyField.tsx, AllowListEditor.tsx, MappingEditor.tsx, LimitsField.tsx, RotateAddressDialog.tsx, MessageLogTable.tsx, MessageDetailDrawer.tsx, AuthResultChips.tsx, AttachmentList.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: a decided message from T286 with its parsed part inventory; list query `{ cursor?, limit?, address_id?, sheet_id?, disposition?, from?, received_after?, received_before? }`.
- Output/behavior: `sanitize.rs` prefers the `text/plain` part and otherwise reduces `text/html` through an allowlist dropping `script`, `style`, `iframe`, `object`, `embed`, `svg`, `link`, `meta`, every event-handler attribute and every `javascript:` or `data:` URL, storing text only, fetching nothing remote, capping the body at 262,144 bytes with a `body_truncated` issue, truncating the subject to 500 characters and stripping `\r`, `\n` and NUL from anything reused in a bounce or notification. `apply.rs` reads the `inbound_address_mappings` rows and writes one row through the F006 row path with formula interpretation off so a leading `=`, `+`, `-`, `@`, tab or carriage return stays literal; `from` resolves to the active tenant user holding the address or becomes an unresolved contact with a `sender_unresolved` issue; each attachment is streamed to `POST /api/v1/files/uploads` with `target_kind = 'row'` and recorded as one `inbound_message_attachments` row with disposition `stored`, `rejected_type`, `rejected_size`, `rejected_count` past ten parts or `quarantined`; any unsatisfiable mapping writes to the sheet's primary column and records an `inbound_message_issues` row instead of dropping the message, and only a deleted sheet or one with no writable column refuses, as `target_unavailable`. `threading.rs` mints the `Reply-To` plus-token for F037 row notifications, claims it in constant time, appends an F016 comment attributed to the token's recipient, and treats `In-Reply-To` and `References` as display metadata that never selects a row. Success publishes `inbound-message.applied.v1` with the row or comment id and notifies the address owner through F037 when issues exist. `handlers_message.rs` serves `GET /api/v1/inbound-messages` with cursor paging, `limit` 1–100, the filters above, the authentication results, disposition, rejection reason, row or comment id, attachments and issues, no body text, headers or raw message, and `404 not_found` for a cross-tenant address. The React feature mounts `/sheets/:sheetId/settings/inbound-email` and `/admin/inbound-email` from `apps/web/src/ui` only, with tokens as the sole source of visual values, and ships loading, empty, error with `correlation_id`, denied, stale, offline and success states; the surface follows `design/artboards/InboundEmail.dc.html`.
- Data access: `sanitize.rs`, `apply.rs`, `threading.rs`, the handler and the React feature hold no SQL; they use `InboundMessageRepository::{append_attachment, append_issue, record_disposition, list_messages}` and `InboundReplyTokenRepository::{mint_token, claim_token, retire_token, revoke_tokens_for_row}`, and the apply step commits the row write, attachment rows, issue rows, disposition and outbox event in one `UnitOfWork` (decision section 2.1).
- Dependencies: T286 decided messages; F006 and F008 row and cell writes; F007 column types; F016 comments; F017 uploads and scan states; F037 notifications; F062 component library and tokens.
- Feature flag: `F072_FEATURE` gates the log route and both web routes.

## TDD

- Failing test first: `testing/features/F072/api/apply_tests.rs::html_only_body_is_reduced_to_text`, `::remote_image_is_never_fetched`, `::body_beginning_with_equals_stays_literal`, `::apply_maps_subject_body_from_and_date`, `::unresolved_sender_records_issue_and_row`, `::missing_column_records_issue_not_drop`, `::deleted_sheet_refused_as_target_unavailable`, `::attachment_quarantined_by_scanner_does_not_block_row`, `::eleventh_attachment_recorded_rejected_count`, `::valid_reply_token_appends_comment`, `::forged_in_reply_to_creates_new_row`, `::message_log_never_returns_body_text`; `testing/features/F072/frontend/MessageLogTable.test.tsx::shows_accepted_rejected_and_quarantined_entries`, `::links_accepted_entry_to_its_row`; `testing/features/F072/frontend/AddressCard.test.tsx::copy_control_announces_success`; `testing/features/F072/frontend/MappingEditor.test.tsx::rejects_duplicate_source_and_column`
- Targeted command: `cargo xtask test-feature F072`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/inbound_email.rs` sheet `Vendor intake` with text, long-text, date, contact and file columns; F017 upload and scan stubs with clean, quarantined and rejected outcomes; MSW handlers for the address and message routes; fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Log route and both web routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Every surface state composed from F062 with tokens as the only visual values
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S144
- [ ] `finished_at` recorded
