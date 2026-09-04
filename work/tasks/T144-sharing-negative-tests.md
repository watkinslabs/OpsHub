---
id: T144
type: task
status: planned
parent_epic: E004
parent_feature: F036
parent_story: S072
depends_on: [T143]
owned_paths: [apps/web/src/features/sharing/**, testing/features/F036/api/**, testing/features/F036/frontend/**, testing/features/F036/e2e/**, testing/features/F036/accessibility/**]
feature_flag: F036_FEATURE
branch: t144-sharing-negative-tests
started_at: null
finished_at: null
---

# T144 — Sharing negative tests

## Identity

- Parent story: `S072` Guest identity and links
- Owner: platform
- Branch: `t144-sharing-negative-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 6, 9; `docs/capability-contracts.md` row F036

## Objective

Prove that guests and link holders cannot escape their grants, that deny always wins, and that the share dialog, landing page, and guest acceptance work end to end in the browser with keyboard and screen-reader support.

## Specification

- Owned paths: `apps/web/src/features/sharing/{PublicShareLanding.tsx, GuestAcceptPage.tsx, scopedClient.ts}` (hardening only: no navigation chrome, scoped token never persisted), `testing/features/F036/api/isolation_tests.rs`, `testing/features/F036/frontend/{LinkSection.test.tsx, PublicShareLanding.test.tsx}`, `testing/features/F036/e2e/sharing.spec.ts`, `testing/features/F036/accessibility/sharing.a11y.spec.ts`
- Contract/input: fixtures are seeded through the sharing repository traits (`ShareRepository`, `ShareLinkRepository`, `GuestInvitationRepository`, `GuestUserRepository`) so no SQL lives in this suite; seeded fixture with tenant A (owner `own`, admin `adm`, editor `eli`, `dana` in group `Contractors`, guest `client@example.com`), tenant B, a viewer link with `max_uses` 2, and the F006 row routes, F010 search route, and F005 workspace list as probe targets.
- Output/behavior: isolation suite asserts for a scoped link token: `GET /api/v1/workspaces` → 403, `GET /api/v1/search` → 403, `PATCH /api/v1/rows/{id}` → 403, `GET /api/v1/sheets/{other}` → 404, `GET /api/v1/sheets/{target}` → 200, scoped token after expiry → 401 `denied`; for a guest session: workspace list contains only granted workspaces, other sheets → 404, `Share` route → 403; deny beats inherited allow for user and group; cross-tenant share, link, and invitation IDs → 404; tracing output contains no raw token and no token hash, which never leaves the repository query; landing page renders without workspace navigation and stores the scoped token only in memory; E2E covers share with user and group, invite and accept a guest in a second browser context, create and copy a link, open it in an incognito context, revoke, reopen shows `This link is no longer valid`; accessibility covers dialog focus trap, role select, copy announcement, and landing page axe.
- Dependencies: T143 routes, repositories, and UI; F006 rows, F010 search, F005 workspace list available in the E2E stack.
- Feature flag: `F036_FEATURE`.

## TDD

- Failing test first: `testing/features/F036/api/isolation_tests.rs::link_scoped_token_cannot_search_or_write`, `::link_scoped_token_cannot_read_other_resources`, `::link_scoped_token_expires_after_15_minutes`, `::guest_cannot_reach_ungranted_sheet`, `::guest_cannot_open_share_dialog_routes`, `::deny_wins_for_group_member`, `::public_routes_redact_tokens_in_traces`; `testing/features/F036/frontend/PublicShareLanding.test.tsx::renders_target_without_navigation`, `LinkSection.test.tsx::copy_link_announces_and_hides_url_after_close`; `testing/features/F036/e2e/sharing.spec.ts::share_invite_link_and_revoke`, `::guest_accepts_and_sees_only_granted_sheet`; `testing/features/F036/accessibility/sharing.a11y.spec.ts::share_dialog_and_landing_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F036`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright with three browser contexts (owner, guest, anonymous link holder); fixed clock advanced past 15 minutes for expiry; tracing subscriber capture in tests

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] API isolation, component, E2E, and accessibility lanes pass, and `cargo xtask check-persistence` confirms the suite contains no SQL
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S072
- [ ] `finished_at` recorded
