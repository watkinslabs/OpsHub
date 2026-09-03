# F054 performance cases

File: `testing/features/F054/performance/{run_bench.rs,run_list_bench.rs}`. Runs against the seeded flow with scripted connector mocks (zero external latency) and a 100,000-run generator with fixed seed. Flag `F054_FEATURE`.

- `enqueue_ack_p95_under_2s` — NFR-F054-01: 200 sequential `POST /bridge/flows/{id}/run`; p95 < 2 s for the 202 response.
- `ten_step_run_under_30s` — NFR-F054-01: 20 runs of a 10-step flow with mocked connectors; each completes in under 30 s wall clock.
- `run_list_100k_p95` — NFR-F054-01: 200 `GET /bridge/runs?status=failed&limit=50` against 100,000 runs; p95 < 500 ms using the status index.
- `run_detail_with_50_steps_p95` — FR-F054-11: 200 `GET /bridge/runs/{id}` for a 50-step run with 200 KB snapshots; p95 < 500 ms.
- `waiting_runs_release_worker_slots` — FR-F054-09: 500 runs parked on `wait.delay` consume zero worker slots; a concurrent 10-step run still completes under 30 s.

Evidence: criterion/k6 summaries under `testing/evidence/F054/performance/`.
