# F036 — Sharing, guests, and links harness

Feature-gated tests for `F036`. Keep test code in this directory.

- Gate: `F036_FEATURE`
- Targeted: `cargo xtask test-feature F036`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/sharing.rs` (tenant A with workspace "Ops", folder, sheet "Launch plan", dashboard "Exec"; owner `own`, admin `adm`, editor `eli`, viewer `vic`, `dana` in group `Contractors`; seeded workspace editor grant for `Contractors`, sheet viewer grant for `dana`, dashboard deny for `dana`; viewer link with `max_uses` 2; invitation for `client@example.com`; tenant B foreign owner)
- Determinism: fixed token RNG seed, fixed scoped-token signing key, fixed clock `2026-09-03T00:00:00Z` with advance helpers for 15-minute, 7-day, and 30-day boundaries; rate limiter on the fixed clock
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
