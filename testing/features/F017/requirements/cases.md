# F017 requirements cases

Feature: Files and proofing. Flag `F017_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F017-REQ-001` | FR-F017-01 | api | editor starts upload on row → 201 with `put_url`, `expires_at` +15 min |
| `F017-REQ-002` | FR-F017-02 | api | `application/x-msdownload` → 400 `mime_type: not_allowed`; 251 MB → `size_bytes: too_large` |
| `F017-REQ-003` | FR-F017-03 | api, database | complete after PUT → version 1 `pending`, `file.uploaded.v1`; without PUT → 409 `object_missing` |
| `F017-REQ-004` | FR-F017-04 | api | clean PDF → `clean`, `file.scanned.v1`; EICAR → `quarantined`, object under `quarantine/`, `file.quarantined.v1` |
| `F017-REQ-005` | FR-F017-05 | api | download clean → 302 signed 15 min; pending → 409; quarantined → 403; `?version=1` serves old version |
| `F017-REQ-006` | FR-F017-06 | api | GET file → versions array, scan and preview state, proof summary |
| `F017-REQ-007` | FR-F017-07 | api | PNG and PDF → `preview.state ready` with WebP key; ZIP → `unsupported` |
| `F017-REQ-008` | FR-F017-08 | api, database | add version → `current_version` 2, version 1 still downloadable, `file.version-added.v1` |
| `F017-REQ-009` | FR-F017-09 | api | delete → hidden from list, `file.deleted.v1`, objects untouched |
| `F017-REQ-010` | FR-F017-10 | api | 150 files → pages of 100, `scan_state=clean` filter, sort by name |
| `F017-REQ-011` | FR-F017-11 | api, database | proof with 2 reviewers → `open`; second open → 409; reviewer without access → 400 |
| `F017-REQ-012` | FR-F017-12 | api | both approve → `approved`; first reject → `rejected`; repeat → 409; outsider → 403 |
| `F017-REQ-013` | FR-F017-13 | api | new version on open proof → `superseded` and `proof.decided.v1 outcome superseded` |
| `F017-REQ-014` | FR-F017-14 | frontend, e2e | file tab, badges, versions, proof panel render and act |
| `F017-REQ-015` | FR-F017-15 | api, database | each mutation → audit row and outbox row; tenant B → 404; viewer → 403 |
| `F017-NFR-001` | NFR-F017-01 | performance | start/complete p95 < 800 ms; list p95 < 500 ms; 250 MB scan < 120 s |
| `F017-NFR-002` | NFR-F017-02 | api, database | keys under tenant prefix; signed URL expired at +16 min → rejected; quarantine never signed |
| `F017-NFR-003` | NFR-F017-03 | accessibility | axe serious = 0; keyboard upload; live region on scan and decision |
| `F017-NFR-004` | NFR-F017-04 | api | replayed scan job no-op; 5 failures → dead letter with `pending`; metrics exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F017/`.
