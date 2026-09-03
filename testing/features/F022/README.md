# F022 — Metrics and summaries harness

Feature-gated tests for `F022`. Keep test code in this directory.

- Gate: `F022_FEATURE`
- Targeted: `cargo xtask test-feature F022`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/metrics.rs` (F021 three-sheet fixture plus metrics "Open high risks" and "Budget margin"; expected values in `fixtures/expected_values.json`)
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
