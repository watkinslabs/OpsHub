# F058 — Mobile clients harness

Feature-gated tests for `F058`. Keep test code in this directory.

- Gate: `F058_FEATURE`
- Targeted: `cargo xtask test-feature F058`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/mobile.rs` (two users with sessions and devices, 200-row sheet with six column types, published form, foreign tenant), fixed signing key, in-memory push recorder, Playwright Pixel 7 emulation.
