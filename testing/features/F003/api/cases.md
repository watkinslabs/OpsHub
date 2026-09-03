# F003 api cases

File: `testing/features/F003/api/{engine_tests.rs,role_tests.rs,acl_tests.rs,check_tests.rs,audit_tests.rs,negative_matrix.rs,isolation_tests.rs}`. Flag `F003_FEATURE`.

- `deny_on_ancestor_beats_allow_on_resource` — FR-F003-05: folder deny, sheet allow → `denied`, reason `explicit_deny`, `matched_rule.scope` folder.
- `role_binding_at_ancestor_grants` — FR-F003-03, FR-F003-05: editor binding on workspace → `allowed` on sheet with reason `role_binding`.
- `guest_ignores_tenant_binding` — FR-F003-06: guest with tenant `Everyone` viewer binding → `denied` reason `no_match`; direct entry → `allowed`.
- `wildcard_permission_matches` — FR-F003-01: `*:read` grants `sheet:read` and `report:read`, not `sheet:edit`.
- `suspended_tenant_denies_everything` — FR-F003-05: suspended tenant → `denied` reason `suspended` before ACL lookup.
- `cache_invalidated_after_acl_update` — FR-F003-08: cached allow → ACL deny → next check denied within the same second.
- `role_create_custom_and_list` — FR-F003-02: `reviewer` created with 3 permissions; list pages by cursor.
- `role_unknown_permission_invalid` — FR-F003-02: `sheet:fly` → 400 `field_errors.permissions`.
- `role_system_slug_immutable` — FR-F003-01: PATCH slug on `viewer` → 400 `SystemRoleImmutable`.
- `role_member_create_denied` — NFR-F003-02: member POST → 403.
- `acl_effective_includes_inherited` — FR-F003-04: workspace entry appears on sheet with `inherited_from { kind: workspace }`; `caller_permissions` resolved.
- `acl_replace_emits_diff_event` — FR-F003-04: PUT adds QA/Reviewer and a guest deny → version 2, `acl.updated.v1` with `added` 2, `removed` 0.
- `acl_over_500_entries_invalid` — FR-F003-03: 501 entries → 400.
- `acl_duplicate_entry_invalid` — FR-F003-04: same principal and effect twice → 400.
- `acl_stale_version_conflicts` — FR-F003-12: stale `If-Match` → 409.
- `acl_commenter_replace_denied` — NFR-F003-02: commenter PUT → 403; version unchanged.
- `check_delegated_requires_admin` — FR-F003-07: member passing `principal` → 403; admin → 200 with decision.
- `require_maps_missing_read_to_not_found` — FR-F003-08: no `sheet:read` → 404; read without `sheet:edit` on PATCH → 403.
- `record_audit_writes_row_in_caller_transaction` — FR-F003-09: row visible only after commit; `audit.recorded.v1` enqueued.
- `audit_write_failure_aborts_mutation` — NFR-F003-04: forced insert failure → mutation rolled back, `audit_write_failures_total` +1.
- `audit_redacts_tagged_fields` — NFR-F003-02: `secret_enc` and third-party emails appear as `[redacted]` in `before`/`after`.
- `audit_list_filters_and_pages_newest_first` — FR-F003-11: 1,000 rows, `limit=200`, five pages; filters by `action_prefix=acl.` and time range.
- `audit_member_denied_owner_scoped` — FR-F003-11: member → 403; owner sees rows for own sheet only.
- `audit_idempotent_replay_returns_stored` — FR-F003-12: same key twice → one audit row.
- `auth_sink_writes_login_events` — FR-F003-09: F038 login through the database sink → `auth.login.success` row.
- `all_authz_routes_cross_tenant_not_found` — FR-F003-13: tenant B on all seven routes → 404; audit query → empty page.
- `all_authz_routes_role_negative` — NFR-F003-02: matrix runs every system role against every route.
- `f002_and_f038_routes_pass_matrix` — FR-F003-08: extractor swap proven on F002 and F038 route lists.
- `metrics_and_span_recorded` — NFR-F003-04: `authz_checks_total{decision="denied",reason="explicit_deny"}` +1; span has `resource_kind`.

Evidence: JUnit output and request logs under `testing/evidence/F003/api/`.
