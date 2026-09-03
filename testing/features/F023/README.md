# F023 — Dashboard builder harness

Feature-gated tests for `F023`. Keep test code in this directory.

- Gate: `F023_FEATURE`
- Targeted: `cargo xtask test-feature F023`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/dashboards.rs` (F021 fixture plus dashboard "Weekly review" with table, report embed, text, image, and one unresolved `kpi` widget; editor, viewer, restricted viewer, share-link guest, foreign tenant)
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
