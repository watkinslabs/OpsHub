# F073 api cases

File: `testing/features/F073/api/{announcement_tests.rs,targeting_tests.rs,budget_tests.rs,hashing_tests.rs,markdown_tests.rs,help_tests.rs,bundle_tests.rs,negative_tests.rs}`. Flag `F073_FEATURE`.

- `list_excludes_dismissed_and_expired` — FR-F073-01: an announcement dismissed by the caller and one past `expires_at` are both absent; `include_dismissed=true` returns the first with its dismissal date.
- `list_orders_newest_first_and_pages` — FR-F073-01, NFR-F073-01: 60 announcements page at 20 by cursor in descending `published_at`; `limit=100` is clamped to 50.
- `platform_operator_publishes_platform_scope` — FR-F073-02: 201 with `state: published`, `audience_size` and `content_hash`; the row has `tenant_id is null`.
- `tenant_admin_cannot_publish_platform_scope` — FR-F073-02: a `tenant-admin` posting `scope: "platform"` → 403 `denied`, nothing written.
- `platform_operator_cannot_publish_tenant_scope` — FR-F073-03: that principal has no tenant, so `scope: "tenant"` → 400 `invalid`.
- `tenant_scope_takes_tenant_from_session` — FR-F073-03: a body naming another tenant id is ignored for `announcements.tenant_id` and the row belongs to the caller.
- `foreign_tenant_target_denied` — FR-F073-03: a `tenant` target for another tenant → 403 with `field_errors.targets` set to the foreign-tenant reason.
- `targets_and_across_kinds_or_within_kind` — FR-F073-04: a `plan` kind holding both `team` and `enterprise` plus `role: tenant-admin` reaches a team admin and an enterprise admin, not an enterprise member.
- `free_tenant_never_sees_enterprise_target` — FR-F073-04: a `plan: enterprise` announcement is absent for every user of a `free` tenant, including its admin.
- `entitlement_target_matches_trial_state` — FR-F073-04: an `entitlement: workapps` target matches a tenant holding it in `trial`, not one holding it in `none`.
- `empty_target_set_reaches_everyone` — FR-F073-04: no target rows → every user in scope receives it.
- `publish_snapshots_audience_size_and_emits_event` — FR-F073-05: `announcement.published.v1` carries `audience_size`; adding 10 users afterwards leaves the stored value unchanged.
- `dismiss_is_idempotent_and_permanent` — FR-F073-06: two dismissals → one row, both 204; `announcement.dismissed.v1` contains no user identifier; the item never returns to the default list.
- `dismissal_survives_retention_sweep` — FR-F073-06, FR-F073-14: the 90-day sweep clears interruption rows and leaves every dismissal row intact.
- `editorial_edit_within_token_threshold_accepted` — FR-F073-07: a typo fix under 5% of the token count returns 200 with a new `version` and the same `content_hash` inputs for severity and targets.
- `material_edit_rejected_with_conflict` — FR-F073-07: changing `severity`, a target row or `learn_more_article_slug` → 409 `conflict` with the material revision field error.
- `supersede_keeps_original_dismissed` — FR-F073-07: publishing with `supersedes_id` sets the original to `superseded`; a user who dismissed it sees only the replacement, exactly once.
- `passive_severities_never_interrupt` — FR-F073-08: `info` and `change` return `interrupting: false` regardless of budget.
- `interruption_budget_degrades_to_passive` — FR-F073-09: with one interruption 4 hours old the next `action_required` returns `interrupting: false`; after 24 hours it returns true and writes the ledger row.
- `weekly_interruption_cap_holds` — FR-F073-09: three interruptions inside 7 days suppress the fourth even when the daily window is clear.
- `content_hash_stable_across_target_order` — NFR-F073-05: the same targets submitted in a different order produce the same `content_hash`.
- `announcement_body_drops_raw_html_node` — FR-F073-13: every string in the injection corpus renders as text; the `SafeDoc` output contains no anchor with a non-`https:` scheme.
- `help_index_filters_by_context_key` — FR-F073-10: `context=sheet.grid` returns its three mapped articles in `position` order with `matched: true`.
- `unknown_context_returns_full_index_unmatched` — FR-F073-10: an unmapped key returns every article with `matched: false` and status 200.
- `article_returns_highest_version` — FR-F073-11: with versions 1 and 2 present the read returns version 2 and its `updated_at`.
- `article_missing_translation_falls_back_to_default_locale` — FR-F073-11: a `de-DE` caller on an English-only article gets the English body with `translation_fallback: true` and the fallback counter increments.
- `withdrawn_slug_returns_not_found` — FR-F073-12: a slug removed by a later bundle → 404 `not_found`.
- `etag_matching_request_returns_304` — FR-F073-12, NFR-F073-01: `If-None-Match` on the current slug, version and locale → 304 with no body.
- `signed_bundle_imports_articles_and_contexts` — FR-F073-11, NFR-F073-05: the signed fixture writes eight articles, their versions, translations and six context rows in one transaction.
- `repeated_bundle_id_is_noop` — NFR-F073-04: re-running the same `bundle_id` writes nothing and leaves `current_version` unchanged.
- `unsigned_bundle_leaves_previous_version_serving` — NFR-F073-05: a broken signature writes nothing, maps to `503 unavailable`, and the previous article version still reads.
- `member_cannot_publish` — FR-F073-15: an ordinary member posting an announcement → 403 `denied`.
- `foreign_announcement_not_found` — FR-F073-15: tenant B's admin gets 404 on `PATCH` and on dismiss of a tenant A announcement.
- `scoped_actor_may_read_but_not_publish` — FR-F073-15: a token without the announcement scope lists announcements and is denied every mutation.
- `mutations_require_idempotency_key_and_if_match` — FR-F073-15: publish without `Idempotency-Key` and `PATCH` without `If-Match` are both rejected.
- `no_reading_behaviour_rows_written` — FR-F073-14: after a full list, open and article read, the only per-user rows are one dismissal and one interruption ledger entry.

Evidence: JUnit output and event-bus captures under `testing/evidence/F073/api/`.
