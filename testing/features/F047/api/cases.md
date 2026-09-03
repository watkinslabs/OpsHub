# F047 api cases

File: `testing/features/F047/api/{jsonrpc_tests.rs,auth_tests.rs,manifest_tests.rs,rate_tests.rs,sse_tests.rs,uri_tests.rs,resource_tests.rs,redaction_tests.rs,read_tool_tests.rs,mutation_tests.rs,confirmation_route_tests.rs,audit_route_tests.rs}`. Driven by the in-process stub MCP client; no port is bound. Flag `F047_FEATURE`.

- `initialize_negotiates_protocol_and_capabilities` — FR-F047-01: response carries `protocolVersion 2025-06-18`, `serverInfo.name opshub`, `resources.subscribe`, `tools.listChanged`.
- `unsupported_protocol_version_returns_invalid` — FR-F047-01: `2024-11-05` → `-32602` with `data.supported: ["2025-06-18"]`.
- `unknown_method_returns_method_not_found` — FR-F047-01: `prompts/list` → `-32601`.
- `malformed_json_returns_parse_error` — FR-F047-01: truncated body → `-32700` with `id: null`.
- `batch_over_ten_rejected` — FR-F047-01: 11-element batch → `-32602`; a 10-element batch returns 10 responses with echoed ids.
- `domain_errors_map_to_jsonrpc_codes` — FR-F047-01: `invalid`, `denied`, `not_found`, `conflict`, `rate_limited`, `unavailable` map to `-32602`, `-32001`, `-32002`, `-32003`, `-32004`, `-32005`.
- `token_without_mcp_access_scope_denied` — FR-F047-02: token holding only `records:read` → `-32001` `denied`.
- `revoked_token_denied_with_invalid_token_reason` — FR-F047-02: token revoked mid-session → `-32001` with `reason: invalid_token` at HTTP 200.
- `session_cookie_is_not_accepted` — FR-F047-02, NFR-F047-02: `__Host-oh_session` alone → `-32001`.
- `tools_list_omits_tools_without_scope` — FR-F047-06: read-only token sees the five read tools and none of the five mutating tools.
- `manifest_hash_matches_checked_in_file` — FR-F047-06: built manifest equals `openapi/mcp-manifest.sha256`; a mutated DTO makes the assertion fail.
- `uri_round_trips_all_nine_kinds` — FR-F047-03: parse and render for workspace, document, folder, project, task, ticket, dashboard, workflow, audit.
- `unknown_kind_returns_invalid` — FR-F047-03: `opshub://sheet/<uuid>` → `-32602`.
- `foreign_tenant_id_returns_not_found` — NFR-F047-02: tenant B task URI read by a tenant A token → `-32002`.
- `resources_list_filtered_by_permission` — FR-F047-03: 40 seeded tasks, 12 readable → exactly 12 descriptors.
- `resources_list_pages_at_hundred_with_signed_cursor` — FR-F047-03: 250 resources → 3 pages; a tampered cursor → `-32602`.
- `resource_read_invisible_uri_is_not_found` — FR-F047-04: readable-by-nobody task and a random UUID both → `-32002` with identical bodies.
- `document_read_returns_current_revision_body` — FR-F047-04: `text/markdown` content with `revision` and `updated_at` from F045.
- `workflow_read_returns_definition_and_last_ten_runs` — FR-F047-04: 14 runs seeded → 10 newest returned.
- `every_resource_kind_has_a_permission_negative_case` — FR-F047-03: enumerating test over `ResourceKind` fails when an adapter lacks a denial case.
- `resource_read_strips_unreadable_fields` — FR-F047-05: `cost` column without `field:read` removed and named in `annotations.redactedFields`.
- `secret_fields_never_serialized` — FR-F047-05, NFR-F047-02: token hashes, webhook secrets, and OAuth ciphertext absent from every payload.
- `oversized_body_truncated_at_record_boundary` — FR-F047-05: 300 KB document → `annotations.truncated: true` with a usable `nextCursor`.
- `search_records_is_permission_filtered_and_ranked` — FR-F047-07: hits ordered by score with `uri`, `title`, `snippet`; invisible matches absent.
- `read_tools_write_nothing` — FR-F047-07: row versions and `mcp_confirmations` unchanged after all five read tools.
- `get_report_rejects_limit_over_fifty` — FR-F047-07: `limit: 51` → `-32602` with the field named.
- `mutating_tool_first_call_writes_nothing` — FR-F047-08: task `version` unchanged; one `pending` confirmation row exists.
- `proposal_returns_confirmation_required_with_diff` — FR-F047-08: `structuredContent.summary.changes` shows `due_date 2026-09-10 → 2026-09-24`.
- `proposal_publishes_mutation_proposed_event` — FR-F047-08: `mcp.mutation-proposed.v1` with the confirmation id as `aggregate_id`.
- `approve_requires_proposer_or_admin` — FR-F047-09: second member → `403 denied`; proposer and tenant-admin → `200`.
- `approve_expired_returns_conflict` — FR-F047-09: clock advanced 16 minutes → `409 conflict`.
- `approve_foreign_tenant_returns_not_found` — FR-F047-09: tenant B confirmation id → `404`.
- `approve_replays_idempotency_key` — FR-F047-09: same `Idempotency-Key` twice → one `mcp.mutation-confirmed.v1` and the stored response.
- `approved_confirmation_consumed_once` — FR-F047-10: retry writes the due date once, row becomes `consumed`, `mcp.tool-called.v1` published.
- `pending_confirmation_retry_returns_conflict` — FR-F047-10: retry before approval → `-32003`; second retry after consumption → `-32003`.
- `retry_with_changed_arguments_rejected` — FR-F047-10: `2026-10-01` against a hash for `2026-09-24` → `-32602` `arguments_changed`, nothing written.
- `calls_bucket_returns_rate_limited_with_retry_after` — FR-F047-12: 601st call in a minute → `-32004` with `retry_after_seconds`.
- `mutations_bucket_caps_at_sixty_per_minute` — FR-F047-12: 61st proposal → `-32004` while reads still succeed.
- `mutations_bucket_is_separate_from_application_budget` — FR-F047-12: exhausting the MCP bucket leaves an F028 application's `X-RateLimit-Remaining` untouched.
- `sse_stream_drops_events_after_grant_removed` — FR-F047-13: ACL revoked mid-stream → later updates for that resource are not emitted and the stream stays open.
- `sse_resumes_by_last_event_id_within_window` — NFR-F047-04: reconnect at 30 s replays missed events; at 90 s sends `list_changed` instead.
- `fourth_stream_per_token_rejected` — FR-F047-13: 4th concurrent stream → `denied`.
- `audit_row_per_method_call` — FR-F047-11: the conformance script produces one `mcp_audit` row per call with `decision` and `correlation_id`.
- `audit_list_scopes_non_admin_to_own_rows` — FR-F047-14: member sees only rows with their `actor_id`; tenant-admin sees all.
- `audit_list_filters_by_tool_and_decision` — FR-F047-14: `tool=update_record&decision=confirmation_required` returns exactly the proposal rows.
- `expiry_enforced_at_read_time_with_sweeper_stopped` — NFR-F047-04: sweeper disabled, clock +16 min → retry still returns `-32003`.

Evidence: JUnit output and recorded stub-client frames under `testing/evidence/F047/api/`.
