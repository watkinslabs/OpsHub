# F017 e2e cases

File: `testing/features/F017/e2e/files.spec.ts`. Playwright against seeded tenant with MinIO and the ClamAV stub. Flag `F017_FEATURE`.

- `upload_scan_preview_download` — FR-F017-01, FR-F017-03, FR-F017-04, FR-F017-05, FR-F017-07: `eli` drops `spec.pdf` on row "Kickoff", progress reaches 100 %, badge turns `Clean`, thumbnail appears, `Download` opens a MinIO URL that returns 200.
- `eicar_upload_is_quarantined` — FR-F017-04, FR-F017-05: `eli` uploads `eicar.txt`; badge shows `Quarantined` with signature; no download for `eli` or admin.
- `disallowed_type_shows_field_error` — FR-F017-02: dropping `tool.exe` shows the `not_allowed` message inline.
- `version_and_proof_approval` — FR-F017-08, FR-F017-11, FR-F017-12: `eli` uploads version 2, opens `Versions` and sees both, requests review from `rae` and `ron`; each opens `/files/{id}/proof` and approves; card shows `Approved 2/2`.
- `rejection_requires_reason_and_closes_proof` — FR-F017-12: `rae` rejects with a reason; card shows `Rejected` and `ron` sees decisions closed.
- `new_version_supersedes_proof` — FR-F017-13: with an open proof, `eli` uploads version 3; proof panel shows `Superseded`.
- `viewer_cannot_upload_or_delete` — FR-F017-15: `vic` sees cards and can download clean files but has no upload, delete, or version controls.
- `keyboard_only_upload` — FR-F017-14, NFR-F017-03: no mouse; Tab to the drop zone, Enter opens the picker, file chosen, live region announces `spec.pdf scanned clean`.

Evidence: Playwright traces and videos under `testing/evidence/F017/e2e/`.
