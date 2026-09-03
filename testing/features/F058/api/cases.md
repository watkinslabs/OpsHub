# F058 api cases

File: `testing/features/F058/api/{device_tests.rs,sync_tests.rs,deeplink_tests.rs,concurrency_tests.rs}`. Flag `F058_FEATURE`.

- `manifest_is_tenant_branded` — FR-F058-01: `GET /manifest.webmanifest` returns tenant name, 192/512 icons, `start_url: /m/home`, `display: standalone`.
- `device_register_bound_to_session` — FR-F058-02: POST `/api/v1/mobile/devices` → 201 with `session_id` of the caller; `mobile-device.registered.v1` published.
- `device_revoke_other_user_not_found` — FR-F058-02: user B deletes user A's device → 404; own device → 204 and push subscription removed.
- `device_cross_tenant_not_found` — NFR-F058-02: tenant B device id from tenant A → 404.
- `device_routes_flag_off_not_found` — FR-F058-14: flag off → 404 on sync and device routes.
- `sync_applies_ops_in_recorded_order` — FR-F058-04: 4 ops out of order in the array apply by `recorded_at`; versions returned.
- `sync_rejects_conflict_with_server_value` — FR-F058-05: base_version 5, server changed the same cell at 6 → `conflict`, `server_value`, `server_version 6`.
- `sync_untouched_cell_with_old_base_applies` — FR-F058-05: base_version 5, server changed a different cell → applied.
- `sync_rejects_denied_at_sync_time` — FR-F058-05, NFR-F058-02: editor downgraded to viewer → `denied`, no cell change.
- `sync_rejects_deleted_row_not_found` — FR-F058-05: row soft-deleted → `not_found`.
- `sync_replay_batch_returns_original` — FR-F058-06: same `batch_id` twice → same body, one set of writes.
- `sync_replay_op_id_in_new_batch_skipped` — FR-F058-06: applied `client_op_id` in a new batch → returned as applied with original version, no second write.
- `sync_batch_501_ops_invalid` — FR-F058-04: 501 ops → 400 `field_errors.ops = too_many`.
- `sync_revoked_device_denied` — FR-F058-02: revoked device → 403.
- `sync_writes_audit_per_op` — FR-F058-13: 3 applied ops → 3 audit events with device id and `recorded_at`; one `mobile-sync.applied.v1`.
- `pull_returns_changed_and_deleted_rows` — FR-F058-07: since cursor → 2 changed, 1 deleted marker, new cursor.
- `pull_expired_cursor_invalid` — FR-F058-07: 8-day-old cursor → 400 `field_errors.since = expired`.
- `pull_excludes_unsubscribed_sheets` — FR-F058-07: sheet never opened by the device absent from pull.
- `deep_link_resolves_row` — FR-F058-09: valid `row.<id>.<sig>` → 302 to `/m/rows/{id}`; audit `mobile.deeplink.resolve`.
- `deep_link_bad_signature_not_found` — FR-F058-09: tampered signature → 404.
- `deep_link_unreadable_row_not_found` — FR-F058-09: target outside ACL → not-found page.
- `deep_link_expired_not_found` — NFR-F058-02: link older than 30 days → 404.
- `same_batch_from_two_connections_applies_once` — NFR-F058-04: concurrent identical batch → one application, both responses equal.

Evidence: JUnit output and request logs under `testing/evidence/F058/api/`.
