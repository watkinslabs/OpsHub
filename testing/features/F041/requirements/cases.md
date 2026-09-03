# F041 requirements cases

Feature: Work-item schema. Flag `F041_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F041-REQ-001` | FR-F041-01 | api | task file missing `parent_story` → `front.missing_key` at the front matter line |
| `F041-REQ-002` | FR-F041-02 | api | `estimate: 4`, `priority: P9`, `finished_at: yesterday` → three `front.bad_value` findings |
| `F041-REQ-003` | FR-F041-03 | api | same id in `work/tasks` and `work/archived` → `id.duplicate`; `T900-x.md` with `id: T901` → `id.filename_mismatch` |
| `F041-REQ-004` | FR-F041-04 | api | title `Grid API` with file `T023-grid-ui.md` → `file.slug_mismatch`; branch `t23-grid-api` → `branch.invalid` |
| `F041-REQ-005` | FR-F041-05 | api | story under F900 with `parent_epic: E001` while F900 is in E900 → `parent.inconsistent` |
| `F041-REQ-006` | FR-F041-06 | api | T900↔T901 cycle → `depends.cycle T900 -> T901 -> T900`; F901 depends on F900 without mirror → `depends.blocks_mismatch` |
| `F041-REQ-007` | FR-F041-07 | api | plan says F902 depends on F900, F901; ticket lists F900 → `plan.depends_mismatch missing: [F901]` |
| `F041-REQ-008` | FR-F041-08 | api | feature owning `services/api/**` → `paths.catch_all`; story owning `services/api/src/authz/**` under a `sheets` feature → `paths.not_subset`; a feature owning `.lanes/**` or `testing/evidence/**` → no finding (exempt roots) |
| `F041-REQ-009` | FR-F041-09 | api | feature without `### Fast fanout configuration` or with two scenarios → `section.missing` |
| `F041-REQ-010` | FR-F041-10 | api | ticket with 6 FRs, story with 3 SRs, a `PLACEHOLDERS` marker in the body → `content.too_thin`, `marker.unresolved` |
| `F041-REQ-011` | FR-F041-11 | api, database | file in `work/inprogress` with `started_at: null` → `lifecycle.timestamp`; archived with `finished_at < started_at` → `lifecycle.timestamp` |
| `F041-REQ-012` | FR-F041-12 | database, performance | 501-line file → `line.limit`; NUL-byte file skipped; symlink not followed |
| `F041-REQ-013` | FR-F041-13 | api | plan lists T915 with no file → `plan.missing_item`; `work/tasks/T999-x.md` → `plan.orphan_item`; row with three stories → `plan.pairing` |
| `F041-REQ-014` | FR-F041-14 | api | `testing/features/F900/e2e/cases.md` deleted → `harness.missing`; FR-F900-07 not cited → `harness.uncovered` |
| `F041-REQ-015` | FR-F041-15 | frontend, accessibility | findings sorted by path, line, code; `--json` object shape; exit 0/1/2 |
| `F041-NFR-001` | NFR-F041-01 | performance | 500 work files + 20,000-file tree validated in < 2 s |
| `F041-NFR-002` | NFR-F041-02 | database | symlink escape refused; echoed lines truncated to 200 chars; no network sockets opened (strace count 0) |
| `F041-NFR-003` | NFR-F041-03 | accessibility | `NO_COLOR` honoured; ASCII-only; no line > 200 chars; JSON parity with text |
| `F041-NFR-004` | NFR-F041-04 | frontend, e2e | two runs byte-identical; `GITHUB_ACTIONS=true` emits `::error file=…` per finding |

Evidence: command, fixture name, result, and artifact path recorded under `testing/evidence/F041/`.
