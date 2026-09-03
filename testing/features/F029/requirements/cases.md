# F029 requirements cases

Feature: Microsoft/Google/Slack. Flag `F029_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F029-REQ-001` | FR-F029-01 | api | providers list three entries with capabilities and scopes; missing credentials → `enabled: false` |
| `F029-REQ-002` | FR-F029-02 | api | start connection → 202, `authorize_url` with S256 challenge and 10-minute state; disabled provider → 400 |
| `F029-REQ-003` | FR-F029-03 | api, e2e | callback → tokens sealed, scopes recorded, `active`; narrowed scopes → `limited`; reused state → 400 |
| `F029-REQ-004` | FR-F029-04 | api, database | ciphertext and `key_id` stored; plaintext absent from responses, logs, audit, export |
| `F029-REQ-005` | FR-F029-05 | api | refresh 5 min before expiry; three failures → `needs_reauth`, owner notified, syncs paused |
| `F029-REQ-006` | FR-F029-06 | api, database | DELETE → provider revoke called, token row gone, `revoked`, `integration.revoked.v1` |
| `F029-REQ-007` | FR-F029-07 | api | list pages by cursor and filters by `provider` and `status` |
| `F029-REQ-008` | FR-F029-08 | api | notify channel renders Adaptive Card, Chat card, Block Kit for five kinds with deep links |
| `F029-REQ-009` | FR-F029-09 | api, e2e | notify-test → `delivered: true`, message id, `integration.notified.v1`; 11th in an hour → 429 |
| `F029-REQ-010` | FR-F029-10 | api, performance | binding pushes row dates and pulls provider changes using delta and sync tokens |
| `F029-REQ-011` | FR-F029-11 | api, frontend | both sides changed → policy decides; conflict event with both values; `manual` → `needs_review` |
| `F029-REQ-012` | FR-F029-12 | api | Slack thread reply → comment with `source: provider`; unknown email → owner attribution |
| `F029-REQ-013` | FR-F029-13 | api | adapter retries 5xx three times, honors `Retry-After`, logs `kind: call` rows |
| `F029-REQ-014` | FR-F029-14 | api | member → 403; owner may test only; foreign id → 404; missing idempotency key → 400 |
| `F029-REQ-015` | FR-F029-15 | frontend, e2e | page shows cards, popup hand-off, states with `Reconnect`, test dialog, binding dialog |
| `F029-NFR-001` | NFR-F029-01 | performance | reads p95 < 500 ms; callback < 2 s; 1,000-row sync < 5 min; notify p95 < 3 s |
| `F029-NFR-002` | NFR-F029-02 | api | PKCE and state enforced; rewrap by `key_id`; cross-tenant state rejected |
| `F029-NFR-003` | NFR-F029-03 | accessibility | axe serious = 0; status text plus icon; popup result announced |
| `F029-NFR-004` | NFR-F029-04 | api | jobs idempotent per cursor; restart resumes; dead letter after 3; metrics emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F029/`.
