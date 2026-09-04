---
id: T184
type: task
status: planned
parent_epic: E004
parent_feature: F046
parent_story: S092
depends_on: [T183]
owned_paths: [testing/features/F046/**]
feature_flag: F046_FEATURE
branch: t184-reconnect-conflict-tests
started_at: null
finished_at: null
---

# T184 — Reconnect/conflict tests

## Identity

- Parent story: `S092` Change recovery
- Owner: platform
- Branch: `t184-reconnect-conflict-tests`
- Decision references: `docs/architecture-decisions.md` sections 5, 9; `docs/capability-contracts.md` row F046

## Objective

Build the two-browser end-to-end, accessibility, and load lanes that prove convergence, reconnect replay, visible conflict resolution, lease expiry, and the latency and concurrency targets of the live protocol.

## Specification

- Owned paths: `testing/features/F046/e2e/{collab.spec.ts, reconnect.spec.ts}`, `testing/features/F046/accessibility/collab.a11y.spec.ts`, `testing/features/F046/performance/{round_trip_bench.rs, sessions_bench.rs, replay_bench.rs}`, `testing/features/F046/fixtures/{load_generator.rs, change_corpus.rs}`
- Contract/input: Playwright with two browser contexts (Ana, Ben) plus a viewer context against the seeded tenant with `services/realtime`, `services/api`, and JetStream running; network interruption via Playwright route abort and `context.setOffline`; `change_corpus.rs` generates 1,000 deterministic Automerge changes with fixed actor IDs and their dependency hashes; `load_generator.rs` opens N WebSocket clients with the harness client. Any seeding or assertion these lanes make against `collaboration_sessions`, `presence_leases`, `document_changes`, or `document_change_deps` drives the `CollaborationSessionRepository`, `PresenceLeaseRepository`, and `DocumentChangeRepository` traits against an isolated tenant fixture; no test file holds a SQL string, `sqlx::query*` call, or connection.
- Output/behavior: E2E asserts both editors' document text converges after concurrent inserts, Ben's offline edits replay after reconnect with revs continuing from the last durable rev and each replayed change's `document_change_deps` rows resolving against `document_changes(document_id, hash)`, Ben sees the conflict banner on a stale sheet patch and `Take theirs` applies the server value, the viewer sees presence and live text but no editing, Ana's avatar disappears from Ben's list 30 seconds after Ana's client stops renewing; axe reports zero serious violations with presence and the banner shown; benches assert change round trip p95 < 250 ms with 50 editors on one document, 1,000 sessions on one node under 512 MB resident, presence propagation < 1 s across two nodes, replay of 1,000 changes < 500 ms.
- Dependencies: T183 UI and replay; `testing/harness/` Playwright, axe, criterion, and WebSocket client; F045 document editor.
- Feature flag: `F046_FEATURE` enabled in the seeded tenant.

## TDD

- Failing test first: `testing/features/F046/e2e/collab.spec.ts::two_editors_converge_on_document`, `::stale_sheet_patch_shows_conflict_take_theirs`, `::viewer_sees_presence_but_cannot_edit`, `::presence_disappears_after_lease_expiry`; `testing/features/F046/e2e/reconnect.spec.ts::offline_edits_replay_after_reconnect`, `::changes_not_saved_after_thirty_seconds`; `testing/features/F046/accessibility/collab.a11y.spec.ts::editor_with_presence_and_banner_has_no_serious_axe_violations`, `::presence_join_announced_rate_limited`; `testing/features/F046/performance/round_trip_bench.rs::change_round_trip_50_editors_p95`, `sessions_bench.rs::thousand_sessions_one_node_memory`, `replay_bench.rs::replay_1000_changes_p95`
- Targeted command: `cargo xtask test-feature F046`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded tenant from `testing/fixtures/realtime.rs`; two realtime nodes behind the gateway for propagation tests; no external mocks

## Exit criteria

- [ ] Tests written before fixtures and observed failing
- [ ] E2E, accessibility, and performance lanes pass with evidence under `testing/evidence/F046/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S092
- [ ] `finished_at` recorded
