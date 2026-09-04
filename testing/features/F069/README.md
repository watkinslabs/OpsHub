# F069 — Home and my work harness

Feature-gated tests for `F069`. Keep test code in this directory.

- Gate: `F069_FEATURE`
- Targeted: `cargo xtask test-feature F069`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/home.rs` (tenants A and B; a member with 200 favourites and 100 recents; a brand-new member with neither; a second member for cross-user cases; a `tenant-admin`; a `viewer` with no workspace access; three workspaces, four sheets of 50 rows, two saved views and one document as pin targets; fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seeds).
- Stubs: `testing/harness/home/` provides `StubSectionProvider` and `StubTargetResolver` with programmable latency, error, item count, and readability, so the `assigned`, `approvals`, and `mentions` slots — whose real providers arrive with F010, F020, and F016 — are exercised now. Nothing here reaches the network.
- Two properties every lane exists to protect: a home response never shows an item the caller may not read and never reveals that one was dropped, and one person's favourites and recents are invisible to everyone else including a `tenant-admin`.
- Lanes: `requirements/` (traceability for every FR and NFR id), `api/` (aggregation, favourites, recents, prune, permission and isolation matrices), `database/` (the two tables, their constraints and indexes, rollback), `frontend/` (section, empty, degraded and offline states, the favourite toggle), `e2e/` (landing, visiting, pinning, first run), `accessibility/` (landmarks, headings, toggle naming, both themes), `performance/` (the 400 ms budget and the fixed thirteen-statement cost).
