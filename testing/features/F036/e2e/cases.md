# F036 e2e cases

File: `testing/features/F036/e2e/sharing.spec.ts`. Playwright against seeded tenant with three browser contexts (owner, guest, anonymous link holder). Flag `F036_FEATURE`.

- `share_invite_link_and_revoke` — FR-F036-01, FR-F036-06, FR-F036-09, FR-F036-10, FR-F036-14: `own` opens `Share` on "Launch plan", adds `dana` as commenter and `Contractors` as viewer, invites `client@example.com`, creates a 14-day viewer link, copies it; the anonymous context opens the link and sees the read-only sheet with `Expires in 14 days`; `own` revokes; the anonymous context reloads and sees `This link is no longer valid`.
- `guest_accepts_and_sees_only_granted_sheet` — FR-F036-07, FR-F036-08: the guest context opens `accept_url`, enters a display name, lands on "Launch plan"; the workspace switcher lists only "Ops" and a direct URL to another sheet shows not-found.
- `sheet_viewer_narrows_workspace_editor` — FR-F036-04: `dana` (workspace editor via group, sheet viewer) opens "Launch plan" and sees read-only affordances while another sheet in "Ops" is editable.
- `deny_hides_dashboard` — FR-F036-04: `dana` opens dashboard "Exec" and sees the not-found page; `own` sees the deny row in the share dialog with the `Ban` icon.
- `editor_cannot_change_sharing` — FR-F036-15: `eli` opens `Share` and sees the read-only list with `Only owners and admins can change sharing`.
- `link_holder_has_no_discovery` — FR-F036-12: the anonymous context on the landing page has no search box, workspace navigation, or row editing; a direct `/w/` URL redirects to login.
- `keyboard_only_share_flow` — FR-F036-14, NFR-F036-03: no mouse; open dialog, Tab to `dana`, change role with arrows, Tab to `Copy link`, Enter; live region announces `Link copied`; Escape returns focus to `Share`.

Evidence: Playwright traces and videos under `testing/evidence/F036/e2e/`.
