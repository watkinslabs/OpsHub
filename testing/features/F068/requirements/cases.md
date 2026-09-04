# F068 requirements cases

Feature: Persistence layer and data access classes. Flag `F068_FEATURE`. Every case maps to a ticket requirement ID and names the lane that proves it.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F068-REQ-001` | FR-F068-01 | api | the seven signatures and five associated types compile as declared; `Version` is a `NonZeroI64` newtype and `Deleted`/`Purged` carry id and version |
| `F068-REQ-002` | FR-F068-02 | api | a hand-written `impl Repository` fails to build with `module 'sealed' is private`; `BaseRepository` remains the only implementation |
| `F068-REQ-003` | FR-F068-03 | api | a `RepositorySpec` exposes constants and mappers only; a member returning SQL text or an executor does not compile |
| `F068-REQ-004` | FR-F068-04 | database | every read binds `tenant_id = $1` and hides `deleted_at is not null`; foreign tenant and soft-deleted rows both return `NotFound` |
| `F068-REQ-005` | FR-F068-05 | database | update, soft delete, and restore carry `version = $expected` in one statement; a stale version yields `VersionConflict` with expected and actual and writes nothing |
| `F068-REQ-006` | FR-F068-06 | database | each mutation writes the `audit_events` and `outbox_events` rows on the same connection; no public `audit`, `enqueue`, or `publish` member exists |
| `F068-REQ-007` | FR-F068-07 | api | `S::event` is total over the five mutating operations; `UserSpec` maps to `user.created.v1`, `user.updated.v1`, `user.deactivated.v1`, and a silent purge |
| `F068-REQ-008` | FR-F068-08 | database | a mutating method accepts only `WriteCtx`; a replayed idempotency key returns the first entity and writes no second row |
| `F068-REQ-009` | FR-F068-09 | api, database | `PurgeCtx` needs a verified `PurgeGrant`; purge removes children, audits the pre-image, and publishes nothing |
| `F068-REQ-010` | FR-F068-10 | database | keyset paging over the signed cursor; a cursor from another tenant, order, filter, or table, or an expired one, is `InvalidCursor`; an unknown sort key is `InvalidSort` |
| `F068-REQ-011` | FR-F068-11 | database | one `UnitOfWork` transaction spans two repositories; a rollback removes write, audit row, and event together |
| `F068-REQ-012` | FR-F068-12 | database | the pool handle wraps its own single write; the transaction handle never begins, commits, or rolls back |
| `F068-REQ-013` | FR-F068-13 | api, e2e | `find_by_email`, `list_active_in_group`, and `count_by_status` stay tenant-scoped; no `query`, `execute`, `raw`, `sql`, or `pool` member exists |
| `F068-REQ-014` | FR-F068-14 | e2e | each of the six gate rules fires on its fixture tree with the expected code, path, and line; the clean tree exits 0 |
| `F068-REQ-015` | FR-F068-15 | e2e | the policy file lists the eleven permitted `jsonb` columns; F029's four array columns are reported with the owning feature |
| `F068-REQ-016` | FR-F068-16 | frontend, e2e | sorted `BLOCKED:` lines, a single summary or JSON object, and exit codes 0, 1, 2, and 3 including baseline refusal |
| `F068-NFR-001` | NFR-F068-01 | performance | insert is one batch, update adds a read only on conflict, list is one statement; gate under 2 s; page 2,000 as cheap as page 2 |
| `F068-NFR-002` | NFR-F068-02 | database, api | no unscoped statement; cross-tenant work returns `NotFound`; errors and `Debug` carry no row value or idempotency key; the gate opens no connection |
| `F068-NFR-003` | NFR-F068-03 | accessibility | ASCII output, findings with path and line, words not colour, JSON parity, and a README with one heading per recipe step |
| `F068-NFR-004` | NFR-F068-04 | database, performance | spans and metrics per operation; audit and outbox atomicity proven by rollback on every specification; two gate runs byte-identical |
| `F068-NFR-005` | NFR-F068-05 | database | the eight-case conformance suite runs against every entry in the link-time registry; a catalog table with no specification is `persist.table_unmapped` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F068/`.
