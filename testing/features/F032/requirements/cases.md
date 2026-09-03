# F032 requirements cases

Feature: Project health/governance. Flag `F032_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F032-REQ-001` | FR-F032-01 | api, database | PUT model with weights 40/30/10/10/10 → 200; weights summing to 99 → 400 `field_errors.weights`; second `tenant_default` → 409 |
| `F032-REQ-002` | FR-F032-02 | api | 15 days late → schedule 50; 10 percent over → budget 60; two medium risks → risk 67 |
| `F032-REQ-003` | FR-F032-03 | api | resource indicator missing → weights renormalized over 90, `confidence: 90`; no indicators → `unknown` |
| `F032-REQ-004` | FR-F032-04 | api | three row edits in 10 s → one recompute; `project-health.computed.v1` names moved indicators |
| `F032-REQ-005` | FR-F032-05 | api | GET health → computed, override, `effective_colour`; viewer without project access → 404 |
| `F032-REQ-006` | FR-F032-06 | api, frontend | override red with 9-char reason → 400; valid → audit and `health-override.set.v1`; past `expires_at` → `expired: true` |
| `F032-REQ-007` | FR-F032-07 | api | `project.provisioned.v1` → three gates in sequence with `pending` and `attempt: 0` |
| `F032-REQ-008` | FR-F032-08 | api, frontend | submit gate 2 before gate 1 → 409 `gate_sequence`; missing checklist → 400 `evidence[1]`; complete → `submitted`, approval opened |
| `F032-REQ-009` | FR-F032-09 | api, database | approve → decision row with approver, `decided_at`, `evidence_snapshot`; decide pending gate → 409; reject → `pending`, attempt 2 |
| `F032-REQ-010` | FR-F032-10 | api, e2e | `approval.decided.v1` applied once; replay → no second decision row |
| `F032-REQ-011` | FR-F032-11 | api | POST intake → `submitted`, approval with policy `project_intake`, `project-intake.submitted.v1` |
| `F032-REQ-012` | FR-F032-12 | api, e2e | approval approved → `provisioning` → `provisioned` with `project_sheet_id`, portfolio membership added; failure → `failed` with error |
| `F032-REQ-013` | FR-F032-13 | api | tenant B → 404 on all routes; viewer → 403 on override, model, submit, decide; each mutation → audit row |
| `F032-REQ-014` | FR-F032-14 | frontend, e2e | health card, override banner, gate timeline, dialogs, intake form and status page with text labels on every colour |
| `F032-NFR-001` | NFR-F032-01 | performance | health and gates read p95 < 500 ms; writes p95 < 800 ms; recompute < 5 s; nightly 1,000 projects < 20 min |
| `F032-NFR-002` | NFR-F032-02 | api | evidence snapshot has IDs and checksums only; reasons absent from logs; non-approver decide → 403 |
| `F032-NFR-003` | NFR-F032-03 | accessibility | axe serious = 0; colours labelled; timeline is ordered list; dialogs trap focus |
| `F032-NFR-004` | NFR-F032-04 | api | recompute idempotent by source version, retried 3 times then dead-lettered with `last_error`; spans carry IDs |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F032/`.
