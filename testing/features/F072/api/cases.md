# F072 api cases

File: `testing/features/F072/api/{address_tests.rs,token_tests.rs,webhook_tests.rs,authentication_tests.rs,policy_tests.rs,limit_tests.rs,mime_tests.rs,apply_tests.rs,oracle_tests.rs}`. Flag `F072_FEATURE`.

- `local_part_is_unguessable_and_unique` — FR-F072-01: 10,000 minted local parts are 22 Crockford base32 characters, all distinct, and pass a chi-square uniformity check at 110 bits.
- `local_part_never_encodes_sheet_or_tenant` — NFR-F072-02: two addresses on the same sheet share no prefix, suffix or edit-distance neighbourhood, and neither contains a sheet, workspace or tenant substring.
- `sixth_active_address_conflicts` — FR-F072-01: a sixth `active` address on one sheet → 409 with `field_errors.sheet_id = "address_limit"`; allowed once one is revoked.
- `mapping_rejects_column_from_another_sheet` — FR-F072-01: a `column_id` outside the sheet → 400 `invalid` with `field_errors.mappings`.
- `allow_list_required_for_allow_list_policy` — FR-F072-06: `sender_policy = "allow_list"` with an empty list → 400 `invalid`.
- `rotation_sets_seven_day_grace_on_predecessor` — FR-F072-03: `rotate_from_id` → successor active, predecessor `rotation_grace_ends_at` at +7 days, its messages tagged `rotated_source`, refused on day 8.
- `revoked_local_part_is_never_reissued` — FR-F072-03: 10,000 mints after revocation never reproduce the revoked local part; the revoked row is retained.
- `address_hidden_from_actor_without_sheet_editor` — FR-F072-02: a commenter's list response omits the `address` field while keeping the id and counts.
- `viewer_cannot_revoke_address` — FR-F072-01: viewer POST and DELETE → 403 `denied`, address unchanged.
- `foreign_tenant_address_not_found` — FR-F072-15: tenant B address and message ids → 404 on the address, the delete and the log.
- `reply_token_stored_only_as_hash` — FR-F072-14: no response, log or column holds the token; `token_hash` is the SHA-256 of the minted value.
- `reply_token_retired_after_twenty_uses` — FR-F072-09: the 21st reply → `thread_cap`, token `retired_at` set.
- `reply_tokens_revoked_with_row` — FR-F072-14: deleting the row cascades the token; a later reply → `invalid_thread_token`.
- `webhook_rejects_stale_signature` — FR-F072-04: a timestamp 301 s old → 403 `denied`, audit `inbound-webhook.signature-rejected`, no message row.
- `webhook_rejects_forged_signature_in_constant_time` — NFR-F072-02: a wrong HMAC → 403; comparison timing shows no prefix dependence over 1,000 samples.
- `webhook_accepts_previous_secret_during_rotation` — FR-F072-04: a body signed with the previous secret → 200; a third, retired secret → 403.
- `redelivered_message_creates_one_row` — FR-F072-04: the same `provider_message_id` twice → 200 with the first id, one message row, one sheet row, one `inbound-message.received.v1`.
- `unknown_recipient_recorded_and_uniformly_refused` — FR-F072-07: mail to a local part that never existed → recorded `rejected` with `unknown_recipient` and the standard bounce.
- `dmarc_fail_rejected_under_enforce` — FR-F072-05: `dmarc = fail` → `rejected`, `dmarc_fail`, `inbound-message.rejected.v1`, no row.
- `dmarc_fail_quarantined_under_quarantine` — FR-F072-05: same message on an address with `auth_policy = "quarantine"` → `quarantined`, no row, held.
- `dmarc_none_with_aligned_spf_accepted` — FR-F072-05: `dmarc = none`, `spf = pass`, envelope aligned → accepted with `auth_note = "dmarc_none_aligned"`.
- `dmarc_none_unaligned_rejected` — FR-F072-05: `dmarc = none` with no aligned mechanism → `unauthenticated_sender`.
- `dkim_temperror_quarantined_under_enforce` — FR-F072-05: any `temperror` or `permerror` → `quarantined` under both policies, never `rejected`.
- `anyone_policy_still_requires_authentication` — FR-F072-05: `sender_policy = "anyone"` with `dmarc = fail` → still rejected.
- `sender_not_in_allow_list_rejected` — FR-F072-06: an unlisted sender → `sender_not_permitted`.
- `allow_list_domain_matches_subdomain` — FR-F072-06: a listed `example.com` admits `mail.example.com` and refuses `example.com.attacker.test`.
- `tenant_members_policy_rejects_outsider` — FR-F072-06: a DMARC-passing outsider under `tenant_members` → `sender_not_permitted`.
- `hourly_limit_rejects_sixty_first` — FR-F072-08: 61st message in the window → `rate_limited`; the window rolls and the next hour accepts.
- `per_sender_limit_rejects_eleventh` — FR-F072-08: 11th message from one sender in an hour → `rate_limited` while other senders still pass.
- `oversize_message_rejected_before_parsing` — FR-F072-08: a 30 MB declared size → `too_large` with no MIME parse and no object written.
- `mailing_list_headers_rejected_without_bounce` — FR-F072-09: `List-Id`, `Precedence: bulk` and `Auto-Submitted: auto-replied` → `loop_suspected` and zero bounces emitted.
- `twenty_six_received_headers_rejected` — FR-F072-09: a 26-hop chain → `loop_suspected`; 25 hops pass.
- `bounce_suppressed_after_first_per_hour` — FR-F072-07: two refusals from one sender in an hour → one bounce, `inbound_bounces_suppressed_total` incremented.
- `refusals_are_byte_identical_and_time_bounded` — FR-F072-07: bodies and bounces across the five refusal reasons are byte-identical and elapsed times fall inside the measured floor.
- `rfc2047_subject_decoded` — NFR-F072-05: an encoded-word subject decodes to UTF-8 and truncates at 500 characters.
- `nested_forward_parsed_to_depth_five` — NFR-F072-05: a five-deep `message/rfc822` forward yields the innermost text; a sixth level is ignored.
- `unparseable_mime_quarantined` — NFR-F072-05: a truncated multipart boundary → `quarantined` with `unparseable`, never dropped.
- `html_only_body_is_reduced_to_text` — FR-F072-10: script, style, iframe, handlers and `javascript:` URLs are gone; no HTML is stored.
- `remote_image_is_never_fetched` — FR-F072-10: the fixture image host records zero requests during ingest and render.
- `body_beginning_with_equals_stays_literal` — FR-F072-10: a body starting `=SUM(A1:A9)` is stored as text and F035 never evaluates it.
- `apply_maps_subject_body_from_and_date` — FR-F072-11: mapped sources land in their columns and `from` resolves to the tenant user.
- `unresolved_sender_records_issue_and_row` — FR-F072-11: an unknown sender address → unresolved contact plus a `sender_unresolved` issue, row created.
- `missing_column_records_issue_not_drop` — FR-F072-13: a deleted mapped column → value in the primary column plus `column_missing`, row created.
- `deleted_sheet_refused_as_target_unavailable` — FR-F072-13: a deleted sheet → the only mapping-side refusal.
- `attachment_quarantined_by_scanner_does_not_block_row` — FR-F072-12: a detected part → `quarantined` attachment row, clean parts stored, row created.
- `eleventh_attachment_recorded_rejected_count` — FR-F072-12: eleven parts → ten stored, one `rejected_count`.
- `valid_reply_token_appends_comment` — FR-F072-14: a plus-token reply → F016 comment on the bound row, `inbound-message.applied.v1` with the comment id, no new row.
- `forged_in_reply_to_creates_new_row` — FR-F072-14: `In-Reply-To` naming another row without a token → a new row on the address's own sheet.
- `message_log_never_returns_body_text` — FR-F072-15: no log response contains body text, headers or the raw key.
- `raw_object_unreachable_and_swept` — FR-F072-16: no route serves `raw_object_key`; the retention job deletes it at `raw_expires_at` and a legal hold blocks the delete.
- `sender_address_redacted_to_domain_in_telemetry` — NFR-F072-02: no log line, span attribute or metric label carries a full sender address.
- `local_part_from_other_tenant_does_not_resolve` — NFR-F072-02: a tenant A local part posted with tenant B context → `unknown_recipient`.
- `ingest_resumes_after_worker_restart` — NFR-F072-04: a job killed mid-apply and re-run produces no duplicate row, attachment or event; a poison message dead-letters after 3 attempts.

Evidence: JUnit output and mock provider logs under `testing/evidence/F072/api/`.
