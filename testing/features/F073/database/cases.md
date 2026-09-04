# F073 database cases

File: `testing/features/F073/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F073_FEATURE`.

- `announcements_tables_exist_with_constraints` — T289: the nine tables exist with tenant, version and audit columns where specified, and `announcements` carries the `scope`, `severity` and `state` check constraints.
- `platform_row_requires_null_tenant` — FR-F073-02: `scope = 'platform'` with a `tenant_id` violates the agreement check, and so does `scope = 'tenant'` without one.
- `action_required_requires_article_slug` — FR-F073-08: inserting `severity = 'action_required'` with a null `learn_more_article_slug` violates the check, so an interruption always has somewhere to go.
- `slug_unique_per_scope_ignoring_deleted` — FR-F073-02, FR-F073-03: a duplicate platform slug is rejected by the partial unique index; a duplicate tenant slug is rejected per tenant but allowed across tenants; a soft-deleted row does not block reuse.
- `dismissal_primary_key_blocks_duplicate` — FR-F073-06: a second `announcement_dismissals` row for the same announcement and user violates the primary key, which is what makes dismissal idempotent.
- `dismissals_have_no_delete_path` — FR-F073-06, FR-F073-14: the migration grants no delete on `announcement_dismissals` outside tenant purge, and the retention sweep excludes it.
- `interruption_ledger_one_row_per_user_and_announcement` — FR-F073-09: a second `announcement_interruptions` row for the same pair violates the primary key.
- `target_kind_check_rejects_unknown_kind` — FR-F073-04: a target kind outside `plan`, `entitlement`, `role` and `tenant` is rejected, and a duplicate `(announcement_id, kind, value)` violates the primary key.
- `translations_cascade_on_announcement_delete` — NFR-F073-05: deleting the announcement removes its translation and target rows; the dismissal rows go with it only on tenant purge.
- `default_locale_translation_required` — NFR-F073-05: publishing without a translation matching `announcements.default_locale` fails inside the publish transaction.
- `supersedes_must_match_scope_and_tenant` — FR-F073-07: `supersedes_id` pointing at an announcement of another scope or tenant is rejected.
- `help_translation_requires_existing_version` — FR-F073-11: a `help_article_translations` row whose `(article_id, version)` has no `help_article_versions` parent violates the composite foreign key.
- `help_version_monotonic_per_article` — FR-F073-11: version 2 cannot be imported before version 1 for the same article.
- `list_index_used_for_visible_query` — NFR-F073-01: `EXPLAIN` on the visible-announcement query uses the partial `(tenant_id, state, published_at desc)` index and the platform-slice index, not a sequential scan.
- `budget_index_used_for_rolling_window` — FR-F073-09: `EXPLAIN` on the 7-day interruption count uses `announcement_interruptions(user_id, shown_at desc)`.
- `no_array_or_jsonb_column_in_module` — NFR-F073-05: an information-schema assertion that no column in the nine tables has an array or `jsonb` type, pinning decision section 2.
- `rollback_drops_announcements_tables` — T289: `sqlx migrate revert` removes the nine tables and both partial unique indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F073/database/`.
