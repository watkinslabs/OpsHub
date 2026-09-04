---
id: F068
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E001
depends_on: [F001]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/lib.rs, crates/persistence/src/repository/**, crates/persistence/src/uow/**, crates/persistence/src/users/**, crates/persistence/schema-policy.toml, automation/xtask/src/persistence.rs, testing/fixtures/persistence/**, testing/features/F068/**]
feature_flag: F068_FEATURE
flag_default: off
branch: f068-persistence-layer-and-data-access-classes
started_at: null
finished_at: null
---

# F068 — Persistence layer and data access classes

## 1. Identity and dates

- Branch: `f068-persistence-layer-and-data-access-classes`
- Capability area: platform data access (spec section 2 canonical data model; section 8 release gates)
- Module slug: `persistence` (crate `crates/persistence`, gate module `automation/xtask/src/persistence.rs`)

### Decision references

- Architecture: `docs/architecture-decisions.md` section 2 (canonical data model) and section 2.1 (data access), with section 1 for the crate layout and section 3 for the cursor and version conventions
- Canonical contract: `docs/capability-contracts.md` row F068 (aggregate `repository`, module `persistence`, surface `crates/persistence/**`, `cargo xtask check-persistence`, the `Repository` and `UnitOfWork` contracts; events none; every table in that catalog reached only through its repository class; role maintainer)

## 2. Requirement specification

### Problem and user outcome

Sixty product features are about to write SQL. Decision section 2 says every tenant row carries `tenant_id`, `version`, audit columns, and `deleted_at`; that writes take an optimistic version check and an idempotency key; that changes publish through a transactional outbox. Decision 2.1 says all of that is applied by a shared contract rather than by each caller. Without that contract the rules are review comments: the ninth repository forgets `and deleted_at is null`, the fourteenth forgets the outbox row, the twenty-second reads across tenants in a join, and each omission is a data-leak or a lost event that no reviewer catches twice.

As a platform maintainer, I want one `Repository` contract that already applies the tenant predicate, the soft-delete filter, the version check, the audit row, and the outbox enqueue, one `UnitOfWork` that owns the transaction shared by several repositories, and `cargo xtask check-persistence` that fails the build when SQL, a pool, an array column, or an unlisted `jsonb` column escapes `crates/persistence/**`, so that a new object type is added by declaring a specification rather than by writing a statement, and forgetting a rule stops the compiler instead of reaching production.

### Functional requirements

- **FR-F068-01:** `crates/persistence/src/repository/mod.rs` declares the contract every data access class implements, with these exact signatures over `async_trait`: `async fn get(&self, ctx: &TenantCtx, id: Self::Id) -> Result<Self::Entity, RepoError>`; `async fn list(&self, ctx: &TenantCtx, filter: &Self::Filter, page: PageRequest) -> Result<Page<Self::Entity>, RepoError>`; `async fn insert(&self, ctx: &WriteCtx, new: Self::New) -> Result<Self::Entity, RepoError>`; `async fn update(&self, ctx: &WriteCtx, id: Self::Id, expected: Version, patch: Self::Patch) -> Result<Self::Entity, RepoError>`; `async fn soft_delete(&self, ctx: &WriteCtx, id: Self::Id, expected: Version) -> Result<Deleted, RepoError>`; `async fn restore(&self, ctx: &WriteCtx, id: Self::Id, expected: Version) -> Result<Self::Entity, RepoError>`; `async fn purge(&self, ctx: &PurgeCtx, id: Self::Id) -> Result<Purged, RepoError>`. The associated types are `type Entity: Send + Sync + 'static`, `type Id: Copy + Send + Sync + Into<Uuid>`, `type Filter: Predicate + Send + Sync`, `type New: Send`, and `type Patch: Send`. `Version` is a `NonZeroI64` newtype, `Deleted { id, version, deleted_at }`, `Purged { id, rows_removed }`.
- **FR-F068-02:** The contract is sealed and has exactly one implementation. `Repository: sealed::Sealed`, `sealed` is a private module, and the only `impl<S: RepositorySpec> sealed::Sealed for BaseRepository<'_, S>` plus the only `impl<S: RepositorySpec> Repository for BaseRepository<'_, S>` live in `crates/persistence/src/repository/base.rs`. A hand-written `impl Repository for MyRepository` fails to compile with `error[E0603]: module 'sealed' is private`, so the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue cannot be bypassed by writing a second implementation.
- **FR-F068-03:** A new data access class is a `RepositorySpec` implementation carrying data, never statements: `const TABLE: &'static str`, `const AGGREGATE: &'static str`, `const COLUMNS: &'static [&'static str]`, `const SORTABLE: &'static [&'static str]`, `const CO_TABLES: &'static [&'static str]` (child tables the same class owns), the five associated types of FR-F068-01, `fn map_row(row: &PgRow) -> Result<Self::Entity, RepoError>`, `fn bind_new(new: &Self::New, b: &mut Binder<'_>)`, `fn bind_patch(patch: &Self::Patch, b: &mut Binder<'_>)`, `fn payload(e: &Self::Entity) -> serde_json::Value`, and `fn event(op: Op) -> EventName`. `RepositorySpec` has no method returning `String`, `&str` SQL, or an executor, so a specification cannot express a predicate of its own.
- **FR-F068-04:** `BaseRepository` composes every statement and always scopes it. Reads are `select {COLUMNS} from {TABLE} where tenant_id = $1` plus the filter predicates plus, unless `Visibility::Deleted` or `Visibility::Any` is passed, `and deleted_at is null`; `list` defaults to `Visibility::Live`. `get` for another tenant, and `get` for a soft-deleted row under `Visibility::Live`, both return `RepoError::NotFound` with no distinguishing message, timing branch, or field, so existence never leaks across tenants.
- **FR-F068-05:** `update`, `soft_delete`, and `restore` compile to a single statement `update {TABLE} set <patch>, version = version + 1, updated_by = $a, updated_at = now() where id = $i and tenant_id = $t and version = $expected and deleted_at is null returning {COLUMNS}` (`restore` inverts the last predicate to `deleted_at is not null` and clears it; `soft_delete` sets `deleted_at = now()`). Zero affected rows triggers one scoped re-read that distinguishes `RepoError::VersionConflict { expected, actual }` from `RepoError::NotFound`. The returned entity carries the new version, which the API layer returns per decision section 3.
- **FR-F068-06:** Every mutation writes its audit row and its outbox row inside the same statement batch, on the same connection, before returning. `audit_events` receives `{ id, tenant_id, actor_id, action: "{AGGREGATE}.{op}", target_kind: AGGREGATE, target_id, before, after, field_diff, correlation_id, occurred_at }`, where `before` is the pre-image the base already read for the version check and `field_diff` is computed by the base from `COLUMNS`. `outbox_events` receives `{ id, tenant_id, aggregate: AGGREGATE, aggregate_id, event: S::event(op), payload: S::payload(&entity), correlation_id, idempotency_key, occurred_at, published_at: null }`. There is no public `audit`, `enqueue`, or `publish` method on any type in the crate, so neither row can be written or skipped separately.
- **FR-F068-07:** `S::event(op)` returns `EventName::Named(&'static str)` or `EventName::Silent(&'static str reason)`; there is no default, so a specification must state the event for all five mutating operations. Every `Named` value must appear in `docs/capability-contracts.md`; `cargo xtask check-contracts` already fails on an event a ticket does not carry, and FR-F068-14 adds the reverse check. `UserSpec` maps `Insert → user.created.v1`, `Update → user.updated.v1`, `SoftDelete → user.deactivated.v1`, `Restore → user.updated.v1`, and `Purge → EventName::Silent("purge is audited, not published; consumers erase on the retention job signal")`.
- **FR-F068-08:** `WriteCtx { tenant: TenantCtx, idempotency_key: IdempotencyKey, db: Db<'_> }` is the only argument type accepted by a mutating method, so decision section 2's "all writes require an idempotency key" is a type requirement. `outbox_events` carries a unique index on `(tenant_id, idempotency_key)`; a replayed key raises a unique violation that the base converts into a scoped re-read of the prior aggregate row, returning the original entity and `RepoError::Replayed` is never surfaced — the second call is a no-op returning the first call's result.
- **FR-F068-09:** `purge` is privileged. `PurgeCtx::new(tenant: TenantCtx, grant: PurgeGrant)` is the only constructor, `PurgeGrant` has a private field and is produced only by `PurgeGrant::verify(scopes: &Scopes, aggregate: &str) -> Result<PurgeGrant, RepoError::Forbidden>` against a `purge:{aggregate}` scope, and neither type implements `Default`, `Clone`, or `From<TenantCtx>`. `purge` deletes the row and its `CO_TABLES` children in one statement batch, writes an audit row with `action: "{AGGREGATE}.purge"` and the full pre-image in `before`, and writes no outbox row.
- **FR-F068-10:** `list` is keyset paginated against the F028 signed cursor. `PageRequest { cursor: Option<SignedCursor>, limit: Limit, sort: SortKey, order: Order }` with `Limit` clamped to 1–200 default 50; the cursor payload is `{ table, tenant_id, sort_value, id, order, filter_hash: [u8; 32], issued_at }` signed HMAC-SHA256 with the 24-hour expiry of FR-F028-04. The predicate is `and (sort_col, id) > ($k, $id)` — never `offset` — and `sort_col` must be a member of `S::SORTABLE` or the call is `RepoError::InvalidSort`. A cursor whose `table`, `tenant_id`, `order`, or `filter_hash` differs from the current call is `RepoError::InvalidCursor`, so a cursor cannot be replayed against another tenant, filter, or table. The result is `Page<T> { items, next_cursor, has_more }`, matching FR-F028-05.
- **FR-F068-11:** `UnitOfWork` owns the transaction. `UnitOfWork::begin(db: &Database, ctx: TenantCtx) -> Result<Self, RepoError>`, `fn repo<S: RepositorySpec>(&mut self) -> BaseRepository<'_, S>`, `async fn commit(self) -> Result<Committed, RepoError>`, `async fn rollback(self) -> Result<(), RepoError>`. Because `repo` borrows `&mut self`, only one repository handle exists at a time and the handles are used in sequence on one transaction; `commit` and `rollback` take `self` by value, so a repository handle cannot outlive the transaction. Replacing a user and its group memberships is `let mut uow = UnitOfWork::begin(&db, ctx).await?; uow.repo::<UserSpec>().update(..).await?; uow.repo::<GroupMemberSpec>().insert(..).await?; uow.commit().await?;`.
- **FR-F068-12:** A repository behaves differently only in where it gets its connection, and it never opens a transaction it was handed one for. `Db<'a>` is a private enum `Pool(&'a PgPool) | Tx(&'a mut PgConnection)`. `Database::repo::<S>()` yields a `Db::Pool` handle whose every mutating method opens one transaction, performs the write, the audit row, and the outbox row, and commits before returning, so a single-aggregate write needs no ceremony. `UnitOfWork::repo::<S>()` yields a `Db::Tx` handle; `BaseRepository` has no `begin`, `commit`, `rollback`, or `savepoint` method at all, so on the unit-of-work path the outbox row is in the caller's transaction by construction and a rollback removes the write, the audit row, and the event together.
- **FR-F068-13:** Beyond the contract a class exposes named, intention-revealing queries and nothing else. `crates/persistence/src/users/queries.rs` adds `impl UserRepository { async fn find_by_email(&self, ctx: &TenantCtx, email: &Email) -> Result<Option<User>, RepoError>; async fn list_active_in_group(&self, ctx: &TenantCtx, group: GroupId, page: PageRequest) -> Result<Page<User>, RepoError>; async fn count_by_status(&self, ctx: &TenantCtx) -> Result<StatusCounts, RepoError>; }`, each built from `self.select(pred)` or `self.select_page(pred, page)` so the tenant predicate and soft-delete filter still apply. There is no `query(sql)`, `execute(sql)`, `raw`, `sql`, `fetch_all`, `pool()`, or `Deref<Target = PgPool>` anywhere in the crate's public surface, and `crates/persistence/src/lib.rs` re-exports no SQLx type.
- **FR-F068-14:** `cargo xtask check-persistence [--json] [--baseline <file>]` enforces six rules and reports every violation. `persist.raw_sql`: outside `crates/persistence/src/**` and `services/api/migrations/**`, no `sqlx::query`, `query!`, `query_as`, `query_scalar`, `query_file`, and no string literal matching `(?is)\b(select\s|insert\s+into|update\s+\w+\s+set|delete\s+from|create\s+table|alter\s+table|with\s+\w+\s+as)\b`. `persist.connection_type`: the identifiers `PgPool`, `PgPoolOptions`, `PgConnection`, `PgRow`, `PgArguments`, `sqlx::Transaction`, `sqlx::Executor`, and `sqlx::Acquire` appear only under `crates/persistence/**`, and `lib.rs` exports none of them. `persist.escape_hatch`: no `pub fn` in the crate is named `query`, `execute`, `exec`, `raw`, or `sql`, and none takes a `&str` parameter named `sql`. `persist.table_unmapped` and `persist.table_double_write`: every table in the `Tables` and `Persistence` columns of `docs/capability-contracts.md` appears in exactly one specification's `TABLE` or `CO_TABLES`, and never in two. `persist.array_column`: no `create table` or `add column` in `services/api/migrations/**` declares an array type. `persist.jsonb_unlisted`: every `jsonb` column has a `crates/persistence/schema-policy.toml` entry naming its decision-section-2 category, its owning feature, and a reason.
- **FR-F068-15:** `schema-policy.toml` is the only allow-list and starts with exactly the categories decision section 2 permits: typed cell values (`cells.value`), view and widget settings (`tenants.settings`, `views.config`, `sheet_user_layouts.layout`), event payloads (`outbox_events.payload`, `notifications.payload`, `workflow_run_steps.payload`), provider response snapshots (`integration_connections.last_error`, `integration_events.detail`), and diffs (`audit_events.before`, `audit_events.after`, `audit_events.field_diff`). An entry whose column no longer exists is `persist.policy_stale`. The gate grants no exemption for tickets written before the decision: `integration_connections.capabilities`, `.scopes`, `.missing_scopes`, and `oauth_tokens.granted_scopes` in the F029 ticket are reported as `persist.array_column` with the owning feature id, and F029 cannot release until they become child tables.
- **FR-F068-16:** Output follows the F041 rules exactly: one line per finding on stderr as `BLOCKED: <code> <path>:<line>: <message>` sorted by path, then line, then code; `check-persistence passed (<n> items)` on stdout with exit `0`; `check-persistence failed: <n> findings` with exit `1`; a usage or I/O error on stderr with exit `2`; and `REFUSED: persist.baseline_widened <code> <path>` with exit `3` when a run adds a finding that `--baseline` does not already record, or when `--write-baseline` runs without `XTASK_ROLE=maintainer`. `--json` prints exactly one object `{ command, ok, checked, findings: [{ code, path, line, message }], duration_ms }` on stdout. Output is ASCII, honours `NO_COLOR`, and no line exceeds 200 characters.

### Non-functional requirements

- **NFR-F068-01 Performance:** the base adds no round trip a hand-written statement would not make — `insert` is one batch of three statements on one connection, `update` is one statement plus a re-read only when zero rows were affected, and `list` is one statement. `check-persistence` completes in under 2 seconds over the whole repository on `ubuntu-latest` with 2 vCPU, reading each file once and streaming files larger than 1 MiB. Keyset pagination over 100,000 `users` rows returns any page in under 30 ms p95 using `users(tenant_id, status, display_name)`, and page 2,000 costs the same as page 2 because there is no `offset`.
- **NFR-F068-02 Security and tenant isolation:** no statement leaves the crate without `tenant_id = $1` bound from `TenantCtx`; cross-tenant reads and writes return `NotFound`; the crate compiles with `#![forbid(unsafe_code)]` and `#![deny(missing_docs)]` on public items; `RepoError`'s `Display` never contains a row value, an email, or a bound parameter, only the aggregate, the operation, and the version numbers; and `Debug` for `TenantCtx` and `WriteCtx` redacts the idempotency key. `check-persistence` reads only regular files under the repository root, makes no network call, and executes nothing.
- **NFR-F068-03 Accessibility of the operator surface:** the gate has no UI, so its accessible surface is its output. Findings name the file and line so navigation needs no visual diff scanning; state is words, never colour or symbols; `--json` is a complete structural equivalent of the text output; `crates/persistence/README.md` documents the four-step recipe for adding a repository with a heading per step and plain-text tables that read in order.
- **NFR-F068-04 Reliability and observability:** every mutation emits a `tracing` span `persistence.{aggregate}.{op}` with `tenant_id`, `correlation_id`, `version`, and `rows_affected`, and metric `repository_operations_total{aggregate,op,outcome}` plus histogram `repository_operation_duration_seconds{aggregate,op}`; the audit row and the outbox row are proven atomic with the write by a rollback test on every registered specification; two runs of `check-persistence` over an unchanged tree produce byte-identical output.
- **NFR-F068-05 Conformance for every repository:** the rules that cannot be sealed by a type are proven for every specification rather than for a sample. Each `RepositorySpec` implementation is collected into a link-time registry, `check-persistence` reports `persist.table_unmapped` for a table with no registered specification, and `testing/features/F068/database/conformance_tests.rs` runs the same eight-case suite — cross-tenant read, cross-tenant write, soft-delete filter, version conflict, audit row present, outbox row present, rollback atomicity, cursor rejection — against every entry in that registry, so adding a repository adds its own proof.

### Scope

Included: the sealed `Repository` contract and its single `BaseRepository` implementation; `RepositorySpec` and the `Binder`, `Predicate`, and `Column` types; tenant, soft-delete, version, audit, and outbox application; `UnitOfWork` and the pool-versus-transaction handle; the signed-cursor keyset pagination built on F028's `SignedCursor`; `RepoError` and its mapping contract; the worked `UserRepository` over F002's `users` table with three named queries; `crates/persistence/schema-policy.toml`; `cargo xtask check-persistence` with its six rules, baseline, and exit codes 0/1/2/3; the conformance registry; and the harness under `testing/features/F068/`.

Excluded: the connection pool, configuration, and secret loading in `crates/persistence/src/runtime/**` (F004, which this feature consumes and never edits); the `outbox_events`, `job_runs`, and `dead_letters` tables and the publisher that drains them (F004); the `audit_events` table, roles, and policy engine (F003); the `tenants`, `users`, `groups`, and `group_members` migrations and their HTTP surface (F002); the `SignedCursor` type, `ListQuery` parsing, and OpenAPI generation (F028); the retention and purge job that calls `purge` (F027); and every aggregate repository other than `UserRepository` — each later feature adds its own specification under `crates/persistence/src/<aggregate>/` and claims that path in its own ticket.

## 3. UX specification

No UI. The developer surface is a crate recipe and one command.

- Entry points: `cargo xtask check-persistence`, `cargo xtask check-persistence --json`, `cargo xtask check-persistence --baseline testing/fixtures/persistence/baseline.json`, and the crate documentation in `crates/persistence/README.md`.
- Primary flow: a developer adding an aggregate writes four things — a `RepositorySpec` implementation, a `Filter` type, `map_row`, and any named queries — then `pub type SheetRepository = BaseRepository<'static, SheetSpec>;`. They write no `where` clause, no `tenant_id`, no `version`, no audit call, and no outbox call, because none of those are theirs to write.
- Success: `check-persistence passed (94 items)` on stdout, exit 0.
- Findings: `BLOCKED: persist.raw_sql services/api/src/tenants/handlers_user.rs:118: SQL string literal outside crates/persistence`, then `check-persistence failed: 3 findings`, exit 1.
- Refused: `REFUSED: persist.baseline_widened persist.array_column services/api/migrations/20260401_integrations_create_tables.sql` after the full finding list, exit 3, no baseline written.
- Compile-time refusal: a hand-written `impl Repository for MyRepository` prints `error[E0603]: module 'sealed' is private` and the crate does not build; the message is captured verbatim in the `trybuild` expectations under `testing/features/F068/api/ui/`.
- Error and empty: an unreadable file, an unparseable catalog table, or an unknown flag prints the reason on stderr with exit 2; a tree with no migrations reports `skipped: no migrations to scan` for the column rules and still runs the other four.
- Keyboard and responsive: not applicable; output is line-oriented and wraps at 100 columns.

## 4. Technical specification

### Rust backend

Canonical contract: aggregate `repository`; module `persistence`; surface `crates/persistence/**`, `cargo xtask check-persistence`, and the `Repository` and `UnitOfWork` contracts; events none; every table in the catalog reached only through its repository class; role maintainer.

- `crates/persistence/src/lib.rs`: `#![forbid(unsafe_code)]`, module declarations, and the public surface — `Repository`, `RepositorySpec`, `BaseRepository`, `UnitOfWork`, `Database`, `TenantCtx`, `WriteCtx`, `PurgeCtx`, `PurgeGrant`, `PageRequest`, `Page`, `Limit`, `SortKey`, `Order`, `Version`, `Visibility`, `Predicate`, `Comparison`, `Op`, `EventName`, `RepoError`. No SQLx type is re-exported.
- `repository/mod.rs`: the sealed trait of FR-F068-01 and FR-F068-02, the private `sealed` module, and `Op { Insert, Update, SoftDelete, Restore, Purge }`.
- `repository/spec.rs`: `RepositorySpec` per FR-F068-03, plus `Binder<'_>` wrapping `sqlx::QueryBuilder` so a specification binds values without composing text, and `Column<S>` whose only constructor `Column::<S>::new(name)` returns `None` unless `name` is in `S::COLUMNS`.
- `repository/filter.rs`: `Predicate { fn comparisons(&self) -> Vec<Comparison<Self::Spec>> }`, `Comparison { column, op: Cmp::{Eq, Ne, Lt, Lte, Gt, Gte, In, Contains, IsNull}, value: Value }`, and `filter_hash` — a SHA-256 over the sorted comparisons that binds a cursor to its filter.
- `repository/base.rs`: `BaseRepository<'a, S>` holding `Db<'a>` and the scoped statement builders `select`, `select_page`, `insert_returning`, `update_returning`, `delete_scoped`; the audit and outbox writers; the version-conflict re-read; and the single `Repository` implementation. Under 500 lines by splitting the writers into `repository/audit.rs` and `repository/outbox.rs`.
- `repository/cursor.rs`: encode and decode over F028's `SignedCursor`, with the payload, expiry, and mismatch rules of FR-F068-10.
- `uow/mod.rs`: `Database { pool: PgPool }` from F004's `PgPoolBuilder`, `UnitOfWork`, `Db<'a>`, and `Committed { events: u32, audits: u32 }`.
- `users/mod.rs`, `users/spec.rs`, `users/queries.rs`: `UserSpec` with `TABLE = "users"`, `AGGREGATE = "user"`, `COLUMNS = ["id", "tenant_id", "email", "display_name", "status", "external_id", "last_login_at", "version", "created_by", "created_at", "updated_by", "updated_at", "deleted_at"]`, `SORTABLE = ["display_name", "created_at", "updated_at"]`, `CO_TABLES = []`; `UserFilter { status, email, group_id, created_after }`; `NewUser`, `UserPatch`; `pub type UserRepository = BaseRepository<'static, UserSpec>;` and the three named queries of FR-F068-13. `find_by_email` uses F002's `users_tenant_email_idx` partial unique index and the `citext` column type, so it is case-insensitive without a `lower()` wrapper.
- `RepoError { NotFound, VersionConflict { expected, actual }, InvalidCursor, InvalidSort, Forbidden, Constraint { name }, Unavailable }`; the API layer maps `VersionConflict → 409 conflict`, `NotFound → 404 not_found`, `InvalidCursor` and `InvalidSort → 400 invalid` with `field_errors.cursor` and `field_errors.sort`, `Forbidden → 403 denied`, `Constraint → 400 invalid`, `Unavailable → 503`, matching decision section 3.
- `automation/xtask/src/persistence.rs`: `check_persistence(args) -> Result<(), String>` with `scan_sources`, `scan_migrations`, `scan_specs`, `catalog_tables`, `Policy` (serde model of `schema-policy.toml`), and `Baseline`. It reuses F041's `support::{OutputFormat, report}` reporter and adds no dependency beyond `toml`, already in the workspace. Production call path: dispatched from `automation/xtask/src/main.rs` as `Some("check-persistence") => persistence::check_persistence(args)`, a one-line addition made under the F041 owner's review at integration, and run as a step in `.github/workflows/gates.yml` owned by F001; `crates/persistence/README.md` carries both lines verbatim so each edit is mechanical.

### PostgreSQL/SQLx

- No migration. This feature creates no table, no index, and no `services/api/migrations/*_persistence_*.sql` file; `cargo xtask check-migrations` reports the same file count before and after the branch. It reads the schema F002, F003, and F004 already own.
- Tables written by the base on behalf of every repository: `audit_events` (F003) for each of the five operations, and `outbox_events` (F004) for the four published operations. The one schema requirement this feature places on F004 is the unique index `outbox_events_tenant_idempotency_idx on outbox_events (tenant_id, idempotency_key) where idempotency_key is not null`, which FR-F068-08 depends on; it is recorded in `crates/persistence/README.md` and asserted by `testing/features/F068/database/schema_expectations_tests.rs` so its absence fails this feature rather than silently disabling idempotency.
- Worked table: `users(id uuid pk, tenant_id uuid not null references tenants(id), email citext not null, display_name text not null, status text not null default 'invited', external_id text, last_login_at timestamptz, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)` from F002 — every column the base needs is already present, which is the point of decision section 2's row shape.
- Statement shapes are fixed and asserted: `insert` is `insert into users (...) values (...) returning ...` followed by the audit insert and the outbox insert on the same connection; `update` is the single statement of FR-F068-05; `list` is `select ... where tenant_id = $1 and deleted_at is null and (display_name, id) > ($2, $3) order by display_name, id limit $4`. Isolation is `read committed`; the version predicate, not a lock, provides the concurrency control, and two concurrent updates leave exactly one `VersionConflict`.
- Column policy: `check-persistence` parses `create table` and `alter table ... add column` in `services/api/migrations/**` for array types and `jsonb` columns and matches them against `crates/persistence/schema-policy.toml`; the initial policy file lists the eleven columns of FR-F068-15 and nothing else.
- Rollback: this feature adds no schema, so rollback is removing the crate modules and the gate; the data it wrote through `audit_events` and `outbox_events` belongs to F003 and F004 and is unaffected.

### React/TypeScript

No UI, no component, no client, and no route. `apps/web/` is untouched and `openapi/v1.json` is byte-identical across this branch, because a repository has no HTTP surface — it is reached only through the handlers other features own. The rendered surfaces delivered in place of a component tree are `crates/persistence/README.md` (the four-step recipe, the statement shapes, the `main.rs` dispatch line, and the `gates.yml` step), `crates/persistence/schema-policy.toml`, and the two renderings of the gate output required by FR-F068-16 — the `BLOCKED:` text form and the single JSON object — which follow the F041 output rules and are tested for parity in `testing/features/F068/frontend/cases.md`.

### Interim specification gate

- `cargo xtask check-persistence` already exists in `automation/xtask/src/persistence.rs` as the specification-level precursor to the runtime gate above, and runs today against the backlog rather than against code that does not exist yet. It enforces three of the rules over every ticket: `persist.array_column` for an array column declared in a DDL line, `persist.jsonb_unjustified` for a ticket keeping `jsonb` without describing it as a payload, and `persist.table_unmapped` for a feature that owns catalog tables but names no repository class. The remaining rules — `persist.raw_sql`, `persist.connection_type`, `persist.escape_hatch`, `persist.table_double_write` — need source files and are delivered by T271, which replaces this implementation rather than adding a second one.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F068-01 through FR-F068-16 and NFR-F068-01 through NFR-F068-05 in `testing/features/F068/requirements/cases.md`
- [ ] Compile-fail tests (`trybuild`, no database): hand-written `impl Repository`, a specification returning SQL text, a `Column` from a foreign specification, holding two repository handles on one `UnitOfWork`, using a `UnitOfWork` after `commit`, and constructing a `PurgeCtx` without a `PurgeGrant`
- [ ] Static gate tests (no database): the six rules of FR-F068-14 over fixture trees, plus baseline widening, exit codes, ordering, and JSON shape
- [ ] Database tests on a throwaway PostgreSQL 18: tenant predicate, soft-delete filter, version conflict, audit and outbox atomicity, idempotent replay, keyset pagination stability, purge with children
- [ ] Conformance suite: the eight cases of NFR-F068-05 run against every specification in the link-time registry
- [ ] Permission-negative tests: cross-tenant `get`, `update`, `soft_delete`, and `purge` all return `NotFound`; `purge` without the `purge:user` scope returns `Forbidden`; a cursor minted for tenant A rejected on tenant B
- [ ] Frontend negative controls: text and JSON output parity, `NO_COLOR`, line width, and `apps/web/` plus `openapi/v1.json` unchanged
- [ ] Database negative controls: no migration added by this feature, and the `outbox_events` idempotency index asserted rather than created
- [ ] Accessibility tests: ASCII-only output, findings carry path and line, JSON structural equivalence, README heading and table structure
- [ ] Performance tests: gate under 2 s over the repository, page 2,000 as fast as page 2 over 100,000 rows, no extra round trip per mutation

### Fast fanout configuration

- Test harness path: `testing/features/F068/`
- Feature flag: `F068_FEATURE`
- Fixture/seed factory: `testing/fixtures/persistence/` — `trees/{clean,raw_sql,connection_leak,escape_hatch,double_write,unmapped_table}/` source trees for the static rules, `migrations/{arrays,jsonb_listed,jsonb_unlisted,stale_policy}/*.sql` for the column rules, `catalog/{matching,missing_table}.md` catalog excerpts, `baseline.json`, and `seed.rs` which inserts tenants A and B with 3 and 100,000 users on a fixed UUIDv7 sequence
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seed sequence, fixed HMAC key for cursor signing, integer versions starting at 1
- Mock/stub contracts: none for the static rules, which read files only; the database lane starts one `postgres:18` container per test session, creates database `opshub_f068_w{worker}` per worker, applies F002's `*_tenants_*.sql`, F003's `*_authz_*.sql`, and F004's `*_runtime_*.sql`, and drops the database at teardown; a session that cannot reach Docker fails the lane rather than skipping it
- Parallel isolation: one database per worker, one tenant id per test, one temporary tree per static case, no shared port
- Targeted command: `cargo xtask test-feature F068`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F068/` holding the gate JSON, the `trybuild` expectations, the conformance matrix per specification, and the pagination timings

## 6. Acceptance criteria

```gherkin
Feature: Repository contract, unit of work, and the persistence gate

Scenario: A repository cannot forget the rules because it cannot be written by hand
  Given a developer writes impl Repository for MyRepository in crates/domain
  When cargo build --workspace runs
  Then compilation fails with "module 'sealed' is private"
  And the only path to the trait is BaseRepository over a RepositorySpec, which always binds tenant_id and filters deleted_at

Scenario: An update under the wrong version conflicts and changes nothing
  Given a user at version 4 in tenant A
  When update is called with expected version 3
  Then the result is VersionConflict with expected 3 and actual 4
  And no audit row and no outbox row were written

Scenario: The outbox row lives or dies with the write
  Given a UnitOfWork that updates a user and then inserts a group member that violates a constraint
  When the unit of work is rolled back
  Then users, audit_events, and outbox_events all have their original row counts
  And no event reaches the publisher

Scenario: A cursor cannot be replayed against another tenant or filter
  Given a page of users listed for tenant A with filter status equals active
  When the returned cursor is presented with tenant B, or with filter status equals invited
  Then the result is InvalidCursor and no row is returned

Scenario: The gate refuses SQL and array columns wherever they appear
  Given a handler in services/api/src/tenants that contains the literal "select id from users"
  And a migration that declares scopes text[]
  When cargo xtask check-persistence --json runs
  Then the findings array contains persist.raw_sql with that file and line
  And it contains persist.array_column naming the migration and the owning feature
  And the exit code is 1

Scenario: Every registered repository proves the rules it cannot be sealed into
  Given the link-time registry of RepositorySpec implementations
  When the conformance suite runs against a throwaway PostgreSQL 18
  Then each specification passes cross-tenant read, cross-tenant write, soft-delete filter, version conflict, audit row, outbox row, rollback atomicity, and cursor rejection
  And a table in the catalog with no registered specification is reported as persist.table_unmapped
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F001 (the Cargo workspace, the `crates/persistence` member, the pinned toolchain, and the CI job this gate joins); decisions sections 1, 2, 2.1, 3; contracts row F068
- Reads but never edits: F004's `crates/persistence/src/runtime/**` pool builder and its `outbox_events` table, F003's `audit_events` table, F002's `users` schema, F028's `SignedCursor` and `Page` conventions. F002, F003, F004, and F028 are ahead of this feature in the plan; until they land, the harness applies their committed migrations and links their types, and the two contracts this feature places on them — the `outbox_events` idempotency index and `SignedCursor` accepting a repository payload — are asserted, not created, so a drift fails here.
- Blocks: nothing formally; every later feature adds its own `crates/persistence/src/<aggregate>/` specification, and `persist.table_unmapped` is the reminder that its table has no data access class yet
- Conflicts with: none. F004 owns `crates/persistence/src/runtime/**`; the paths claimed here are disjoint from it and from `crates/*/Cargo.toml`, which F001 owns
- External dependencies: Docker with `postgres:18` for the database lane; `trybuild` for the compile-fail lane; `toml` for the policy file — all already available to CI
- Risks and mitigations: the sealed trait makes mocking harder for callers, mitigated by the domain depending on narrow per-aggregate traits it defines itself with a thin adapter in this crate, so a unit test substitutes a plain struct without touching `Repository`; a specification could still smuggle a predicate through `map_row`, mitigated by `map_row` receiving a `PgRow` and returning an entity with no query access; the six static rules are text and AST scans that can be evaded by string concatenation, mitigated by the conformance suite and by `persist.connection_type`, which removes the executor a concatenated statement would need; the array-column rule invalidates columns already specified in the F029 ticket, which is intended and recorded in FR-F068-15 rather than exempted; a throwaway container per session is slow on a cold runner, mitigated by one container for the whole session and one database per worker
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration status (none), and rollback procedure.

## 8. Entry criteria — ready for implementation

- [ ] F001 accepted and archived, with `crates/persistence` a workspace member on the pinned Rust 2024 toolchain
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F068/`
- [ ] F002, F003, and F004 migrations available to the harness so the database lane can apply `users`, `audit_events`, and `outbox_events`
- [ ] Owned paths claimed and disjoint from `crates/persistence/src/runtime/**`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Compile-fail, static gate, database, conformance, permission-negative, accessibility, and performance lanes pass
- [ ] `UserRepository` is consumed by a production call path: `services/api/src/tenants/` uses it for `GET /api/v1/users`, `POST /api/v1/users`, and `PATCH /api/v1/users/{id}`, and an integration test proves the audit and outbox rows for each
- [ ] `cargo xtask check-persistence` exits 0 over the repository, is dispatched from `main.rs`, and runs in `gates.yml`
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F068_FEATURE`, revert the gate step, confirm no schema change to revert
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Every table in OpsHub is now reached through exactly one data access class in `crates/persistence`. The shared `Repository` contract applies the tenant predicate, the soft-delete filter, the optimistic version check, the audit row, and the transactional outbox row for `get`, `list`, `insert`, `update`, `soft_delete`, `restore`, and `purge`, and it is sealed so a second implementation does not compile. `UnitOfWork` threads one transaction through several repositories, and a repository handed a transaction never opens its own.
- `cargo xtask check-persistence` fails the build on SQL, a pool, or a connection type outside `crates/persistence/**`, on a table with no repository or two repositories, on an array column, and on a `jsonb` column missing from `crates/persistence/schema-policy.toml`.
- No schema change and no rollback step. The feature is off by default behind `F068_FEATURE`.
