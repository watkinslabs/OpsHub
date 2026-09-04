# F073 frontend cases

File: `testing/features/F073/frontend/{WhatsNewPanel.test.tsx,AnnouncementItem.test.tsx,InterruptModal.test.tsx,HelpDrawer.test.tsx,HelpIndexList.test.tsx,SafeMarkdown.test.tsx,useHelpContext.test.ts}`. Vitest with MSW. Flag `F073_FEATURE`.

- `panel_lists_severity_chip_title_and_date` — FR-F073-01: three items render with a severity chip, title, relative date and a two-line body clamp; `Learn more` appears only where a slug is present.
- `dismissed_item_has_no_dismiss_control` — FR-F073-06: under `Show dismissed` the item is muted, shows its dismissal date, and exposes no dismiss control, because the action cannot be undone.
- `dismiss_removes_item_optimistically` — FR-F073-06: dismissing removes the row immediately and invalidates only the list key; a failed mutation restores the row with the error banner.
- `empty_panel_offers_help_index` — FR-F073-01: with no visible announcements the panel shows the empty state and a link into the help index.
- `passive_severity_never_renders_modal` — FR-F073-08: an `info` item with `interrupting: false` renders in the list only.
- `modal_later_leaves_item_undismissed` — FR-F073-09: `Later` closes the modal, the item stays in the panel with its dismiss control, and no dismissal request is issued.
- `modal_absent_while_editor_open` — FR-F073-09: with an open sheet editor in context the interrupting item degrades to a list row.
- `raw_html_in_body_is_dropped` — FR-F073-13: `SafeMarkdown` renders the injection corpus as text; no image, iframe, style or script element appears in the tree.
- `non_https_anchor_renders_as_text` — FR-F073-13: an anchor with an unsupported scheme renders as plain text; an `https:` anchor carries `rel="noopener noreferrer"`.
- `drawer_opens_on_context_and_lists_related` — FR-F073-10: the drawer opens with the article mapped to the current screen key and the remaining contextual articles beneath it.
- `unmatched_context_renders_full_index` — FR-F073-10: `matched: false` renders the full index without an error state.
- `not_found_renders_index_with_note` — FR-F073-12: a 404 from the article read renders the contextual index with the moved-article note rather than an error page.
- `fallback_locale_shows_shown_in_english_note` — FR-F073-11: `translation_fallback: true` renders the note above the body.
- `drawer_restores_focus_to_trigger` — NFR-F073-03: `Escape` closes the drawer and focus returns to the control that opened it.
- `offline_serves_cached_list_read_only` — FR-F073-01: offline renders the last cached list with the offline chip and disables the dismiss control.
- `error_banner_shows_correlation_id` — NFR-F073-04: a 500 on the list renders the banner with `correlation_id` and retry.
- `surfaces_contact_no_third_party_origin` — FR-F073-14, NFR-F073-02: with MSW failing every unexpected origin, mounting the panel and the drawer issues requests to the OpsHub API only — no analytics, tag, font or content host.

Evidence: Vitest JUnit and the MSW request log under `testing/evidence/F073/frontend/`.
