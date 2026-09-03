# F046 e2e cases

File: `testing/features/F046/e2e/{collab.spec.ts,reconnect.spec.ts}`. Playwright with two editor contexts and one viewer context against realtime, API, and JetStream. Flag `F046_FEATURE`.

- `two_editors_converge_on_document` — FR-F046-04, FR-F046-14: Ana inserts "Goals" at top, Ben appends "Risks"; both documents show identical text and both see each other's avatar and cursor.
- `offline_edits_replay_after_reconnect` — FR-F046-09, FR-F046-10: Ben goes offline at rev 12, types two paragraphs, Ana makes 8 changes; Ben reconnects; Ben sees revs 13..20 then his edits acked at 21 and 22; texts converge.
- `changes_not_saved_after_thirty_seconds` — FR-F046-10: Ben offline 31 s → `Changes not saved` badge; closing tab shows unload prompt.
- `stale_sheet_patch_shows_conflict_take_theirs` — FR-F046-07, FR-F046-08: both edit cell Status; Ben sees the banner with "Done" vs "Blocked"; `Take theirs` shows "Done".
- `viewer_sees_presence_but_cannot_edit` — FR-F046-14: viewer sees `Read-only`, avatars, and live text; no typing possible.
- `presence_disappears_after_lease_expiry` — FR-F046-03: Ana's client stops renewing; after 30 s Ben's list no longer shows Ana.
- `revoked_editor_downgraded_live` — NFR-F046-02: admin removes Ben's editor grant; within 60 s Ben's badge reads `Read-only` with a toast.
- `keyboard_only_conflict_resolution` — NFR-F046-03: `Alt+Shift+C` focuses the banner, arrow to `Keep mine`, `Enter`; resolution announced.

Evidence: Playwright traces and videos under `testing/evidence/F046/e2e/`.
