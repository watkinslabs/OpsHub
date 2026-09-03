# F039 — AI formulas/queries harness

Feature-gated tests for `F039`. Keep test code in this directory. No lane may reach a live model: every command sets `AI_PROVIDER=recorded` and installs the socket guard, and a missing cassette fails the run instead of falling back to a network call.

- Gate: `F039_FEATURE`, with the F048 `ai-assist` entitlement seeded `active`
- Targeted: `cargo xtask test-feature F039`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/ai_assist.rs` (tenants A and B; viewer, sheet-editor, report-editor, tenant-admin; sheet `Launch plan` with 200 rows and columns `Status`, `Due date`, `Owner`, `Owner email`, `Salary` marked sensitive, and formula column `Days late`; sheet `Risks` with 120 rows; sheet `Finance FY26` readable only by the admin; a 20-sheet 400-column set for the scope benchmark; seeded `ai_settings` and `ai_usage`; fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seeds and hash salt).
- Providers: `recorded` replays `evaluation/cassettes/<suite>/<envelope_hash>.json`; `stub` scripts every `ProviderError` variant for the error paths. No other adapter is compiled into the test binaries.
- Lanes: `requirements/` (traceability for every FR-F039 and NFR-F039 id), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`, and `evaluation/` (leakage, grounding, refusal, formula, plan suites with the thresholds in `evaluation/thresholds.toml`).
- Seam note: the provider and retrieval modules exercised here are the same ones F040 consumes; changes to their contracts must keep these lanes green.
