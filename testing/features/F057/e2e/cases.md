# F057 e2e cases

File: `testing/features/F057/e2e/assets.spec.ts`. Playwright against seeded entitled and unentitled tenants with the rendition backend fake. Flag `F057_FEATURE`.

- `register_render_rights_approve_collect_archive` — FR-F057-01, FR-F057-03, FR-F057-05, FR-F057-06, FR-F057-08, FR-F057-09: full lifecycle from register to archive with `Usable` badge after approval.
- `expired_rights_shows_not_usable` — FR-F057-05: set `valid_until` yesterday → badge `Not usable: rights expired`.
- `rejected_approval_shows_reason` — FR-F057-06: approver rejects with reason; drawer shows reason.
- `unentitled_tenant_sees_upsell` — FR-F057-11: unentitled user opens `/w/{id}/assets` and sees the upsell.
- `viewer_has_no_mutation_controls` — FR-F057-13: viewer sees library and drawer read-only.
- `rendition_failure_retry` — FR-F057-14: backend fake fails three times; editor clicks Retry; thumbnail appears.

Evidence: Playwright traces and videos under `testing/evidence/F057/e2e/`.
