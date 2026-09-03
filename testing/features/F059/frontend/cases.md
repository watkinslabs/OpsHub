# F059 frontend cases

File: `testing/features/F059/frontend/{PublishDialog.test.tsx,PublicationsListPage.test.tsx,PublicRenderPage.test.tsx,EmbedRenderPage.test.tsx,FreshnessBanner.test.tsx}`. Vitest with MSW. Flag `F059_FEATURE`.

- `publish_dialog_reveals_token_once` — FR-F059-13: after publish the token and snippet appear with copy buttons; reopening shows masked token.
- `origin_editor_rejects_http` — FR-F059-01: `http://` origin blocked inline; `https://` accepted up to 10.
- `expiry_picker_caps_at_30_days` — FR-F059-01: dates beyond 30 days disabled.
- `list_shows_status_and_view_counts` — FR-F059-11: rows show active, expired, revoked badges and `view_count_7d`.
- `rotate_and_revoke_actions_confirm` — FR-F059-02, FR-F059-08: confirm dialogs call `rotateToken` and `revokePublication`.
- `shows_freshness_banner_when_stale` — FR-F059-05: `stale: true` renders "Data as of" text with failure note.
- `hides_freshness_when_disabled` — FR-F059-05: `show_freshness: false` renders no banner but header still parsed.
- `shows_error_state_with_reason` — FR-F059-03: `error` render shows reason text and no widgets.
- `shows_unavailable_for_404` — FR-F059-08: 404 renders "This link is no longer available".
- `public_page_has_no_navigation_or_edit` — FR-F059-04: no app shell, links, or mutation controls in DOM.
- `posts_height_only_to_allowed_origin` — FR-F059-07: `postMessage` called with allowed origin, never `*`.
- `polls_at_refresh_interval` — FR-F059-05: query refetches every `refresh_interval_s`.

Evidence: Vitest JUnit under `testing/evidence/F059/frontend/`.
