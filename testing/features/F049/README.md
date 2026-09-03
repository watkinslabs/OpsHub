# F049 — Localization harness

Feature-gated tests for `F049`. Keep test code in this directory.

- Gate: `F049_FEATURE` (pseudo-locale sweep additionally needs `F049_PSEUDO_LOCALE=true`)
- Targeted: `cargo xtask test-feature F049`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/i18n.rs` seeds tenant A (`de-DE`, `Europe/Berlin`), tenant B (`en-US`, `UTC`), a user with a `pt-BR`/`America/Sao_Paulo` override, and eight catalogs; browser projects pin `TZ=Europe/Berlin` and `TZ=America/Sao_Paulo`.
