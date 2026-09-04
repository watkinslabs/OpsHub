---
id: T292
type: task
status: planned
parent_epic: E003
parent_feature: F073
parent_story: S146
depends_on: [S146]
owned_paths: [testing/features/F073/**]
feature_flag: F073_FEATURE
branch: t292-announcement-tests
started_at: null
finished_at: null
---

# T292 — Announcement tests

## Identity

- Parent story: `S146` Contextual help
- Owner: platform
- Branch: `t292-announcement-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 3; `docs/capability-contracts.md` row F073; `docs/accessibility-conformance.md`

## Objective

Build the F073 harness that proves the two surfaces end to end: the E2E, accessibility and performance lanes, the shared fixtures, the HTML injection corpus and the editorial-classifier corpus, plus the traceability lane that maps every requirement id to a case.

## Specification

- Owned paths: `testing/features/F073/{feature.toml, README.md}`, `testing/features/F073/requirements/cases.md`, `testing/features/F073/e2e/{announcements.spec.ts, help.spec.ts}`, `testing/features/F073/accessibility/announcements.a11y.spec.ts`, `testing/features/F073/performance/{list_bench.rs, audience_bench.rs, article_bench.rs}`, `testing/features/F073/api/fixtures/`, `testing/features/F073/frontend/`
- Contract and input: the fixture factory builds tenant A on `enterprise` holding the `assets` entitlement and tenant B on `free`, a `platform-operator` principal, a `tenant-admin` and a member per tenant, six announcements across the three severities and the four target kinds, one superseded pair, one pre-dismissed announcement, and a help bundle of eight `en-US` articles with four `de-DE` translations, six context mappings and one withdrawn slug. Clock fixed at `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seeds, fixed bundle signing key.
- Output and behaviour: E2E covers dismiss-and-reload proving an announcement never returns, a free tenant never seeing an enterprise-targeted item, the interrupting modal appearing once and then degrading to a passive item, contextual help opened with `F1` from the sheet grid and closed with `Escape` without losing selection, and a withdrawn slug landing on the index. The accessibility lane runs axe on the panel, the modal and the drawer, asserts focus return, the polite live region, severity carried by text plus a labelled icon, and an escapable modal under `prefers-reduced-motion`. The performance lane measures the list p95 with 200 announcements in scope, article reads warm and with a matching `ETag`, and audience resolution for a 50,000-user target. The frontend lane additionally asserts that neither surface issues a request to any origin other than the API, which is how the no-tracking requirement is verified rather than asserted. The HTML injection corpus and the editorial token corpus live under `testing/features/F073/api/fixtures/` and are consumed by the T290 unit tests.
- Data access: the harness never opens a database connection of its own; it seeds through the fixture factory, which uses the repositories from `crates/persistence/src/announcements/` (decision section 2.1).
- Dependencies: T289 schema and T290 and T291 surfaces must exist before the lanes go green; the lanes are written first and observed failing.
- Feature flag: `F073_FEATURE` is enabled explicitly by both the targeted and full commands.

## TDD

- Failing test first: `testing/features/F073/e2e/announcements.spec.ts::dismissed_announcement_absent_after_reload`, `::free_tenant_sees_no_enterprise_announcement`, `::interrupting_modal_shows_once_then_degrades`; `testing/features/F073/e2e/help.spec.ts::f1_opens_contextual_help_on_grid`, `::withdrawn_slug_lands_on_index`; `testing/features/F073/accessibility/announcements.a11y.spec.ts::panel_and_drawer_have_no_serious_violations`, `::severity_is_not_colour_only`, `::modal_is_escapable_with_reduced_motion`; `testing/features/F073/performance/list_bench.rs::list_p95_under_150ms_with_200_announcements`, `::audience_resolution_50k_under_3s`, `testing/features/F073/performance/article_bench.rs::article_read_p95_under_80ms_warm`
- Targeted command: `cargo xtask test-feature F073`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/announcements.rs`; F048 entitlement and F049 locale stubs; signed and unsigned help bundles; evidence written to `testing/evidence/F073/`

## Exit criteria

- [ ] Every FR and NFR id in the ticket has a row in `testing/features/F073/requirements/cases.md`
- [ ] All seven lanes present and running in targeted and full modes
- [ ] Positive control recorded per lane: a known defect fails the lane, restoring the code passes it
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S146
- [ ] `finished_at` recorded
