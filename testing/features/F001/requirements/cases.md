# F001 requirements cases

Feature: Repository and CI. Flag `F001_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F001-REQ-001` | FR-F001-01 | api, e2e | clean clone → `cargo build --workspace` exits 0, five binaries present, cold CI under 10 min |
| `F001-REQ-002` | FR-F001-02 | api | root `Cargo.toml` → ten members, edition 2024, shared deps inherited |
| `F001-REQ-003` | FR-F001-03 | api | injected unused variable → clippy exits 1; clean tree → fmt and clippy exit 0 |
| `F001-REQ-004` | FR-F001-04 | api, e2e | `pnpm --filter web build` → `apps/web/dist/index.html`; typecheck strict passes |
| `F001-REQ-005` | FR-F001-05 | frontend, e2e | dev server `/status` → badge shows `ok`, `degraded`, or `unreachable` |
| `F001-REQ-006` | FR-F001-06 | api, e2e | `gates.yml` → five named jobs; PR with a failing check cannot merge |
| `F001-REQ-007` | FR-F001-07 | api | invalid ticket fixture → `validate-work` fails with `BLOCKED:` from `validate-work` |
| `F001-REQ-008` | FR-F001-08 | api, e2e | poisoned commit body → `policy` fails with `BLOCKED:`; clean history passes |
| `F001-REQ-009` | FR-F001-09 | api | 501-line file → `line-limit` fails with `limit is 500`; 500 lines passes |
| `F001-REQ-010` | FR-F001-10 | api, database | `rust` job → `postgres:18` and `nats:2.11` services, `cargo test`, `rust-junit` artifact |
| `F001-REQ-011` | FR-F001-11 | api | `web` job → lint, typecheck, Vitest JUnit, build, `web-build` artifact |
| `F001-REQ-012` | FR-F001-12 | api | docs-only push → `rust` and `web` skipped, other three run; superseded run cancelled |
| `F001-REQ-013` | FR-F001-13 | api | two builds with different `CARGO_TARGET_DIR` → disjoint target dirs |
| `F001-REQ-014` | FR-F001-14 | e2e | merged feature → `test-feature F001` and `test-all` exit 0, evidence written |
| `F001-NFR-001` | NFR-F001-01 | performance | warm build < 4 min, web build < 90 s, workflow < 15 min |
| `F001-NFR-002` | NFR-F001-02 | api | actions pinned by SHA, `contents: read`, frozen lockfile, `cargo deny` runs |
| `F001-NFR-003` | NFR-F001-03 | accessibility | `/status` axe serious = 0, single `h1`, live region announces state |
| `F001-NFR-004` | NFR-F001-04 | api | rerun of a job is idempotent; no retry-on-flake configuration present |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F001/`.
