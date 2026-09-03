# F015 requirements cases

Feature: Templates and baselines. Flag `F015_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F015-REQ-001` | FR-F015-01 | api | admin creates template "Launch playbook" in category `pmo` → 201, version 1, no published version |
| `F015-REQ-002` | FR-F015-02 | api | valid manifest → draft version 1; dangling dependency key → 400 `field_errors.manifest.sheets[0].dependencies[2]` |
| `F015-REQ-003` | FR-F015-03 | api | 21 sheets, 5,001 rows, or 2 MB + 1 byte → 400 with the limit name |
| `F015-REQ-004` | FR-F015-04 | api, database | publish → immutable, `template.published.v1`; update published → 409 `immutable` |
| `F015-REQ-005` | FR-F015-05 | api, database | seed has 10 built-ins, one per category; `copy_from` clones into a tenant draft |
| `F015-REQ-006` | FR-F015-06 | api | provision published version → 202 run `queued` under 2 s; draft → 400 `not_published` |
| `F015-REQ-007` | FR-F015-07 | api | worker creates sheets, rows with calendar-resolved dates, dependencies, views, draft forms; reports `skipped` |
| `F015-REQ-008` | FR-F015-08 | api | failing dependencies step → 3 retries, rollback, `provisioning.failed.v1`; success → `project.provisioned.v1` |
| `F015-REQ-009` | FR-F015-09 | api, frontend | run poll → per-step status and `created_ids`; non-member → 404 |
| `F015-REQ-010` | FR-F015-10 | api, database | capture baseline → all rows snapshotted, `baseline.captured.v1`; 21st → 409 |
| `F015-REQ-011` | FR-F015-11 | api | list sorted by `captured_at`; editor delete → 403 |
| `F015-REQ-012` | FR-F015-12 | api | reschedule Kickoff +3 working days → `finish_variance_days: 3`, `slipped`; totals updated |
| `F015-REQ-013` | FR-F015-13 | api, database | each mutation → one audit and one outbox event; provisioning steps audited with run correlation |
| `F015-REQ-014` | FR-F015-14 | api | tenant B template/run/baseline → 404; built-in PATCH → 403; editor provision → 403 |
| `F015-REQ-015` | FR-F015-15 | frontend, e2e | catalog, provision dialog, status page, baseline list, variance panel with all states; Gantt overlay via `?baseline_id=` |
| `F015-NFR-001` | NFR-F015-01 | performance | provision ack p95 < 2 s; 500-row run < 60 s; 100k capture < 30 s; variance p95 < 500 ms |
| `F015-NFR-002` | NFR-F015-02 | api | cross-tenant, guest, role-negative suite green; role placeholders resolve only in target tenant |
| `F015-NFR-003` | NFR-F015-03 | accessibility | axe serious = 0; step progress announced; variance chips carry text |
| `F015-NFR-004` | NFR-F015-04 | api | step replay is idempotent; dead letter after 3 failures; metrics and spans present |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F015/`.
