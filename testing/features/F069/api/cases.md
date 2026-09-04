# F069 api cases

File: `testing/features/F069/api/{home_tests.rs,onboarding_tests.rs,favorites_tests.rs,recents_tests.rs,prune_tests.rs,permission_tests.rs,isolation_tests.rs}`. Flag `F069_FEATURE`.

- `home_returns_five_sections_under_their_caps` — FR-F069-01: a member with 200 favourites and 100 recents gets 20 and 12 items with `truncated: true`; the three stub slots return their caps of 10.
- `home_takes_no_paging_parameters` — FR-F069-01: `cursor`, `limit`, `filter` and `sort` on the home route are rejected as `invalid`.
- `unregistered_slot_reports_unavailable` — FR-F069-02: with only the two built-in providers, `assigned`, `approvals` and `mentions` come back `unavailable` with no items.
- `slow_provider_degrades_only_its_section` — FR-F069-02: the approvals stub sleeps 400 ms; that section is `degraded` with a `correlation_id` and the other four still carry items.
- `failing_provider_degrades_with_correlation_id` — FR-F069-02: a stub returning an error degrades its section and leaves the status at `200`.
- `empty_registry_still_returns_two_hundred` — FR-F069-14: no providers at all yields five `unavailable` sections, never an `unavailable` status.
- `resolver_called_once_per_target_kind` — FR-F069-03: 62 items across six kinds issue six `resolve_readable` calls and no per-item statement.
- `unreadable_target_absent_without_marker` — FR-F069-03: an unreadable sheet is missing from the section and nothing in the body counts or marks it.
- `missing_resolver_drops_that_kind` — FR-F069-03: with no `document` resolver registered, document items are dropped and the rest of the response is intact.
- `new_user_gets_onboarding_suggestions` — FR-F069-12: a first-run member with two readable workspaces gets `state: new`, both workspaces and `create_sheet`.
- `viewer_without_workspace_gets_request_access` — FR-F069-12: a viewer who can read no workspace gets `request_access` only, and every section reports `no_access`.
- `empty_section_reports_its_reason` — FR-F069-12: an approvals stub returning nothing reports `all_clear`; an untouched recents section reports `none_yet`.
- `pin_requires_read_on_target` — FR-F069-05: pinning a sheet the caller cannot read returns `not_found`, and no row is written.
- `duplicate_pin_returns_conflict_with_existing_id` — FR-F069-05: a second pin of the same target returns `conflict` carrying the first favourite's id.
- `two_hundred_first_pin_rejected` — FR-F069-05: the 201st pin returns `conflict` with `field_errors.limit` and the count stays at 200.
- `pin_replay_is_idempotent` — FR-F069-05: the same `Idempotency-Key` replayed returns the stored response and publishes `favorite.added.v1` once.
- `unpin_of_other_users_favorite_is_not_found` — FR-F069-06: member B deleting member A's favourite id gets `not_found` and the row survives.
- `unpin_of_unavailable_target_succeeds` — FR-F069-06: a pin whose sheet was purged is still removable and publishes `favorite.removed.v1`.
- `filter_unavailable_returns_cached_label_without_path` — FR-F069-04: the unavailable list carries `label_cache`, `state: unavailable` and no `path` or reason.
- `visit_recorded_after_successful_read` — FR-F069-07: `GET /api/v1/sheets/{id}` returning `200` produces one `recent_items` row after the 5 s flush.
- `visit_not_recorded_for_non_2xx` — FR-F069-07: a `404` and a `403` on the observed routes record nothing.
- `repeat_visit_within_sixty_seconds_coalesces` — FR-F069-07: three reads inside 60 s leave `visit_count` at 1 and move `last_visited_at`.
- `full_channel_drops_and_counts` — FR-F069-07: 5,000 visits against a 4,096 channel drop the excess, increment `home_visits_dropped_total`, and never change a response status.
- `recents_trimmed_to_one_hundred` — FR-F069-08: a 101st distinct visit evicts the oldest row inside the same transaction as the upsert.
- `prune_deletes_recents_past_ninety_days` — FR-F069-10: rows at 91 days go, rows at 89 stay.
- `prune_removes_rows_for_purged_targets` — FR-F069-10: a purged sheet clears both its favourite and its recent rows in 500-id batches.
- `prune_is_idempotent_and_bounded` — FR-F069-10: a second run changes nothing and a 20,000-row backlog stops at 10,000.
- `unreadable_target_absent_from_home` — NFR-F069-02: an item the stub provider returns for an unreadable target never reaches the body.
- `deleted_and_denied_bodies_are_identical` — NFR-F069-02: soft-deleted, unshared, moved out of reach and never-existed produce byte-identical responses.
- `truncated_flag_does_not_leak_dropped_items` — NFR-F069-02: `truncated` reflects the readable set, not the candidate set.
- `pin_of_unreadable_target_returns_not_found_not_denied` — FR-F069-14: the pin route cannot be used to probe existence.
- `revoking_access_takes_effect_on_next_request` — FR-F069-09: an ACL replace removing read makes the item vanish from all three routes on the very next call.
- `tenant_admin_sees_only_own_favorites` — FR-F069-11: a `tenant-admin` reading `GET /api/v1/favorites` sees their own rows and none of another member's.
- `tenant_admin_sees_only_own_recents` — FR-F069-11: the same for `GET /api/v1/recents`.
- `cross_tenant_favorite_delete_is_not_found` — NFR-F069-02: a tenant B principal deleting a tenant A favourite id gets `not_found`.
- `visit_by_one_user_never_appears_for_another` — FR-F069-11: member A's reads leave nothing in member B's recents.
- `favorite_mutations_rate_limited` — FR-F069-14: the 61st pin or unpin in a minute returns `rate_limited`.
- `home_span_carries_section_key` — NFR-F069-04: each provider's span carries `tenant_id`, `actor_id`, `correlation_id` and the section key, and the state metric is emitted per section.

Evidence: JUnit output and outbox dumps under `testing/evidence/F069/api/`.
