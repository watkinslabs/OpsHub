# F043 requirements cases

Feature: Fanout orchestration. Flag `F043_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F043-REQ-001` | FR-F043-01 | api | T901 depends on unarchived T900 → `lane.precondition`, exit 3; overlap with active F901 → refused |
| `F043-REQ-002` | FR-F043-02 | api, database | claim T900 with `XTASK_NOW` → file in `work/inprogress`, only `status`/`started_at` lines differ |
| `F043-REQ-003` | FR-F043-03 | api | branch `t900-alpha` created from `origin/main`; worktree at `.worktrees/t900-alpha`; pre-existing branch → `lane.branch_exists` |
| `F043-REQ-004` | FR-F043-04 | database | `.lanes/T900.toml` has every field; second claim → `lane.exists`, no change |
| `F043-REQ-005` | FR-F043-05 | database | 100 lanes → 101st claim `lane.slots_exhausted`; two concurrent claims get slots 0 and 1 |
| `F043-REQ-006` | FR-F043-06 | api, accessibility | `allocate-target` twice → identical `export` lines; `--json` shape |
| `F043-REQ-007` | FR-F043-07 | api | `allocate-fixture T900` slot 0 → `lane_t900`, `lane.t900.`, port 20000, UUIDv5 tenant, seed crc32 |
| `F043-REQ-008` | FR-F043-08 | e2e | `test-feature` inside the worktree → stub harness sees `OPSHUB_TEST_SCHEMA=lane_t900` |
| `F043-REQ-009` | FR-F043-09 | api | junit, trace, axe, criterion, xtask JSON copied under lane dirs; manifest written |
| `F043-REQ-010` | FR-F043-10 | database, performance | second collection identical file list; 600 MiB → `artifacts.too_large`; escaping symlink refused |
| `F043-REQ-011` | FR-F043-11 | api | failing junit → `release --outcome done` refused; passing → archived, worktree removed, slot freed |
| `F043-REQ-012` | FR-F043-12 | api | abandon restores planning file bytes; evidence kept unless `--purge-evidence` |
| `F043-REQ-013` | FR-F043-13 | api | `XTASK_OWNER=b@…` release → `lane.not_owner`; `--owner-override` logged |
| `F043-REQ-014` | FR-F043-14 | frontend | `--list` sorted output; `no active lanes` when empty |
| `F043-REQ-015` | FR-F043-15 | database | each command appends a `history.log` line; exit codes 0/1/2/3 |
| `F043-NFR-001` | NFR-F043-01 | performance | claim < 5 s with 100 lanes; allocations < 100 ms; collection < 64 MiB resident |
| `F043-NFR-002` | NFR-F043-02 | database | `.lanes/`, `.worktrees/`, `.agent-target/` ignored by git; symlink escape refused; no code executed from worktree |
| `F043-NFR-003` | NFR-F043-03 | accessibility | `eval` round trip in sh/bash/zsh; `NO_COLOR`; ASCII |
| `F043-NFR-004` | NFR-F043-04 | database | crash between move and lane file → `--repair` reconciles; `history.log` append-only |

Evidence: command, fixture, result, and artifact path recorded under `testing/evidence/F043/`.
