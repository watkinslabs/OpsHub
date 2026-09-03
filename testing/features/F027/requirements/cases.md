# F027 requirements cases

Feature: Governance/compliance. Flag `F027_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F027-REQ-001` | FR-F027-01 | api, database | first read seeds eight policies; `audit_events` purge 200 → 400 `invalid` |
| `F027-REQ-002` | FR-F027-02 | api | PUT with stale `If-Match` → 409; valid PUT → `retention-policy.updated.v1` and audit diff |
| `F027-REQ-003` | FR-F027-03 | api | sweep soft-deletes only `auto_soft_delete` kinds and marks `purge_eligible`; never hard-deletes |
| `F027-REQ-004` | FR-F027-04 | api, database | hold on `sheet:{id}` → rows excluded from sweep and purge; release publishes `action: released` |
| `F027-REQ-005` | FR-F027-05 | api | restore under hold succeeds; creator release under two-person policy → 403 |
| `F027-REQ-006` | FR-F027-06 | api, database | export → 202 queued; second while running → 409 `conflict` |
| `F027-REQ-007` | FR-F027-07 | api, e2e | ZIP has one file per kind and `manifest.json`; secrets absent; URL valid 7 days |
| `F027-REQ-008` | FR-F027-08 | api | propose purge → preview 12,400 candidates, 310 held, code issued, nothing deleted |
| `F027-REQ-009` | FR-F027-09 | api, e2e | wrong code → 400; expired → 409; proposer under two-person → 403; second admin → confirmed |
| `F027-REQ-010` | FR-F027-10 | api, database | purge → 1,000-row batches, held skipped, blobs removed, audit rows untouched |
| `F027-REQ-011` | FR-F027-11 | api | review lists roles, groups, shares, links, tokens; JSON and CSV stored; event published |
| `F027-REQ-012` | FR-F027-12 | api, frontend | inactive 120 days and guest link 45 days flagged; `revoke` removes ACL and tokens |
| `F027-REQ-013` | FR-F027-13 | api | tenant-admin → 403 on all routes; foreign IDs → 404; missing `Idempotency-Key` → 400 |
| `F027-REQ-014` | FR-F027-14 | frontend, e2e | console lists all five areas; purge dialog requires retyped code; progress shown |
| `F027-NFR-001` | NFR-F027-01 | performance | reads p95 < 500 ms; purge 100k rows < 10 min; review 5,000 principals < 60 s |
| `F027-NFR-002` | NFR-F027-02 | api | export encrypted at rest, download audited, secrets redacted, holds honored |
| `F027-NFR-003` | NFR-F027-03 | accessibility | axe serious = 0; code field labelled; progress bars expose `aria-valuenow` |
| `F027-NFR-004` | NFR-F027-04 | api | export resumes after restart; purge dead-letters after 3 retries with `failed` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F027/`.
