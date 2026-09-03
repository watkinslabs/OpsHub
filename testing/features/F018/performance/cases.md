# F018 performance cases

File: `testing/features/F018/performance/{validate_bench.rs,list_bench.rs}`. Runs against the 5,000-workflow generator with seed `0x0F18`. Flag `F018_FEATURE`.

- `validate_25_actions_p95` — NFR-F018-01: 500 validations of a 25-action, depth-4, 200-leaf definition; p95 < 200 ms.
- `test_with_formula_leaf_p95` — NFR-F018-01: 200 `test` calls with a formula leaf over a 100-row sheet; p95 < 2 s.
- `workflow_list_5000_p95` — NFR-F018-01: 200 `GET /api/v1/workflows?limit=50` pages across 5,000 workflows; p95 < 500 ms.
- `publish_transaction_p95` — FR-F018-07: 200 publishes of 25-step definitions; p95 < 800 ms including outbox write.

Evidence: criterion summaries under `testing/evidence/F018/performance/`.
