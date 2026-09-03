# F016 e2e cases

File: `testing/features/F016/e2e/comments.spec.ts`. Playwright against seeded tenant. Flag `F016_FEATURE`.

- `comment_mention_resolve_and_history` — FR-F016-01, FR-F016-04, FR-F016-08, FR-F016-09: `ana` opens row "Kickoff", posts "Check this @dana", `dana` replies in a second session, `ana` resolves; activity tab lists two `comment.created` and one `comment.resolved` entry.
- `mention_chip_renders_after_reload` — FR-F016-04, FR-F016-13: reload shows the mention as a chip with `dana`'s display name.
- `viewer_cannot_comment` — FR-F016-12: `vic` sees threads and the read-only message; no composer, edit, or resolve controls.
- `non_member_sees_not_found` — FR-F016-12: user outside the workspace opens the row URL with `tab=conversation` → not-found page.
- `edit_and_delete_own_comment` — FR-F016-06, FR-F016-07: `ana` edits within the window, `edited` label shows; deletes a parent with a reply, placeholder remains.
- `row_delete_and_restore_keeps_history` — FR-F016-14: delete row, restore from trash, threads visible and activity shows delete and restore entries.
- `keyboard_only_mention_and_submit` — FR-F016-13, NFR-F016-03: no mouse; `@`, ArrowDown, Enter, `Ctrl+Enter` posts the comment and the live region announces it.

Evidence: Playwright traces and videos under `testing/evidence/F016/e2e/`.
