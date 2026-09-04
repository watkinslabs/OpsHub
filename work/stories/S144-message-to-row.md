---
id: S144
type: story
status: planned
parent_epic: E003
parent_feature: F072
depends_on: [F006, F017, F037]
owned_paths: [crates/domain/src/inbound-email/**, crates/persistence/src/inbound-email/**, services/api/src/inbound-email/**, apps/web/src/features/inbound-email/**, testing/features/F072/**]
feature_flag: F072_FEATURE
branch: s144-message-to-row
started_at: null
finished_at: null
---

# S144 — Message to row

## Identity

- Parent feature: `F072` Inbound email
- Owner: platform
- Branch: `s144-message-to-row`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 5, 6, 9; `docs/capability-contracts.md` row F072; `docs/threat-model.md` sections 3.2, 3.4

## Vertical slice

As a sheet editor, I want an accepted message turned into a row whose subject, body, sender and attachments sit in the columns I chose — or into a comment on the row a notification was about — with every mapping problem recorded on the row instead of the message being dropped, and a log that shows me what arrived and what was refused.

This slice starts where S143 stops: a decided, parsed message. It owns sanitisation, mapping, attachments, threading, the log route and the screens.

## Requirements

- **SR-S144-01:** Body text is taken from the `text/plain` part, or reduced from `text/html` by an allowlist that drops `script`, `style`, `iframe`, `object`, `embed`, `svg`, `link`, `meta`, every event-handler attribute and every `javascript:` or `data:` URL; no HTML is stored or rendered, no remote image, stylesheet, link or `cid:` outside the message's own parts is fetched, and the stored text is capped at 262,144 bytes with a `body_truncated` issue (covers FR-F072-10).
- **SR-S144-02:** Cell values are written through the F008 path as literal text with formula interpretation off, so a leading `=`, `+`, `-`, `@`, tab or carriage return survives as text and is never parsed by F035; the subject is truncated to 500 characters and `\r`, `\n` and NUL are stripped from any value reused in a bounce or notification (FR-F072-10, NFR-F072-02).
- **SR-S144-03:** `apply_to_row` creates one row through the F006 row path from the `inbound_address_mappings` rows — `subject`, `body_text`, `received_at`, `message_id`, `to` and `from`, with `from` resolved to the active tenant user holding that address and otherwise stored as an unresolved contact with a `sender_unresolved` issue — and publishes `inbound-message.applied.v1` with the message, address and row ids (FR-F072-11).
- **SR-S144-04:** Attachments are streamed to `POST /api/v1/files/uploads` with `target_kind = 'row'` and recorded as one `inbound_message_attachments` row per part in `position` order with disposition `stored`, `rejected_type`, `rejected_size`, `rejected_count` past ten parts, or `quarantined` when the F017 scan quarantines it; a rejected part never blocks the row and a mapped file column holds only parts that reached `clean` (FR-F072-12).
- **SR-S144-05:** A mapping that cannot be satisfied writes the value into the sheet's primary column and records an `inbound_message_issues` row with a code, column and reason rather than dropping the message; the row is still created, the issues surface on the row and in the log, and F037 notifies the address owner. The only mapping-side refusal is a deleted sheet or one with no writable column, refused as `target_unavailable` (FR-F072-13).
- **SR-S144-06:** Reply tokens are 32 CSPRNG bytes carried as `<local_part>+<token>@<domain>` in the `Reply-To` of F037 row notifications, stored only as SHA-256 in `inbound_reply_tokens`, compared in constant time, bound to one tenant, address, row and recipient, expiring in 30 days, revoked with the row and retired after 20 uses; a valid token appends an F016 comment attributed to the recipient and publishes `inbound-message.applied.v1` with the comment id (FR-F072-14).
- **SR-S144-07:** `In-Reply-To` and `References` are recorded for display and never select a row: a forged `In-Reply-To` without a valid token creates a new row on the address's own sheet, and a token that does not match is refused as `invalid_thread_token` behind the uniform bounce (FR-F072-14, NFR-F072-02).
- **SR-S144-08:** `GET /api/v1/inbound-messages` pages and filters by `address_id`, `sheet_id`, `disposition`, `from`, `received_after` and `received_before`, returns the authentication results, disposition, rejection reason, row or comment id, attachments and issues, never returns body text, headers or the raw message, and returns `not_found` for a cross-tenant address (FR-F072-15).
- **SR-S144-09:** The sheet settings surface and the workspace index render the address with a copy control, the sender policy and allow-list editor, the mapping editor, the limits, rotation and revocation dialogs, and a message log whose accepted, rejected and quarantined entries each show what happened, with loading, empty, error, denied, stale and offline states composed from F062 (FR-F072-17, NFR-F072-03).
- **SR-S144-10:** The log and drawer are keyboard operable, disposition and authentication results carry text as well as colour, the copy control announces through a polite live region, the drawer traps and restores focus, and axe reports zero serious or critical violations on both routes (NFR-F072-03).

## Surfaces

- Infrastructure/container: no new infrastructure; consumes the F017 upload and scan API and the F037 notification transport configured in S143
- Data access: `crates/persistence/src/inbound-email/{message_repository.rs, reply_token_repository.rs}` supply `append_attachment`, `append_issue`, `record_disposition`, `list_messages`, `mint_token`, `claim_token`, `retire_token` and `revoke_tokens_for_row`; `apply.rs`, `threading.rs`, `sanitize.rs`, the message handler and the React feature contain no SQL, and the apply step commits the row write, attachment rows, issue rows, disposition and outbox event in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/inbound-email/{sanitize.rs, apply.rs, threading.rs}`; `services/api/src/inbound-email/{handlers_message.rs, dto.rs}` adding `GET /api/v1/inbound-messages`
- Data/migration: none; this slice writes to the tables the S143 expand migration creates
- React/UI: `apps/web/src/features/inbound-email/{InboundEmailPage.tsx, AddressCard.tsx, AddressDialog.tsx, SenderPolicyField.tsx, AllowListEditor.tsx, MappingEditor.tsx, LimitsField.tsx, RotateAddressDialog.tsx, MessageLogTable.tsx, MessageDetailDrawer.tsx, AuthResultChips.tsx, AttachmentList.tsx, api.ts, hooks.ts, routes.ts}` at `/sheets/:sheetId/settings/inbound-email` and `/admin/inbound-email`, drawn by `design/artboards/InboundEmail.dc.html`
- Mocks/fixtures: `testing/fixtures/inbound_email.rs` sheet `Vendor intake` with text, long-text, date, contact and file columns; the adversarial `.eml` corpus in `testing/harness/providers/inbound-email/`; F017 upload and scan stubs with clean, quarantined and rejected outcomes; MSW handlers for the two routes

## TDD harness

- Test path: `testing/features/F072/{api,frontend,e2e,accessibility}/`
- Feature flag: `F072_FEATURE`
- Targeted command: `cargo xtask test-feature F072`
- Full command: `cargo xtask test-all`
- First failing tests: `html_only_body_is_reduced_to_text`, `remote_image_is_never_fetched`, `body_beginning_with_equals_stays_literal`, `apply_maps_subject_body_from_and_date`, `unresolved_sender_records_issue_and_row`, `missing_column_records_issue_not_drop`, `attachment_quarantined_by_scanner_does_not_block_row`, `valid_reply_token_appends_comment`, `forged_in_reply_to_creates_new_row`, `message_log_never_returns_body_text`

## Exit criteria

- [ ] Requirement tests SR-S144-01 through SR-S144-10 written first and failing
- [ ] Tasks T287 and T288 complete and wired through the `services/api` router and the web route table
- [ ] Unit, API, React, E2E, permission-negative and accessibility tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/inbound-email/handlers_message.rs` mounted through `services/api/src/inbound-email/routes.rs` in `services/api/src/router.rs` (`/api/v1/inbound-messages`); `apps/web/src/features/inbound-email/routes.ts` registered in `apps/web/src/app/routes.tsx`
- [ ] `design/artboards/InboundEmail.dc.html` regenerates from `design/generator/inbound_email.py` and matches the shipped surface
- [ ] Handoff evidence recorded in the F072 ticket
