# Isolated feature-gated testing

All reusable test code, harnesses, fixtures, deterministic seed data, mocks, performance tests, accessibility tests, and release evidence live here—not in the live application code paths.

```text
testing/
├── harness/             # shared Rust/API/DB/React/browser runners
├── fixtures/            # deterministic builders and seed data
├── features/            # one folder per feature ticket
│   └── F###/            # feature.toml, README.md, then one cases.md per lane
│       ├── requirements/
│       ├── api/
│       ├── database/
│       ├── frontend/
│       ├── e2e/
│       ├── accessibility/
│       └── performance/
├── config/              # feature-gate/test-profile configuration
└── evidence/            # CI artifacts and release-gate results
```

Each feature suite is independently selectable for fast fanout testing and all suites can be enabled for release validation. Every suite must document its flag, targeted command, full command, fixture isolation, and CI artifact location in its ticket.

Feature tests must be written before production implementation and must trace back to ticket requirement IDs (`FR-F###-NN` and `NFR-F###-NN`). Each lane's `cases.md` lists the named tests for that lane and the requirement each proves; the `requirements/cases.md` table must cover every FR and NFR in the ticket. `validate-work` rejects lanes below the minimum case count or identical across features.

Tests must be deterministic, order-independent, timezone-controlled, and parallel-safe. Use isolated tenants, database schemas or transactions, worker IDs, and external-service mocks. Do not rely on shared mutable state.

Required validator command: `cargo xtask validate-tickets`. It checks ticket metadata, dependency references, owned paths, feature flags, required sections, file size, and lifecycle timestamps.
