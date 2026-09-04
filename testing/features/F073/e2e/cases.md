# F073 e2e cases

File: `testing/features/F073/e2e/{announcements.spec.ts,help.spec.ts}`. Playwright against the seeded tenants. Flag `F073_FEATURE`.

- `dismissed_announcement_absent_after_reload` — FR-F073-06: a member opens the bell, sees the dot, opens `What's new`, dismisses the top item, reloads, signs out and back in; the item is gone from the default list and present only under `Show dismissed`.
- `free_tenant_sees_no_enterprise_announcement` — FR-F073-04: with a `plan: enterprise` announcement published platform-wide, the tenant B admin on `free` opens the panel and sees only the untargeted item, while the tenant A admin sees both.
- `tenant_admin_publishes_to_own_tenant_only` — FR-F073-03, FR-F073-15: the tenant A admin publishes a tenant-scope announcement; it appears for tenant A users and never for tenant B users.
- `interrupting_modal_shows_once_then_degrades` — FR-F073-09: an `action_required` announcement opens the modal on first load; `Later` closes it; a second `action_required` published minutes later appears only in the panel because the daily cap is spent.
- `material_change_appears_as_new_item` — FR-F073-07: after a user dismisses an announcement the author publishes a superseding version; the user sees the new item once, and the superseded one never returns.
- `f1_opens_contextual_help_on_grid` — FR-F073-10: on the sheet grid with three rows selected the user presses `F1`, the drawer opens on the grid article with its related list, `Escape` closes it, and the selection and scroll position are unchanged.
- `withdrawn_slug_lands_on_index` — FR-F073-12: a `Learn more` link whose slug was withdrawn by the latest bundle opens the drawer on the contextual index with the moved-article note.
- `german_user_reads_fallback_article` — FR-F073-11: a `de-DE` user opens an article with no German translation and sees the English body with the fallback note.

Evidence: Playwright traces and network logs under `testing/evidence/F073/e2e/`.
