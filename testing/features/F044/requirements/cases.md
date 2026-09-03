# F044 requirements cases

Feature: contract and release control — `check-contracts`, `check-migrations`, `check-flags`, `verify-release`.

Fixtures: `testing/features/F044/fixtures/{catalog,tickets,openapi,migrations,flags,evidence}/` with a good tree and one mutated copy per case. All runs are offline against fixture trees; the real repository is never mutated.

| Case | Requirement | Lanes | Setup and expected finding |
|---|---|---|---|
| `F044-REQ-001` | FR-F044-01 | api | Catalog row missing the `roles` column and a second row repeating id `F012` → `contract.row_malformed` and `contract.row_duplicate`; a well-formed catalog parses 61 rows into `ContractRow` with no findings |
| `F044-REQ-002` | FR-F044-02 | api | Ticket F012 section 4 drops the backticked route `/api/v1/dependencies` → `contract.route_missing_in_ticket`; drops event `dependency.created.v1` → `contract.event_missing_in_ticket`; both name the ticket path and line |
| `F044-REQ-003` | FR-F044-03 | api | Ticket for module `sheets` omits `services/api/src/sheets/**` from `owned_paths` → `contract.paths_mismatch`; ticket without a link to `docs/architecture-decisions.md` → `contract.decision_link` |
| `F044-REQ-004` | FR-F044-04 | api | `openapi/v1.json` missing `paths["/api/v1/sheets"].post`, an `operationId` of `createSheet` instead of `sheets_create`, and a route lacking `x-opshub-feature` → `openapi.route_missing`, `openapi.operation_id`, `openapi.feature_extension`; absent OpenAPI file skips the lane without a finding |
| `F044-REQ-005` | FR-F044-05 | api | `crates/events/src/registry.rs` missing `SHEET_CREATED_V1` → `events.registry_missing`; an extra constant absent from the catalog → `events.registry_orphan`; payload struct with no `tenant_id` → payload finding |
| `F044-REQ-006` | FR-F044-06 | api | `apps/web/src/api/generated/manifest.json` carrying a stale `openapi_sha256` → `client.stale`; MCP `services/mcp/schemas/manifest.json` with a stale contract hash → the matching stale finding |
| `F044-REQ-007` | FR-F044-07 | database | Migration `create_sheets.sql` (no timestamp), an `up` with no matching `down`, and a module segment not in the catalog → `migration.name`, `migration.missing_down`, `migration.module_unknown` |
| `F044-REQ-008` | FR-F044-08 | database | Two migrations sharing one timestamp → `migration.order`; a branch migration timestamped before the newest reachable from `origin/main` → `migration.order` naming both files |
| `F044-REQ-009` | FR-F044-09 | database | `up` containing `DROP COLUMN`, `ADD COLUMN … NOT NULL` without `DEFAULT`, and `CREATE INDEX` without `CONCURRENTLY` → one `migration.unsafe` finding per statement with file and line; no SQL is executed |
| `F044-REQ-010` | FR-F044-10 | api | `crates/contracts/src/feature_flags.rs` missing `F029_FEATURE`, a flag whose `feature` is not in the plan, and a flag defaulting on → `flag.missing`, `flag.orphan`, `flag.default` |
| `F044-REQ-011` | FR-F044-11 | api | Planned ticket whose flag is `Active`, archived-in-milestone ticket whose flag is `Planned`, and a completed milestone whose flag is not `Graduated` → `flag.state` per case |
| `F044-REQ-012` | FR-F044-12 | api, e2e | `verify-release F029` with the ticket still in `work/tickets`, then with one task unarchived, then with `testing/evidence/F029/manifest.json` absent → a distinct precondition finding each time and exit 1 |
| `F044-REQ-013` | FR-F044-13 | api, database | Successful `verify-release F029` writes `testing/evidence/F029/release.json` with `id`, `verified_at`, `verifier`, `head_commit`, per-input `sha256`, the three gate results, lane results, and the signature; rerunning with an unchanged tree reproduces every field except `verified_at` and `head_commit` |
| `F044-REQ-014` | FR-F044-14 | api | `verify-release` without `XTASK_ROLE=release-manager` and outside CI refuses to write `release.json` and exits 3; with the role set, `verifier` records `XTASK_OWNER`; with `GITHUB_ACTIONS=true` on `main`, the write succeeds |
| `F044-REQ-015` | FR-F044-15 | api, e2e | `verify-release --milestone M1` over 10 fixture features writes `testing/evidence/milestones/M1.json` with one signature per feature; one failing feature fails the milestone and names it |
| `F044-REQ-016` | FR-F044-16 | api, frontend | Each of the four commands under `--json` emits the shared object shape and exit codes 0/1/2/3; `.githooks/pre-commit`, `.githooks/pre-push`, and `.github/workflows/gates.yml` invoke the commands the ticket lists |
| `F044-NFR-001` | NFR-F044-01 | performance | 61 tickets, a 2 MiB `openapi/v1.json`, and 500 migrations: `check-contracts` under 3 s; `verify-release` for one feature under 5 s; `--milestone` over 10 features under 30 s |
| `F044-NFR-002` | NFR-F044-02 | accessibility, performance | Under `strace`, no SQL connection and no network socket is opened; a write attempt outside `testing/evidence/` fails the run; the signature is reproducible from repository content alone |
| `F044-NFR-003` | NFR-F044-03 | accessibility | `NO_COLOR` honoured, ASCII-only output, and every drift finding prints both sides, for example `expected: sheet.created.v1, found: sheet.create.v1`; `--json` carries the same pair of values |
| `F044-NFR-004` | NFR-F044-04 | accessibility, e2e | Every finding names file, line, and the two disagreeing artifacts; killing the process mid-write leaves no partial `release.json` because the writer uses a temp file plus rename |

Evidence: each case records the command, fixture seed, exit code, JSON finding, and artifact path under `testing/evidence/F044/`.
