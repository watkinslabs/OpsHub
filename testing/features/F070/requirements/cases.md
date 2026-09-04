# F070 requirements cases

Feature: Trash and recovery. Flag `F070_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F070-REQ-001` | FR-F070-01 | api | index pages by `deleted_at desc, entry_id`; `kind`, `workspace_id`, `deleted_by`, date and `q` filters apply; `limit` 201 → 400 `invalid` |
| `F070-REQ-002` | FR-F070-02 | api | member with no access to `Procurement` sees no entry from it; its id → 404 `not_found` on index, restore and purge; deleter identity grants nothing |
| `F070-REQ-003` | FR-F070-03 | api, database | `sheet.deleted.v1` → one entry; replay and a lower `version` are discarded; `sheet.restored.v1` deletes it; `folder.updated.v1` with `deleted_at` in `changed_fields` projects a folder entry |
| `F070-REQ-004` | FR-F070-04 | api, performance | `trash.rebuild` writes a new `projection_epoch` and drops the old one atomically; rebuilt rows equal the incremental rows apart from `projected_at` and `projection_epoch` |
| `F070-REQ-005` | FR-F070-05 | api | registry loads `sheet`, `row`, `folder`; a duplicate kind key and an unknown resource key each refuse start-up; a kind declared outside this module is picked up with no change here |
| `F070-REQ-006` | FR-F070-06 | api, e2e | restore puts the sheet and its rows back, publishes `item.restored.v1`, removes the entry, returns the new `version`; write on the destination is required |
| `F070-REQ-007` | FR-F070-07 | api, frontend | child under a deleted parent → 409 `conflict` code `parent_deleted` naming the parent, nothing written, entry `blocked`; missing owning row → 404 with `target_missing` |
| `F070-REQ-008` | FR-F070-08 | api | `expires_at` is `deleted_at` plus the F027 `purge_after_days`; a null policy shows no countdown; the sweep marks `expired` and hands 500 per batch to the executor without deleting itself |
| `F070-REQ-009` | FR-F070-09 | api, frontend | a held entry stays past `expires_at` as `held`, is skipped and counted by the sweep, refuses `DELETE` with 409 `legal_hold`, and still restores |
| `F070-REQ-010` | FR-F070-10 | api, e2e | `DELETE` as `compliance-admin` with matching `If-Match` runs through the shared executor, audits `trash.purge`, publishes `item.purged.v1`, returns 204; an editor → 403 `denied`; stale `If-Match` → 409 |
| `F070-REQ-011` | FR-F070-11 | api | foreign-tenant kind, item and entry ids return `not_found` on all three routes; `q` never matches across tenants; the projector drops a tenant-mismatched event |
| `F070-REQ-012` | FR-F070-12 | frontend, e2e | the screen lists kind, title, location, deleter, countdown and state, filters and bulk-restores, offers `Restore parent first` on a blocked row, and disables `Purge` with a reason |
| `F070-NFR-001` | NFR-F070-01 | performance | first page p95 < 400 ms over 200,000 entries; projection lag p95 < 5 s and p99 < 120 s; rebuild of 200,000 entries < 3 minutes; a page is never short while visible rows remain |
| `F070-NFR-002` | NFR-F070-02 | api | no title, path or count leaks for an unreadable item; `deleted_by` falls back to `Someone`; purge is `compliance-admin`, audited, and refused under hold; guest and scoped-token negatives hold |
| `F070-NFR-003` | NFR-F070-03 | accessibility | axe serious and critical = 0 on the screen and both dialogs in both themes; state is text plus labelled icon; countdown is readable text; dialogs trap focus and announce results |
| `F070-NFR-004` | NFR-F070-04 | api | projector idempotent per `(tenant_id, kind, item_id, source_version)`, resumes from its cursor after restart, dead-letters after 3 attempts; the four metrics are emitted with the span fields present |
| `F070-NFR-005` | NFR-F070-05 | api | after a randomized delete/restore/out-of-order sequence, rebuild equals the live projection; a deliberately corrupted entry is detected by the same comparison |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F070/`.
