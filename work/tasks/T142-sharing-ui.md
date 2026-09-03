---
id: T142
type: task
status: planned
parent_epic: E004
parent_feature: F036
parent_story: S071
depends_on: [T141]
owned_paths: [apps/web/src/features/sharing/**, testing/features/F036/frontend/**, testing/features/F036/requirements/**]
feature_flag: F036_FEATURE
branch: t142-sharing-ui
started_at: null
finished_at: null
---

# T142 — Sharing UI

## Identity

- Parent story: `S071` Resource sharing grants
- Owner: platform
- Branch: `t142-sharing-ui`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F036

## Objective

Build the share dialog with the people list, role selectors, add-people search, and admin deny option wired to the real share routes with optimistic role changes and rollback.

## Specification

- Owned paths: `apps/web/src/features/sharing/{ShareDialog.tsx, PeopleList.tsx, PersonRow.tsx, RoleSelect.tsx, AddPeopleSearch.tsx, api.ts, hooks.ts}`
- Contract/input: generated `SharingApi` client (`listShares`, `createShare`, `updateShare`, `revokeShare`); props `{ targetKind, targetId, canShare, isAdmin }` from the hosting header; F002 user and group search for `AddPeopleSearch` (tenant-scoped, ≤ 20 results); query key `['shares', targetKind, targetId, { cursor, principalKind, effect }]`.
- Output/behavior: dialog lists direct grants first then inherited grants with an `Inherited from <workspace or folder name>` label and disabled controls; `RoleSelect` offers owner, admin, editor, commenter, viewer, form submitter (guest rows limit to the four guest roles); admins see a `Deny` option that sets `effect: deny` with a `Ban` icon; role change applies optimistically with `If-Match` and rolls back on `conflict` showing the stale banner; revoke prompts and removes the row, restoring it on error; the `last_owner` error renders inline as `Add another owner before removing this one`; states loading skeleton, empty `Only you have access`, error banner with `correlation_id`, read-only list with `Only owners and admins can change sharing` when `canShare=false`, offline badge; focus trapped and restored to the `Share` button; telemetry `share_dialog_opened`, `share_granted`, `share_denied_set`, `share_revoked`.
- Dependencies: T141 routes; F005 workspace shell header exposes the `Share` button slot; F006 sheet header.
- Feature flag: `F036_FEATURE` read through the flag hook; the `Share` button is not rendered when off.

## TDD

- Failing test first: `testing/features/F036/frontend/ShareDialog.test.tsx::renders_direct_then_inherited_grants`, `::share_dialog_role_change_rolls_back_on_conflict`, `::editor_sees_read_only_list`, `::last_owner_error_shown_inline`, `::deny_option_visible_only_to_admin`, `AddPeopleSearch.test.tsx::search_lists_users_and_groups_max_20`, `::selecting_person_creates_grant_with_default_viewer`
- Targeted command: `cargo xtask test-feature F036`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded sharing fixture (workspace editor grant for `Contractors`, sheet deny for `dana`, one owner); Vitest with fake timers for the stale banner

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component lane passes; dialog opens from the sheet and workspace headers against the real API in the dev stack
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S071
- [ ] `finished_at` recorded
