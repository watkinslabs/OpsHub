# F062 — Design system and UI primitives harness

Feature-gated tests for `F062`. Keep test code in this directory.

- Gate: `F062_FEATURE`
- Targeted: `cargo xtask test-feature F062`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/design_system.ts` (the story matrix of every exported primitive and pattern × its states × light and dark × comfortable and compact, a 10,000-row `DataTable` dataset, a 1,000-row repaint dataset, fixed clock `2026-09-03T00:00:00Z`, locale `en-US`, timezone `UTC`).
- Determinism: fonts load from `apps/web/src/design/fonts/` rather than the network, animations are disabled during capture, device pixel ratio is pinned to 1, and screenshot baselines are keyed by story id, theme, and density.
- Note on lanes: F062 owns no route and no table, so `api/` and `database/` hold negative controls — no module under `apps/web/src/ui/**` may perform a network call, and the feature may add no migration. That absence is the contract worth testing.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
