---
id: T013
type: task
status: planned
parent_epic: E001
parent_feature: F004
parent_story: S007
depends_on: [S007]
owned_paths: [infra/**, crates/persistence/src/runtime/**, services/api/src/runtime/**, testing/features/F004/frontend/**, testing/features/F004/e2e/**]
feature_flag: F004_FEATURE
branch: t013-container-compose-baseline
started_at: null
finished_at: null
---

# T013 — Container/compose baseline

## Identity

- Parent story: `S007` Config/secrets
- Owner: platform
- Branch: `t013-container-compose-baseline`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 1, 7
- Canonical contract: `docs/capability-contracts.md` row F004

## Objective

Deliver the compose stack, service images, NATS and MinIO initialisation, and the typed `RuntimeConfig` with `SecretSource` and log redaction that every service loads at startup.

## Specification

- Owned paths: `infra/compose/{docker-compose.yml, .env.example}`, `infra/docker/{api,worker,realtime,web}.Dockerfile`, `infra/nats/{streams.json, permissions.conf}`, `infra/minio/init.sh`, `Makefile` (`up`, `down`, `logs`, `ps`), `crates/persistence/src/runtime/{mod.rs, config.rs, secrets.rs, pool.rs, redaction.rs}`, `services/api/src/runtime/state.rs`; the pool is built and owned in `crates/persistence` and handed to services as repository handles, so no service opens a pool or writes SQL of its own (decision 2.1)
- Contract/input: compose services `postgres` (`postgres:18`, `wal_level=replica`, `archive_mode=on`, `pg_isready` healthcheck), `nats` (`nats:2 --jetstream`), `minio` plus `minio-init` (buckets `opshub-files`, `opshub-backups`, `opshub-documents`), `mailpit`, `api`, `worker`, `realtime`, `web`, profiles `dev` and `ci`, named volumes; `RuntimeConfig::load() -> Result<RuntimeConfig, ConfigError>` reading `OPSHUB_*`; `SecretSource::resolve(name) -> Result<Secret<String>>` with `FileSecretSource`, `EnvSecretSource`, `VaultKvSecretSource` chosen by `OPSHUB_SECRET_SOURCE`; `RedactionLayer` for `tracing-subscriber`; `PgPoolBuilder` (max connections, 30 s statement timeout, application name) is the only constructor of a SQLx pool and `services/api/src/runtime/state.rs` stores the repository handles it yields, never the pool.
- Output/behavior: `docker compose up -d --wait` healthy within 120 s; `docker compose ps --format json` shows eight healthy services; missing variable exits 78 naming the variable only; `secret://` values resolved once at startup, `Debug` prints `[redacted]`, log lines never contain the resolved value; images distroless, uid 65532, read-only root, `--version` prints the crate version; `permissions.conf` grants api publish-only on `events.>` and `jobs.>`, worker consume, realtime consume on `events.>`.
- Dependencies: F001 workspace, `gates.yml` image build job; Docker Engine 27 with compose v2.
- Feature flag: `F004_FEATURE` (compose and config are always active; the flag gates relay and consumer startup)

## TDD

- Failing test first: `testing/features/F004/e2e/stack.spec.rs::compose_stack_healthy_within_120s`, `::compose_services_non_root_read_only`; `testing/features/F004/frontend/cli_tests.rs::config_missing_var_exits_78_without_value`, `::env_example_covers_every_config_field`, `::image_version_flag_prints_crate_version`; `testing/features/F004/api/config_tests.rs::secret_reference_resolved_and_redacted`, `::api_state_exposes_repositories_not_pool`, `::nats_permissions_deny_api_consume`
- Targeted command: `cargo xtask test-feature F004`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/runtime.rs` in-memory `SecretSource`, log capture layer; real compose stack in the stack E2E lane

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Stack boots healthy in CI; images built and labelled with the git SHA
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S007
- [ ] `finished_at` recorded
