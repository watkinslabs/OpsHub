# F004 — Runtime operations harness

Feature-gated tests for `F004`. Keep test code in this directory. This is a runtime/tooling feature with no UI: the `frontend/` lane holds CLI and compose output cases, and `e2e/` holds stack tests that boot the real compose services.

- Gate: `F004_FEATURE`
- Targeted: `cargo xtask test-feature F004`
- Full: `cargo xtask test-all`
- Fixture: `RuntimeFixture::start()` provisions PostgreSQL 18, NATS JetStream, and MinIO (test containers or the CI service containers), creates `OPSHUB_EVENTS` and `OPSHUB_JOBS` with a per-test subject prefix, registers the recording `sample` job, seeds 10,000 unpublished outbox rows on demand, and uses tokio paused time for retry schedules; clock fixed at `2026-09-03T00:00:00Z`.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/` (CLI output), `e2e/` (stack), `accessibility/` (operator output), `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
