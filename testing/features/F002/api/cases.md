# F002 api cases

File: `testing/features/F002/api/{tenant_tests.rs,user_tests.rs,group_tests.rs,isolation_tests.rs}`. Flag `F002_FEATURE`.

- `tenant_create_bootstraps_admin` — FR-F002-01: operator POST returns 201, `version: 1`, `admin_user_id`; the admin user row is `active`.
- `tenant_slug_taken_conflicts` — FR-F002-02: second tenant with slug `acme` → 409 `conflict`.
- `tenant_invalid_region_rejected` — FR-F002-02: `region: eu-west` → 400 with `field_errors.region`; `plan: gold` → `field_errors.plan`.
- `tenant_stale_version_conflicts` — FR-F002-03: `If-Match: 1` against version 2 → 409 with `current_version: 2`, no write.
- `tenant_suspend_blocks_api_routes` — FR-F002-04: after suspend, `POST /api/v1/groups` → 403 `reason: tenant_suspended`; `GET /api/v1/tenants/{id}` still 200.
- `tenant_idempotent_replay_returns_original` — FR-F002-11: same key twice → one row; different body → 409 `idempotency_mismatch`.
- `tenant_cross_tenant_not_found` — FR-F002-13: tenant B admin GET/PATCH/suspend tenant A → 404.
- `tenant_member_mutation_denied` — NFR-F002-02: member PATCH/suspend → 403 `denied`.
- `user_create_invited_unique_email` — FR-F002-05: `Ops@Acme.test` then `ops@acme.test` → 409 `field_errors.email: taken`.
- `user_list_pages_filters_sorts` — FR-F002-06: 450 users, `limit=200`, three pages; `status=active`, `email_prefix=fin`, `group_id`; `sort=email`.
- `user_illegal_transition_invalid` — FR-F002-07: `invited → suspended` → 400 `field_errors.status`.
- `user_self_edit_limited_to_display_name` — FR-F002-07: member PATCH own `external_id` → 403; own `display_name` → 200.
- `user_deactivate_revokes_sessions_and_memberships` — FR-F002-08: memberships deleted, `SessionRevoker` recorded with the user id, `user.deactivated.v1` enqueued.
- `user_deactivate_last_admin_rejected` — FR-F002-08: sole active tenant-admin → 400 `reason: last_admin`.
- `group_name_case_insensitive_conflicts` — FR-F002-09: `finance` then `Finance` → 409.
- `group_members_replace_atomic` — FR-F002-10: 2 kept + 4 new → 6 members; event has `added_user_ids` 4, `removed_user_ids` 1.
- `group_members_foreign_user_invalid` — FR-F002-10: tenant B user id → 400 `field_errors.user_ids` naming it; deactivated user likewise.
- `group_members_over_cap_invalid` — FR-F002-10: 5,001 ids → 400.
- `mutation_writes_audit_and_outbox` — FR-F002-12: each of the nine mutations → one audit row with diff and one outbox event.
- `all_routes_cross_tenant_not_found` — FR-F002-13: fixture helper replays all twelve routes under tenant B → 404.
- `all_mutations_member_denied` — NFR-F002-02: every mutation under member context → 403.
- `request_span_carries_ids_and_metric` — NFR-F002-04: span has `tenant_id`, `actor_id`, `correlation_id`; `tenant_mutations_total{action="user.create"}` +1.
- `email_redacted_in_logs` — NFR-F002-02: log capture shows `o***@acme.test`, never the full address.

Evidence: JUnit output and request logs under `testing/evidence/F002/api/`.
