# F001 performance cases

File: `testing/features/F001/performance/ci_budget_tests.rs`. Measures build and workflow wall clock from CI run metadata. Flag `F001_FEATURE`.

- `cold_workspace_build_under_10_minutes` — FR-F001-01: `cargo build --workspace` with empty caches on the CI runner completes under 600 s.
- `warm_workspace_build_under_4_minutes` — NFR-F001-01: with restored registry and target caches, `cargo build --workspace` completes under 240 s.
- `web_build_under_90_seconds` — NFR-F001-01: `pnpm --filter web build` with restored pnpm store completes under 90 s.
- `warm_workflow_under_15_minutes` — NFR-F001-01: full `gates.yml` run duration from `gh run view --json` is under 900 s.

Evidence: timing summaries and run JSON under `testing/evidence/F001/performance/`.
