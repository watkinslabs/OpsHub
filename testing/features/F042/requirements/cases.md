# F042 requirements cases

Feature: xtask audit/gates. Flag `F042_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F042-REQ-001` | FR-F042-01 | api | mixed-case token with U+200D inserted → one `policy.token` at the original line/column, masked |
| `F042-REQ-002` | FR-F042-02 | api, database | staged `docs/a.md` with token → exit 1; staged `automation/README.md` with token → skipped; staged PNG → skipped |
| `F042-REQ-003` | FR-F042-03 | api | message with token only after the scissors line → exit 0; token in subject → exit 1 |
| `F042-REQ-004` | FR-F042-04 | api | token in author email local part of commit 3 of 5 → finding `commit:<sha> author email` |
| `F042-REQ-005` | FR-F042-05 | api | body file missing → exit 2; token in title → exit 1 |
| `F042-REQ-006` | FR-F042-06 | api | active T022 owns `services/api/src/sheets/**`; staged `apps/web/.../api.ts` → `ownership.outside`; empty inprogress → skipped, exit 0 |
| `F042-REQ-007` | FR-F042-07 | api | active F900 and F901 both own `crates/domain/src/sheets/**` → `ownership.overlap`; staged path matched by both → `ownership.ambiguous` |
| `F042-REQ-008` | FR-F042-08 | api | active T023 depends on T022 in `work/tasks` → `depends.unmet`; active S900 conflicts_with active S901 → `depends.conflict` |
| `F042-REQ-009` | FR-F042-09 | api | broken control (empty token list) → `self-test` exit 1 naming the control |
| `F042-REQ-010` | FR-F042-10 | e2e | `install-hooks` twice → `core.hooksPath=.githooks`, mode 0755, same output |
| `F042-REQ-011` | FR-F042-11 | e2e | pre-commit stops at `audit-staged` failure without running validators; pre-push scans `remote..local` |
| `F042-REQ-012` | FR-F042-12 | frontend | `--json` on each command → contract shape, exit codes 0/1/2 |
| `F042-REQ-013` | FR-F042-13 | api, performance | token straddling byte 1,048,576 of a 3 MiB blob detected once; 6,000-commit range count exact |
| `F042-REQ-014` | FR-F042-14 | accessibility | captured output of every failing case contains no token |
| `F042-NFR-001` | NFR-F042-01 | performance | 200 files / 20 MiB < 1 s; 1,000 commits < 2 s; self-test < 500 ms |
| `F042-NFR-002` | NFR-F042-02 | database | only `git` subprocesses spawned (no shell); working tree untouched; author email masked |
| `F042-NFR-003` | NFR-F042-03 | accessibility | `NO_COLOR`, ASCII, ≤ 200 chars, `BLOCKED:` prefix |
| `F042-NFR-004` | NFR-F042-04 | frontend, e2e | byte-identical repeat runs; `self-test` present in the CI validate step |

Evidence: command, fixture, result, and artifact path recorded under `testing/evidence/F042/`.
