# F047 requirements cases

Feature: MCP access server. Flag `F047_FEATURE`. Every case maps to a ticket requirement ID and runs against the in-process stub MCP client in `testing/harness/mcp/`.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F047-REQ-001` | FR-F047-01 | api | `initialize` negotiates `2025-06-18` and advertises resources/tools capabilities; unknown method → `-32601`; batch of 11 → `-32602`; bad JSON → `-32700` |
| `F047-REQ-002` | FR-F047-02 | api | bearer token with `mcp:access` yields `ActorContext`; missing scope, revoked token, or session cookie → `-32001` `denied` with `reason: invalid_token` |
| `F047-REQ-003` | FR-F047-03 | api | `resources/list` returns `opshub://<kind>/<id>` for the nine kinds, pages at 100 by signed cursor, and counts differ per actor after permission filtering |
| `F047-REQ-004` | FR-F047-04 | api | each adapter reads its canonical model; absent and invisible URIs both → `-32002` `not_found`; malformed URI → `-32602` |
| `F047-REQ-005` | FR-F047-05 | api | unreadable fields removed into `annotations.redactedFields`; secrets never serialized; 300 KB body truncated with `annotations.truncated` |
| `F047-REQ-006` | FR-F047-06 | api | `tools/list` serves the generated manifest, omits tools whose scope is absent, and a DTO change without a manifest rebuild fails `check-contracts` |
| `F047-REQ-007` | FR-F047-07 | api | `search_records` is ranked, permission-filtered, side-effect free, and stable within one second; `limit` 51 → `-32602` |
| `F047-REQ-008` | FR-F047-08 | api, e2e | first `update_record` call writes nothing, inserts a `pending` confirmation with the field diff, publishes `mcp.mutation-proposed.v1`, returns `confirmation_required` |
| `F047-REQ-009` | FR-F047-09 | api | approve by proposer or tenant-admin → `approved` and `mcp.mutation-confirmed.v1`; other member → `403`; expired or consumed → `409`; foreign tenant → `404` |
| `F047-REQ-010` | FR-F047-10 | api, e2e | retry with matching hash writes once under `mcp:<confirmation_id>` and marks `consumed`; second retry → `-32003`; changed arguments → `-32602` `arguments_changed` |
| `F047-REQ-011` | FR-F047-11 | api, database | one `mcp_audit` row per method call with decision, outcome, digest, and correlation id; `UPDATE` raises `audit_immutable` |
| `F047-REQ-012` | FR-F047-12 | api | `calls` 601st in a minute, `mutations` 61st, and `search` 121st each → `-32004` with `retry_after_seconds`; F028 application budget untouched |
| `F047-REQ-013` | FR-F047-13 | api | SSE emits `resources/updated` only for readable resources, `list_changed` on grant change, heartbeats at 15 s, resumes by `Last-Event-Id`, 4th stream rejected, closes `denied` on revocation |
| `F047-REQ-014` | FR-F047-14 | api | `GET /api/v1/mcp/audit` pages newest first with the ten filters; non-admin sees only own rows; cross-tenant `resource_uri` → empty page |
| `F047-REQ-015` | FR-F047-15 | frontend, e2e | `/admin/mcp` lists pending approvals with diff and countdown, approves through the confirm dialog, and shows both audit rows in the activity table |
| `F047-NFR-001` | NFR-F047-01 | performance | `initialize`/`tools/list` p95 < 100 ms; list of 100 < 300 ms; 100 KB read < 400 ms; tool overhead < 30 ms; 200 streams < 200 MB |
| `F047-NFR-002` | NFR-F047-02 | api | no cookie acceptance, no positive read without `authz::check`, arguments never interpolated into SQL or workflow expressions, no arguments or bodies in logs |
| `F047-NFR-003` | NFR-F047-03 | accessibility | axe serious/critical = 0 on `/admin/mcp` and the call drawer; diff is a labelled description list; countdown announced at 5 and 1 minute; dialog focus returns |
| `F047-NFR-004` | NFR-F047-04 | api, database | SSE resumes inside 60 s then degrades to `list_changed`; expiry enforced at read time with the sweeper stopped; the five metrics emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F047/`.
