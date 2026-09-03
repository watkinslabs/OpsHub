# F048 requirements cases

Feature: Entitlements and feature flags. Flag `F048_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F048-REQ-001` | FR-F048-01 | api | tenant with 2 stored entitlements → list returns 10 modules, 8 with `state: none`, `version: 0` |
| `F048-REQ-002` | FR-F048-02 | api | PUT `data-shuttle` with `limits.max_widgets` → 400 `field_errors.limits.max_widgets`; unknown module → 404 |
| `F048-REQ-003` | FR-F048-03 | api | GET flags → 11 seeded keys with owner, rollout state, cleanup ticket, caller override |
| `F048-REQ-004` | FR-F048-04 | api | tenant-admin sets override → 200; tenant-admin sends `rollout_state` → 403 `denied` |
| `F048-REQ-005` | FR-F048-05 | api, database | `draft`→`general` → 409 `invalid_transition`; retire without cleanup ticket → 409 |
| `F048-REQ-006` | FR-F048-06 | api, performance | kill → default off, state `internal`, all overrides `suspended`, both tenants `reason: killed` |
| `F048-REQ-007` | FR-F048-07 | api | evaluate 3 keys + 2 modules → per-key reason and per-module allowed; 51 keys → 400 |
| `F048-REQ-008` | FR-F048-08 | api | unit truth table: killed, retired, override, general, tenant_list, percentage bucket, internal, draft, default |
| `F048-REQ-009` | FR-F048-09 | api | `bridge` trial expired → `allowed: false, reason: trial_expired`; active + flag off → `flag_disabled` |
| `F048-REQ-010` | FR-F048-10 | api | probe route behind `RequireModule(bridge)` → 403 with `field_errors.module`, probe never ran |
| `F048-REQ-011` | FR-F048-11 | api, database | each mutation → one audit row with diff and one outbox event with `changed_fields` |
| `F048-REQ-012` | FR-F048-12 | performance | kill on instance 1 → instance 2 denies within 30 s; instance 1 within 2 s |
| `F048-REQ-013` | FR-F048-13 | api, database | override `expires_at` yesterday → ignored, `override.expired: true`; prune job deletes it |
| `F048-REQ-014` | FR-F048-14 | frontend, e2e | admin edits trial and override through the pages; member sees denied panel |
| `F048-REQ-015` | FR-F048-15 | api | body `tenant_id` of tenant B → 400; tenant B override invisible in tenant A list |
| `F048-NFR-001` | NFR-F048-01 | performance | guard p99 < 1 ms warm; evaluate 50 keys p95 < 100 ms; list p95 < 500 ms |
| `F048-NFR-002` | NFR-F048-02 | api | platform-field and cross-tenant negatives green; reason string absent from logs |
| `F048-NFR-003` | NFR-F048-03 | accessibility | axe serious = 0; kill dialog focus trap; badges carry text |
| `F048-NFR-004` | NFR-F048-04 | api, performance | `entitlement_denied_total` increments; span carries tenant, key, module, correlation |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F048/`.
