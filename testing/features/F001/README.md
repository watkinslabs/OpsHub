# F001 — Repository and CI harness

Feature-gated tests for `F001`. Keep test code in this directory. Tooling feature: tests shell out to `cargo`, `pnpm`, and `cargo xtask` against a fixture clone and parse `gates.yml`.

- Gate: `F001_FEATURE`
- Targeted: `cargo xtask test-feature F001`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/` (command and workflow assertions), `database/` (CI database service), `frontend/` (status page), `e2e/` (clean checkout and PR gate flow), `accessibility/`, `performance/` (build and workflow budgets); each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
