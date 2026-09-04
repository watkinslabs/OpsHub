# F069 requirements cases

Feature: Home and my work. Flag `F069_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F069-REQ-001` | FR-F069-01 | api, performance | one `GET /api/v1/home` returns five ordered sections at caps 10/10/10/12/20 with `truncated` set; no cursor, filter or sort accepted |
| `F069-REQ-002` | FR-F069-02 | api | registered providers run concurrently; unregistered slot → `unavailable`; 400 ms stub → `degraded` with `correlation_id` inside a `200` |
| `F069-REQ-003` | FR-F069-03 | api, e2e | resolver called once per `target_kind`; unreadable targets dropped with no count, marker or differing body |
| `F069-REQ-004` | FR-F069-04 | api | favourites page newest-first, `limit` 1–100; `filter=unavailable` returns cached label and no `path` |
| `F069-REQ-005` | FR-F069-05 | api | pin requires read → else `not_found`; duplicate → `conflict` with existing id; 201st → `conflict` `field_errors.limit`; `favorite.added.v1` published |
| `F069-REQ-006` | FR-F069-06 | api | unpin under `If-Match` on own row only; unavailable target still removable; other user's id → `not_found`; `favorite.removed.v1` published |
| `F069-REQ-007` | FR-F069-07 | api, performance | `2xx` on the four observed reads records a visit off-request; non-`2xx` records none; repeat inside 60 s coalesces; full channel drops and counts |
| `F069-REQ-008` | FR-F069-08 | api, database | recents newest-visited first with `visit_count`; permission-filtered per request; trimmed to 100 in the flush transaction |
| `F069-REQ-009` | FR-F069-09 | api, e2e | soft-delete, archive, move out of reach and unshare each remove the item from home, recents and favourites on the next read; the favourite row survives and returns with access |
| `F069-REQ-010` | FR-F069-10 | api, database | `home.prune` deletes recents past 90 days and rows for purged targets in 500-id batches, refreshes labels, is idempotent and stops at 10,000 rows |
| `F069-REQ-011` | FR-F069-11 | api | every named query carries `user_id`; `tenant-admin` sees only their own rows on both lists |
| `F069-REQ-012` | FR-F069-12 | api, frontend | no favourites, no recents, all sections empty → `onboarding.state new` with up to three workspaces, `create_sheet`, or `request_access`; each empty section reports its reason |
| `F069-REQ-013` | FR-F069-13 | e2e, frontend | sign-in lands on `/`; the product mark returns to it; the last-route restore is gone |
| `F069-REQ-014` | FR-F069-14 | api | `invalid` for unknown kind and malformed body; `not_found` for unreadable, foreign-user and cross-tenant ids; `conflict` for duplicate and limit; `rate_limited` past 60 mutations per minute; empty registry is still `200` |
| `F069-NFR-001` | NFR-F069-01 | performance | home p95 < 400 ms and p99 < 800 ms at full caps; thirteen statements regardless of item count; lists p95 < 150 ms; visit recording < 1 ms p99 |
| `F069-NFR-002` | NFR-F069-02 | api | `tenant_id` and `user_id` predicates on every query; bodies, errors and telemetry never name an unreadable target; unavailable pin exposes only the cached label |
| `F069-NFR-003` | NFR-F069-03 | accessibility | axe serious and critical = 0 in both themes and densities; sections are labelled regions with headings; toggle state is not colour-only; empty state announced once |
| `F069-NFR-004` | NFR-F069-04 | api, performance | restart loses at most one 5 s visit window; `home_request_duration_seconds`, `home_section_state_total`, `home_visits_dropped_total` and `home_prune_rows_total` emitted; spans carry the section key |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F069/`.
