---
id: F004
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E001
depends_on: [F001]
blocks: [F005, F010, F017, F037, F019, F046, F028]
conflicts_with: []
parallel_safe: true
owned_paths: [infra/**, services/worker/src/**, services/api/src/runtime/**, services/realtime/src/runtime/**, crates/events/src/runtime/**, crates/persistence/src/runtime/**, services/api/migrations/*_runtime_*.sql, testing/features/F004/**]
feature_flag: F004_FEATURE
flag_default: off
branch: f004-runtime-operations
started_at: null
finished_at: null
---

# F004 — Runtime operations

## 1. Identity and dates

- Branch: `f004-runtime-operations`
- Capability area: platform runtime (spec section 3 architecture, section 6 reliability and observability, 5.5 AUTO-03 queue bullet, 5.8 secrets bullet, section 10 PostgreSQL 18 decision)
- Module slug: `runtime`

### Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 7, 9
- Canonical contract: `docs/capability-contracts.md` row F004

- Design: this feature has no user surface; it ships tooling, runtime or contracts only.

## 2. Requirement specification

### Problem and user outcome

The workspace builds (F001) but nothing runs. Every service needs the same reproducible runtime: containers and a compose file that boots PostgreSQL 18, NATS JetStream, MinIO, and Mailpit alongside the API, worker, realtime, and web images; typed configuration with secrets resolved from a secret manager; a transactional outbox that publishes domain events to JetStream without losing writes; a durable job transport with per-tenant quotas, bounded retries, and dead letters consumed by a worker skeleton; tracing, metrics, health, and readiness; and backups with point-in-time recovery proven by a restore drill.

As an operator, I want `docker compose up` to produce a healthy stack, `/readyz` to tell me exactly which dependency is failing, every job to be retried and dead-lettered visibly, and a documented restore that I have actually run, so that later features can rely on events and jobs and I can recover from data loss.

### Functional requirements

- **FR-F004-01:** `docker compose -f infra/compose/docker-compose.yml up -d` on a clean machine brings `postgres` (image `postgres:18` with `wal_level=replica`, `archive_mode=on`, healthcheck `pg_isready`), `nats` (`nats:2` with `--jetstream --store_dir /data`), `minio` (with `minio-init` creating buckets `opshub-files`, `opshub-backups`, `opshub-documents`), `mailpit` (SMTP 1025, UI 8025), `api`, `worker`, `realtime`, and `web` to `healthy` within 120 seconds, and `docker compose ps --format json` reports `Health = healthy` for all eight services.
- **FR-F004-02:** Every service loads `RuntimeConfig` from environment variables prefixed `OPSHUB_` (database URL, NATS URL, object storage endpoint and buckets, SMTP host, OTLP endpoint, metrics port, RP id, base URL, worker id) with validation at startup; a missing or malformed value exits with code 78 (`EX_CONFIG`) and one log line naming the variable, never its value; `infra/compose/.env.example` lists every variable with a comment.
- **FR-F004-03:** Any config value of the form `secret://<name>` is resolved through the `SecretSource` trait with `file`, `env`, and `vault`-compatible (KV v2 HTTP) backends selected by `OPSHUB_SECRET_SOURCE`; resolved secrets implement `Debug` as `[redacted]`, are excluded from the tracing `fields`, and the log redaction layer replaces any occurrence of a resolved secret with `[redacted]`.
- **FR-F004-04:** Multi-stage Dockerfiles `infra/docker/{api,worker,realtime,web}.Dockerfile` produce distroless images running as uid 65532 with a read-only root filesystem, no shell, `SOURCE_DATE_EPOCH`-pinned layers, an `OCI` label with the git SHA, and pass `docker run --rm <image> --version` printing the crate version.
- **FR-F004-05:** `crates/events::runtime::enqueue(tx, OutboxEvent)` calls `OutboxRepository::enqueue` on the caller's `UnitOfWork`, which writes `outbox_events` inside the caller's transaction with `{ id uuidv7, tenant_id, aggregate, aggregate_id, event_name, version, payload, correlation_id, occurred_at }`; `event_name` must match `^[a-z-]+\.[a-z-]+\.v[0-9]+$` or the call fails at compile time through the `EventName` const constructor and at runtime with `OutboxError::InvalidName`.
- **FR-F004-06:** The worker outbox relay polls every 200 ms through `OutboxRepository::claim_unpublished_batch`, whose `SELECT ... FOR UPDATE SKIP LOCKED LIMIT 500` ordered by `id` lives in `crates/persistence` and is the only place that statement appears, publishes each row to JetStream stream `OPSHUB_EVENTS` subject `events.<tenant_id>.<event_name>` with header `Nats-Msg-Id = <outbox id>` for server-side deduplication (window 2 minutes), sets `published_at` on acknowledgement, increments `attempts` and stores `last_error` on failure, and never deletes or skips an unpublished row; after each non-empty batch it publishes `outbox.published.v1` with `{ batch_size, oldest_occurred_at, lag_seconds }`.
- **FR-F004-07:** 10,000 unpublished outbox rows drain within 60 seconds with one relay instance; two relay instances running concurrently publish each row exactly once (verified by `Nats-Msg-Id` dedupe plus `published_at` idempotency).
- **FR-F004-08:** Jobs implement `trait Job { const KIND: &'static str; type Payload; async fn run(ctx: JobContext, payload) -> Result<(), JobError> }` and are enqueued with `enqueue_job(tx, kind, tenant_id, payload, options { max_attempts ≤ 5, timeout, idempotency_key })` which writes `job_runs` (status `queued`) and publishes to stream `OPSHUB_JOBS` subject `jobs.<tenant_id>.<kind>` in the same outbox transaction.
- **FR-F004-09:** The worker consumes `OPSHUB_JOBS` with a durable pull consumer, enforces per-tenant quotas (default 100 concurrent and 1,000 per minute, configurable per kind), records `job_runs.status` transitions `queued → running → succeeded|failed|dead` with `started_at`, `finished_at`, `worker_id`, `attempt`, and `error`, retries failed runs with exponential backoff 1 s, 5 s, 25 s, 2 m, 5 m (max 5 attempts), enforces the per-kind timeout by cancelling the future, and moves exhausted runs to `dead_letters` while publishing nothing further.
- **FR-F004-10:** Killing the worker process (`SIGKILL`) mid-run redelivers the job to another worker within 30 seconds with the same `job_id` and `attempt + 1`; `SIGTERM` stops fetching, drains in-flight jobs for up to 30 seconds, then exits 0; handlers receive `JobContext.idempotency_key` and the harness proves a duplicate delivery produces no second side effect.
- **FR-F004-11:** A `dead_letters` row can be replayed through the worker CLI `opshub-worker replay --id <uuid>` which re-enqueues with `attempt = 1`, sets `replayed_at`, and refuses (exit 65) when the row was already replayed.
- **FR-F004-12:** Every request and job runs inside a `tracing` span carrying `tenant_id`, `actor_id`, `correlation_id`, `service`, and `worker_id` where applicable; `X-Correlation-Id` is honoured when present (UUID) or generated as UUIDv7 and echoed in the response; spans export through OTLP gRPC to `OPSHUB_OTLP_ENDPOINT` with `service.name`, and logs are JSON lines with the same ids.
- **FR-F004-13:** `GET /metrics` on the dedicated port `OPSHUB_METRICS_PORT` (default 9464, not exposed through the public ingress or the `web` proxy) serves Prometheus text with `http_request_duration_seconds{route,method,status}`, `outbox_publish_lag_seconds`, `outbox_pending_events`, `job_run_duration_seconds{kind}`, `job_runs_total{kind,status}`, `dead_letters_total{kind}`, `db_pool_in_use`, `db_pool_idle`, `nats_connected`; a request to `/metrics` on the API port returns `404 not_found`.
- **FR-F004-14:** `GET /healthz` returns `200 {"status":"ok"}` whenever the process is serving; `GET /readyz` returns `200` with `{ status: "ok", components: { database, nats, object_storage, outbox } }` where each component carries `{ state: ok|degraded|unreachable, latency_ms }` so an operator can see which dependency is slow rather than only that something is, when `PgHealthProbe::ping` completes within 500 ms, the NATS connection is `connected`, `HEAD` on `opshub-files` succeeds, and outbox lag is under 60 seconds, and otherwise `503 unavailable` with the failing components marked `"error"` and a reason; both routes are unauthenticated and exempt from the tenant gate and rate limits.
- **FR-F004-15:** `infra/backup/backup.sh` takes a nightly `pg_basebackup` and continuous WAL archive to `opshub-backups` with 30-day retention; `infra/backup/restore.md` documents point-in-time recovery; `make restore-drill` restores the latest base backup plus WAL to a scratch database at a target timestamp, runs `SELECT count(*)` on `tenants`, `users`, `outbox_events`, and compares against the recorded manifest, exiting non-zero on mismatch.
- **FR-F004-17:** Telemetry has a stated lifetime and a closed field list, because logs are the copy of customer data nobody remembers to delete. Structured logs are kept 30 days hot and 1 year in cold storage, traces 7 days, metrics 15 months at reducing resolution, all enforced by retention policy on the sink rather than by intention. A log line may carry `tenant_id`, `actor_id`, `correlation_id`, resource ids, route templates, status, duration and error class — and never a cell value, comment body, file name, email address beyond its domain, token, secret, or request or response body. The redaction list is shared with F027 so one change covers exports, audit diffs and logs together, and a test asserts a seeded secret and a seeded cell value appear in neither the log sink nor a trace span. Personal data in telemetry is deleted by tenant on the F027 purge path, so a deletion request is not silently incomplete because the rows survive in logs.
- **FR-F004-16:** A request that reaches a handler without a gateway `ActorContext` (for example an internal route called without credentials) cannot enqueue a job: `enqueue_job` requires `tenant_id` from the context and returns `JobError::MissingTenant`; the harness proves no `job_runs` row is created.

### Non-functional requirements

- **NFR-F004-01 Performance:** `/readyz` responds in under 50 ms p95 with warm connections; outbox publish lag stays under 2 seconds p95 at 200 events per second (spec section 6 async acknowledgement target); the worker sustains 500 jobs per second across 4 instances with `job_run_duration_seconds` overhead under 5 ms per job.
- **NFR-F004-02 Security/privacy:** images run non-root and read-only; secrets never appear in logs, traces, `Debug`, or `/readyz` output; `/metrics` is network-isolated; NATS uses per-service credentials with subject permissions (`api` publish-only on `events.>` and `jobs.>`, `worker` consume on both, `realtime` consume on `events.>`); backups in `opshub-backups` are server-side encrypted.
- **NFR-F004-03 Accessibility:** operator-facing output is usable without colour or a screen: `/readyz` JSON and CLI output use words (`ok`, `error`) not colour alone, respect `NO_COLOR`, and the runbooks in `infra/backup/` use heading hierarchy and plain-text tables readable by screen readers.
- **NFR-F004-04 Reliability/observability:** no committed write loses its event (outbox rows are never deleted before `published_at`); dead letters are visible through metrics and the CLI; the restore drill runs in CI weekly and stores evidence under `testing/evidence/F004/`; alert rules in `infra/alerts/rules.yml` fire on `outbox_pending_events > 1000` for 5 minutes, `dead_letters_total` increase, and `/readyz` failure.

### Scope

Included: compose file and service images, `RuntimeConfig` and `SecretSource`, log redaction, the outbox table and relay, JetStream streams and consumers, the job trait, quotas, retries, dead letters, replay CLI, worker skeleton with graceful shutdown, tracing and OTLP export, Prometheus metrics, health and readiness routes, backup scripts, PITR runbook, restore drill, alert rules.

Excluded: workflow-specific job kinds and run history UI (F019), notification delivery (F037), search indexing (F010), realtime session logic (F046), file scanning (F017), production cluster orchestration manifests beyond compose (deployment is out of the first release's scope).

## 3. UX specification

No UI. The operator surface is the compose stack, environment variables, CLI commands, HTTP health routes, and runbooks.

- Entry points: `make up` (wraps `docker compose -f infra/compose/docker-compose.yml up -d --wait`), `make down`, `make logs`, `make restore-drill`; `opshub-worker run`, `opshub-worker replay --id`, `opshub-worker dead-letters --tenant <id>`; `curl :8080/healthz`, `curl :8080/readyz`, `curl :9464/metrics`.
- Primary flow: operator copies `.env.example` to `.env`, runs `make up`, watches `docker compose ps` reach healthy, opens Mailpit at `:8025` and MinIO console at `:9001`, calls `/readyz` and sees every component `ok`, enqueues a sample job with `opshub-worker enqueue-sample`, and sees `job_runs_total{kind="sample",status="succeeded"}` on `/metrics`.
- Loading: `--wait` blocks until healthy or 120 s; Empty: `dead-letters` prints `No dead letters`; Error: `/readyz` 503 JSON names the component and reason; CLI errors go to stderr with a non-zero exit code and no stack trace unless `OPSHUB_LOG=debug`; Success: `make up` prints the service URLs.
- Permission-denied: `/metrics` on the public port is `404`; the worker refuses to start without NATS credentials that grant `jobs.>` consume.
- Responsive and keyboard: not applicable; CLI output is line-oriented and wraps at 100 columns.
- Design tokens: not applicable; CLI honours `NO_COLOR` and uses words for state.

## 4. Technical specification

### Rust backend

- `crates/persistence/src/runtime/`: `RuntimeConfig` (`serde` + `envy`-style loader with `OPSHUB_` prefix), `SecretSource` trait with `FileSecretSource`, `EnvSecretSource`, `VaultKvSecretSource`, `Secret<T>` newtype with redacted `Debug`, `PgPoolBuilder` (max connections, statement timeout 30 s, application name), `RedactionLayer` for `tracing-subscriber`.
- Data access (decision 2.1): `IdempotencyKeyRepository` over `idempotency_keys`, which the F068 base contract calls for every mutation so no feature implements idempotency itself, and `OutboxRepository` (`outbox_events`), `JobRunRepository` (`job_runs`), and `DeadLetterRepository` (`dead_letters`) in `crates/persistence/src/runtime/`, alongside `PgHealthProbe` for the readiness ping; each table is written by exactly one of them. `crates/events`, `services/worker`, `services/api`, and `services/realtime` depend on those repository traits and hold no SQL string, `sqlx::query*` call, or pool of their own — the relay, the sweeper, the replay CLI, and `/readyz` all call named repository queries (`claim_unpublished_batch`, `mark_published`, `record_attempt_failure`, `lag_seconds`, `sweep_stuck_runs`, `list_dead_letters`, `mark_replayed`, `ping`).
- `crates/events/src/runtime/`: `EventName` const constructor, `OutboxEvent`, `enqueue`, `OutboxRelay { poll_interval: 200 ms, batch: 500 }`, `JetStreamPublisher` with `Nats-Msg-Id`, `Job` trait, `JobContext { tenant_id, job_id, attempt, idempotency_key, correlation_id, deadline }`, `enqueue_job`, `JobRegistry`, `RetryPolicy` (1 s, 5 s, 25 s, 2 m, 5 m), `TenantQuota`, `DeadLetterStore`, stream definitions `OPSHUB_EVENTS` (subjects `events.>`, file storage, max age 7 days, dedupe window 2 minutes) and `OPSHUB_JOBS` (subjects `jobs.>`, work-queue retention, `max_deliver 5`, `ack_wait 30 s`).
- `services/worker/src/`: `main.rs` (clap CLI `run`, `replay`, `dead-letters`, `enqueue-sample`, `--version`), `runtime/{bootstrap.rs, consumer.rs, relay_task.rs, shutdown.rs, quota.rs, metrics.rs}`; graceful shutdown on `SIGTERM` drains within 30 s; unique `worker_id` = hostname plus UUIDv7 suffix.
- `services/api/src/runtime/` and `services/realtime/src/runtime/`: `health.rs` (`GET /healthz`, `GET /readyz` with component checks and 500 ms budget), `metrics_server.rs` (separate listener on the metrics port), `telemetry.rs` (OTLP exporter, JSON log layer, `X-Correlation-Id` middleware), `state.rs` wiring pool, NATS client, object storage client.
- Events: `outbox.published.v1` with `{ batch_size, oldest_occurred_at, lag_seconds }` published by the relay; domain events from other features flow through the same relay unchanged.
- Authorization: health routes are public; `/metrics` is protected by network placement; `enqueue_job` requires `tenant_id` from `ActorContext` or a system job marker; the worker CLI is operator-only through host access.
- Error mapping: `ConfigError → exit 78`, `ReadinessError → 503 unavailable`, `OutboxError::InvalidName → 400 invalid` when surfaced through an API, `JobError::MissingTenant → 401 denied`, `ReplayError::AlreadyReplayed → exit 65`.

### Interface

This feature has no product HTTP surface. Its three routes are operational, unauthenticated, exempt
from the tenant gate and the rate limiter, and carry no tenant data. Everything else it ships is a
Rust contract that other features implement against, which is where the detail belongs, so the
signatures section below is the larger half of this specification. Timestamps are RFC 3339 UTC and
unlisted fields are rejected.

`GET /healthz` takes no parameters and returns `200` with exactly `{ "status": "ok" }` whenever the
process is serving. It never consults a dependency: a liveness probe that fails when the database is
slow restarts a healthy process.

**`ReadinessResponse`** — `GET /readyz`

| Field | Type | Notes |
|---|---|---|
| `status` | string | `ok` when every component is `ok`; `error` when any component is not, which is also the `503` case |
| `components` | map<string, ComponentHealth> | exactly four keys, always all four present: `database`, `nats`, `object_storage`, `outbox` |

**`ComponentHealth`** — one entry of that map, so an operator sees which dependency is slow rather
than only that something is (FR-F004-14)

| Field | Type | Notes |
|---|---|---|
| `state` | string | `ok`, `degraded`, or `unreachable`. `degraded` means the probe answered outside its budget but did answer; `unreachable` means it did not answer or errored |
| `latency_ms` | integer | the probe's own measurement, rounded up. Present even when `state` is `unreachable`, where it is the time spent before giving up |
| `reason` | string? | present only when `state` is not `ok`: a short machine-stable phrase, never a driver error string and never a connection URL |

The four probes and their budgets: `database` is `PgHealthProbe::ping` within 500 ms; `nats` is the
client's `connected` flag; `object_storage` is a `HEAD` on the files bucket; `outbox` is
`OutboxRepository::lag_seconds` under 60. The whole handler is budgeted at 500 ms and a probe that
exceeds it is reported rather than awaited. A `200` requires all four `ok`; anything else is `503`
with `status: "error"` and the same body shape, so a client parses one shape either way.

`GET /metrics` serves Prometheus text on the dedicated metrics port only, with no JSON body and no
authentication — it is protected by network placement. The same path on the API port is
`404 not_found`, which is a routing fact, not an authorization one, so it leaks nothing.

**Status codes.** No route here uses `field_errors`, because none takes input.

| Status | Code | Produced by |
|---|---|---|
| 200 | — | `/healthz` while serving; `/readyz` with four `ok` components; `/metrics` on the metrics port |
| 404 | `not_found` | `/metrics` requested on the API port or through the web proxy |
| 503 | `unavailable` | `/readyz` with any component not `ok`; the body names which and why |

Configuration failure is not an HTTP status: a missing or malformed `OPSHUB_` variable exits the
process with code 78 before a listener exists, logging the variable name and never its value.

### Use case signatures

These are the contracts every worker and every mutating feature in the product implements against.
They live in `crates/events/src/runtime/` and `crates/persistence/src/runtime/`; none of them takes a
pool or a connection, and none of them contains SQL.

```rust
pub struct OutboxEvent {
    pub id: Uuid,                  // UUIDv7, also the JetStream `Nats-Msg-Id`
    pub tenant_id: TenantId,
    pub aggregate: &'static str,   // the catalog aggregate, e.g. "tenant"
    pub aggregate_id: Uuid,
    pub event_name: EventName,     // `<aggregate>.<verb>.v1`, const-checked
    pub version: i64,              // the aggregate version this event describes
    pub payload: serde_json::Value,
    pub correlation_id: CorrelationId,
    pub occurred_at: Timestamp,
}

impl EventName { pub const fn new(name: &'static str) -> EventName; }        // compile-time shape check
fn enqueue(uow: &mut UnitOfWork, event: OutboxEvent) -> Result<(), OutboxError>;

pub struct JobContext {
    pub tenant_id: TenantId,
    pub job_id: Uuid,
    pub attempt: u8,               // 1-based; 5 is the last before the dead letter
    pub idempotency_key: Option<String>,
    pub correlation_id: CorrelationId,
    pub deadline: Timestamp,       // the per-kind timeout; the future is cancelled at it
    pub worker_id: WorkerId,
}

trait Job {
    const KIND: &'static str;
    type Payload: serde::de::DeserializeOwned + serde::Serialize;
    async fn run(ctx: JobContext, payload: Self::Payload) -> Result<(), JobError>;
}

fn enqueue_job<J: Job>(uow: &mut UnitOfWork, scope: TenantScope, payload: J::Payload, options: JobOptions) -> Result<JobId, JobError>;
// JobOptions { max_attempts: u8 /* ≤ 5 */, timeout: Duration, idempotency_key: Option<String> }

trait SecretSource {
    fn resolve(&self, reference: &SecretRef) -> Result<Secret<String>, ConfigError>;
}
// SecretRef parses `secret://<name>`; Secret<T> renders as [redacted] in Debug, Display and tracing.

trait OutboxRepository {
    fn enqueue(&self, uow: &mut UnitOfWork, event: OutboxEvent) -> Result<(), OutboxError>;
    fn claim_unpublished_batch(&self, uow: &mut UnitOfWork, limit: u16) -> Result<Vec<OutboxEvent>, OutboxError>;
    fn mark_published(&self, uow: &mut UnitOfWork, ids: &[Uuid]) -> Result<(), OutboxError>;
    fn record_attempt_failure(&self, uow: &mut UnitOfWork, id: Uuid, error: &str) -> Result<(), OutboxError>;
    fn lag_seconds(&self) -> Result<u64, OutboxError>;
}
trait JobRunRepository {
    fn start(&self, uow: &mut UnitOfWork, run: JobRunStart) -> Result<(), JobError>;
    fn finish(&self, uow: &mut UnitOfWork, id: JobId, attempt: u8, outcome: JobOutcome) -> Result<(), JobError>;
    fn sweep_stuck_runs(&self, uow: &mut UnitOfWork, older_than: Duration) -> Result<u64, JobError>;
}
trait DeadLetterRepository {
    fn record(&self, uow: &mut UnitOfWork, letter: DeadLetter) -> Result<(), JobError>;
    fn list_dead_letters(&self, tenant: Option<TenantId>, page: Cursor) -> Result<Page<DeadLetter>, JobError>;
    fn mark_replayed(&self, uow: &mut UnitOfWork, id: Uuid) -> Result<(), ReplayError>;
}
trait IdempotencyKeyRepository {
    fn lookup(&self, tenant: TenantId, key: &str, request_hash: &[u8]) -> Result<IdempotencyHit, DomainError>;
    fn store(&self, uow: &mut UnitOfWork, record: IdempotencyRecord) -> Result<(), DomainError>;
}
trait PgHealthProbe { fn ping(&self, budget: Duration) -> ComponentHealth; }
```

`TenantScope` is how `enqueue_job` gets a tenant without depending on F038: the API passes the
`ActorContext` tenant and the harness passes one directly, and a call with neither returns
`JobError::MissingTenant` before any `job_runs` row exists (FR-F004-16). `IdempotencyHit` is
`Fresh | Replay(StoredResponse) | Mismatch`, which is how every feature's `409` with
`reason = idempotency_mismatch` is produced without any feature implementing idempotency itself.

**Transaction boundaries.** This feature's whole reason for existing is that events and jobs share
the caller's transaction rather than opening their own:

- `enqueue` and `enqueue_job` take the caller's `UnitOfWork` and never open a transaction. The
  boundary is the caller's business write, and the invariant it protects is that a committed change
  always has its event and a rolled-back one never does — no publish happens at write time at all.
- The relay's claim, publish and acknowledgement are deliberately **not** one transaction:
  `claim_unpublished_batch` locks rows with `SELECT ... FOR UPDATE SKIP LOCKED` in one unit,
  publishing happens outside it, and `mark_published` commits in a second unit. A crash between them
  republishes, which is why `Nats-Msg-Id` deduplication and the `published_at` check both exist —
  at-least-once delivery with an idempotent consumer, never a lost row.
- A job's `job_runs` insert shares the enqueuing transaction; its status transitions afterwards are
  each their own unit, because the worker and the enqueuer are different processes.
- `mark_replayed` and the re-enqueue share one unit, so a dead letter cannot be replayed twice.

### PostgreSQL/SQLx

- Migration `*_runtime_*.sql` creates `outbox_events(id uuid pk, tenant_id uuid not null, aggregate text not null, aggregate_id uuid not null, event_name text not null check (event_name ~ '^[a-z-]+\.[a-z-]+\.v[0-9]+$'), version bigint not null, payload jsonb not null, correlation_id uuid not null, occurred_at timestamptz not null, published_at timestamptz, attempts int not null default 0, last_error text)`, `job_runs(id uuid pk, tenant_id uuid not null, kind text not null, job_id uuid not null, attempt int not null default 1, status text not null check (status in ('queued','running','succeeded','failed','dead')), idempotency_key text, started_at timestamptz, finished_at timestamptz, error text, worker_id text, correlation_id uuid not null, created_at timestamptz not null)`, `dead_letters(id uuid pk, tenant_id uuid not null, kind text not null, job_id uuid not null, payload jsonb not null, attempts int not null, last_error text not null, dead_at timestamptz not null, replayed_at timestamptz)`. It also creates `idempotency_keys(tenant_id uuid not null, key text not null, request_hash bytea not null, response jsonb not null, route text not null, created_at timestamptz not null, expires_at timestamptz not null, primary key (tenant_id, key))` — named by F002, F005, F006, F008, F011, F016, F018, F019, F020 and F031 through F034 but owned by no feature until now — with an index on `expires_at` for the nightly sweep. `response` is a stored reply replayed verbatim and never queried by key, which is the payload case decision 2 permits.
- Invariants: `outbox_events.payload` and `dead_letters.payload` stay `jsonb` because they are opaque event and job payloads owned by the producing feature — the relay and the replay CLI move them byte for byte and never filter, join, sort, or constrain on a key inside them (decision 2); routing uses the typed `tenant_id`, `aggregate`, and `event_name` columns instead. Unique `job_runs_job_attempt_idx on (job_id, attempt)`; unique `job_runs_idempotency_idx on (tenant_id, kind, idempotency_key) where idempotency_key is not null`; unique `dead_letters_job_idx on (job_id)`; `outbox_events` rows are only ever updated to set `published_at`, `attempts`, `last_error`; a `DELETE` trigger rejects rows with `published_at is null`.
- Indexes: partial `outbox_events_unpublished_idx on (id) where published_at is null` (drives `SKIP LOCKED` polling), `outbox_events(tenant_id, occurred_at desc)`, `job_runs(tenant_id, kind, status, created_at desc)`, `job_runs(status, started_at) where status = 'running'` (stuck-run sweeper), `dead_letters(tenant_id, dead_at desc) where replayed_at is null`.
- Audit actions: `runtime.dead_letter.replay` recorded through the F003 writer when available (in-memory sink otherwise); health and metrics reads are not audited.
- Retention/deletion: published outbox rows older than 7 days and `job_runs` older than 30 days are deleted by the worker sweeper `runtime.retention` job (system tenant); dead letters are kept until replayed plus 90 days; rollback drops the three tables and the trigger.

### React/TypeScript

No UI. The surface for this section is the compose file, environment, and CLI:

- `infra/compose/docker-compose.yml` services and ports: `postgres` 5432, `nats` 4222/8222, `minio` 9000/9001, `mailpit` 1025/8025, `api` 8080 (+9464 metrics on the internal network only), `realtime` 8081, `worker` (no public port, 9465 metrics internal), `web` 5173 in dev and 80 in the image; named volumes `pgdata`, `natsdata`, `miniodata`; profiles `dev` (bind-mount sources, hot reload) and `ci` (built images).
- `infra/compose/.env.example` variables: `OPSHUB_DATABASE_URL`, `OPSHUB_NATS_URL`, `OPSHUB_NATS_CREDS`, `OPSHUB_S3_ENDPOINT`, `OPSHUB_S3_ACCESS_KEY`, `OPSHUB_S3_SECRET_KEY=secret://s3-secret`, `OPSHUB_FILES_BUCKET`, `OPSHUB_BACKUPS_BUCKET`, `OPSHUB_DOCUMENTS_BUCKET`, `OPSHUB_SMTP_HOST`, `OPSHUB_OTLP_ENDPOINT`, `OPSHUB_METRICS_PORT`, `OPSHUB_SECRET_SOURCE`, `OPSHUB_BASE_URL`, `OPSHUB_RP_ID`, `OPSHUB_LOG`.
- `Makefile` targets: `up`, `down`, `logs`, `ps`, `restore-drill`, `backup-now`; `infra/backup/{backup.sh, restore.sh, restore.md, manifest.json}`; `infra/alerts/rules.yml`; `infra/nats/{streams.json, permissions.conf}`.
- Telemetry names: spans `http.request`, `outbox.relay.batch`, `job.run`; log fields `service`, `tenant_id`, `actor_id`, `correlation_id`, `worker_id`, `job_kind`, `attempt`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F004-01 through FR-F004-16 in `testing/features/F004/requirements/cases.md`
- [ ] Failure/edge-case tests: missing env var exit code, malformed secret reference, invalid event name, NATS down during relay, duplicate relay instances, worker `SIGKILL` mid-job, timeout cancellation, quota exceeded, fifth failure to dead letter, double replay, readiness with each dependency down, outbox lag over 60 s
- [ ] Permission-negative and tenant-isolation tests: `/metrics` on the public port, enqueue without `ActorContext`, NATS credentials without `jobs.>` consume, worker consuming another tenant's quota
- [ ] Rust unit tests: `crates/events/src/runtime/` event name validation, retry schedule, quota math, `Secret` redaction, `RuntimeConfig` parsing
- [ ] API contract/integration tests: `/healthz`, `/readyz` (200 and each 503 shape), `/metrics` content, correlation id echo
- [ ] Database migration/constraint tests: tables, unique indexes, unpublished delete trigger, `SKIP LOCKED` batch behaviour, partial index usage, rollback
- [ ] CLI/compose tests in place of React component tests: `compose ps` health, `.env.example` completeness, `--version`, `replay`, `dead-letters` output, `NO_COLOR`
- [ ] Browser E2E tests: replaced by stack E2E: full compose boot, event round trip API → outbox → JetStream → worker, job retry and dead letter, restore drill
- [ ] Accessibility tests: operator output readable without colour, `NO_COLOR`, runbook structure, JSON readiness
- [ ] Performance/load tests: readiness latency, outbox drain and lag, job throughput

### Fast fanout configuration

- Test harness path: `testing/features/F004/`
- Feature flag: `F004_FEATURE`
- Fixture/seed factory: `testing/fixtures/runtime.rs` starts PostgreSQL 18, NATS JetStream, and MinIO test containers (or reuses the CI service containers), creates the two streams with unique per-worker prefixes, registers a `sample` job kind with a recording side-effect store, and seeds 10,000 unpublished outbox rows for drain tests
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z` for retry schedules (tokio paused time), unique `worker_id` per test
- Mock/stub contracts: in-memory `SecretSource` and log capture layer; a fault-injecting `JetStreamPublisher` wrapper for NATS-down tests; MinIO used for real for backup tests
- Parallel isolation: one schema per test worker, stream and subject prefix per test, separate metrics registry per test
- Targeted command: `cargo xtask test-feature F004`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F004/` including the weekly restore-drill log and manifest diff

## 6. Acceptance criteria

```gherkin
Feature: Runtime operations

Scenario: Clean boot is healthy
  Given a clean machine with Docker and the repository
  When the operator runs make up
  Then all eight compose services are healthy within 120 seconds
  And GET /readyz returns 200 with database, nats, object_storage, and outbox all ok

Scenario: A committed write always publishes its event
  Given an API mutation that enqueues tenant.created.v1 in its transaction
  When NATS is unavailable for 30 seconds and then recovers
  Then the outbox row stays unpublished with attempts incremented during the outage
  And it is published exactly once after recovery and outbox.published.v1 reports the batch

Scenario: Job retry and dead letter without duplicate side effects
  Given a sample job that fails on attempts 1 to 5
  When it is enqueued
  Then job_runs shows attempts 1 to 5 with the backoff schedule, a dead_letters row exists, and the side-effect store has zero entries
  When the operator replays the dead letter and the handler succeeds
  Then the side-effect store has exactly one entry keyed by the original idempotency key

Scenario: Metrics are not reachable from the public ingress
  Given the compose stack with the web proxy on port 80
  When a client requests /metrics through the proxy or the API port
  Then the response is 404 not_found
  And the same path on the internal metrics port returns Prometheus text

Scenario: Enqueue without gateway context is refused
  Given an internal route invoked without an ActorContext
  When it calls enqueue_job
  Then the call returns JobError::MissingTenant and no job_runs row exists

Scenario: Restore drill proves point-in-time recovery
  Given last night's base backup and archived WAL in opshub-backups
  When the operator runs make restore-drill with a target timestamp
  Then the scratch database restores to that timestamp and the tenants, users, and outbox_events counts match the manifest
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F001 (workspace, images build in CI, service containers); decisions sections 2, 3, 7, 9; contracts row F004
- Blocks: F005, F010, F017, F037, F019, F046, F028
- Conflicts with: none (disjoint owned paths)
- External dependencies: Docker Engine 27 or newer with compose v2; images `postgres:18`, `nats:2`, `minio/minio`, `axllent/mailpit`; OTLP collector optional in dev (exporter degrades to a no-op with a warning)
- Risks and mitigations: the F038 `ActorContext` lands after this feature, so `enqueue_job` takes a `TenantScope` argument that F038 populates from the context and tests populate directly; JetStream dedupe is bounded by the 2-minute window, so `published_at` idempotency is the durable guard for slower retries; PITR depends on WAL archiving being enabled in the compose image, which the healthcheck verifies by querying `archive_mode`; restore drills need object storage credentials in CI, provided through the secret source.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F001 accepted and archived; images build in the `gates.yml` matrix
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F004/`
- [ ] Migration file name and owned paths claimed
- [ ] Test-container or CI service definitions for PostgreSQL 18, NATS, and MinIO available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, CLI, stack E2E, permission-negative, accessibility, and performance gates pass
- [ ] A restore drill has been executed and its evidence stored under `testing/evidence/F004/restore-drill/`
- [ ] `outbox.published.v1` and job lifecycle verified end to end with the F002 `tenant.created.v1` event
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, and `check-migrations` pass
- [ ] Rollback verified: disable `F004_FEATURE` (relay and consumer idle, health routes remain), run down migration on an empty database
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Operators can boot the full stack with `make up`, observe health, readiness, traces, and metrics, rely on the transactional outbox and JetStream job transport with retries and dead letters, and recover with nightly backups and point-in-time restore.
- Migration adds `outbox_events`, `job_runs`, and `dead_letters`; rollback drops them. Feature is off by default behind `F004_FEATURE`.
