# F012 e2e cases

File: `testing/features/F012/e2e/{gantt.spec.ts,shift.spec.ts}`. Playwright against seeded tenant. Flag `F012_FEATURE`.

- `link_tasks_and_successor_moves` — FR-F012-01, FR-F012-07, FR-F012-14: editor links "Design" → "Build" FS lag 2 days; arrow appears; "Build" bar starts two working days after "Design" ends; reload persists.
- `cycle_rejected_in_dialog` — FR-F012-03: linking "Test" → "Design" shows the cycle path inline and no arrow is drawn.
- `critical_path_toggle_highlights_chain` — FR-F012-08: toggle on → longest chain highlighted; toggle off → default colours.
- `drag_shift_preview_then_commit_persists` — FR-F012-11, FR-F012-12: drag "Design" +3 days, preview lists 15 rows, confirm, reload shows moved bars past the holiday.
- `keyboard_only_shift` — FR-F012-14, NFR-F012-03: focus bar, `Shift+ArrowRight` twice, confirm dialog; live region announces "Shifted 15 rows".
- `viewer_cannot_shift` — FR-F012-15: viewer sees bars, no drag handles, and the shift shortcut does nothing.
- `non_member_sees_not_found` — FR-F012-15: user outside the workspace opens the Gantt URL → not-found page.

Evidence: Playwright traces and videos under `testing/evidence/F012/e2e/`.
