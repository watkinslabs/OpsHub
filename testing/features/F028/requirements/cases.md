# F028 requirements cases

Feature: API/webhooks. Flag `F028_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F028-REQ-001` | FR-F028-01 | api | `openapi.json` lists every `/api/v1` route with DTO, `Error`, `Page` schemas; drift fails `check-contracts` |
| `F028-REQ-002` | FR-F028-02 | api, database | admin creates application → 201, `client_id`, version 1; duplicate name → 409 |
| `F028-REQ-003` | FR-F028-03 | api | suspend → bound tokens rejected within 5 s; delete → tokens revoked, `application.updated.v1` |
| `F028-REQ-004` | FR-F028-04 | api | bad cursor → 400 `field_errors.cursor`; unknown filter field → 400 `field_errors.filter` |
| `F028-REQ-005` | FR-F028-05 | api | `fields=name` → items carry `id`, `version`, `name` only; `include_total` → `total` |
| `F028-REQ-006` | FR-F028-06 | api | error body has `code`, `message`, `field_errors`, `correlation_id`; header echoed |
| `F028-REQ-007` | FR-F028-07 | api, performance | 60/min app → 120 succeed with decreasing remaining, 121st → 429 with `Retry-After` |
| `F028-REQ-008` | FR-F028-08 | api | create webhook → secret once, `webhook.updated.v1`; private URL → 400 |
| `F028-REQ-009` | FR-F028-09 | api, e2e | row update → delivery with delivery-id, event, timestamp, signature headers; receiver verifies |
| `F028-REQ-010` | FR-F028-10 | api | receiver 500 → attempts at 1m, 5m, 30m, 2h, 12h; `exhausted`; `webhook.failed.v1` once |
| `F028-REQ-011` | FR-F028-11 | api, e2e | 10 exhausted deliveries → `disabled`, `webhook.disabled.v1`; success resets counter |
| `F028-REQ-012` | FR-F028-12 | api, frontend | deliveries filter by status/event; replay → 202 new id; disabled → 409; 31 days → 409 |
| `F028-REQ-013` | FR-F028-13 | api | rotate secret → both signatures for 24 h; delete → pending cancelled |
| `F028-REQ-014` | FR-F028-14 | api | member → 403; foreign id → 404; payload excludes fields outside scopes |
| `F028-REQ-015` | FR-F028-15 | frontend, e2e | console shows apps, webhooks, delivery log, replay, re-enable, reference page |
| `F028-NFR-001` | NFR-F028-01 | performance | openapi < 50 ms; list overhead < 20 ms; dispatch p95 < 5 s at 1,000/min |
| `F028-NFR-002` | NFR-F028-02 | api | private ranges rejected at create and attempt; secrets encrypted and unlogged; `allowed_ips` enforced |
| `F028-NFR-003` | NFR-F028-03 | accessibility | axe serious = 0; status text plus icon; secret copy announced |
| `F028-NFR-004` | NFR-F028-04 | api, database | restart yields no duplicate delivery; malformed payload dead-lettered; metrics emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F028/`.
