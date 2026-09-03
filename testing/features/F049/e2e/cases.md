# F049 e2e cases

File: `testing/features/F049/e2e/{locale.spec.ts,pseudo.spec.ts}`. Playwright against seeded tenants with projects `berlin` (`TZ=Europe/Berlin`) and `saopaulo` (`TZ=America/Sao_Paulo`). Flag `F049_FEATURE`; `pseudo.spec.ts` also needs `F049_PSEUDO_LOCALE=true`.

- `admin_changes_tenant_locale_and_preview_updates` — FR-F049-02, FR-F049-11: admin opens `/admin/locale`, picks `Deutsch (Deutschland)` and `Europe/Berlin`, preview shows `03.09.2026` and `1.234.567,89`, saves, toast `Locale saved`; a second user's next page load shows German formats.
- `user_override_switches_language_without_reload` — FR-F049-03, FR-F049-12: user opens `/me/locale`, picks `Português (Brasil)` and `America/Sao_Paulo`, saves; header text switches to Portuguese and a datetime cell shows `09:00` with no navigation.
- `stale_tenant_settings_show_conflict_banner` — FR-F049-11: second admin session saves first; first session's save shows the conflict banner and reload restores current values.
- `non_admin_sees_denied_on_admin_locale` — FR-F049-11, NFR-F049-02: editor visits `/admin/locale` → denied page with link to `/me/locale`.
- `dst_boundary_renders_correctly_per_project` — FR-F049-06: row with datetime `2026-03-29T00:30:00Z` shows `02:30` in `berlin` and `21:30` (previous day) in `saopaulo`.
- `every_route_renders_only_wrapped_strings` — FR-F049-13: pseudo run visits every registered route and fails on any visible text not wrapped in `[!!! … !!!]` outside the user-data allowlist.
- `unicode_name_round_trips` — FR-F049-07: sheet named with combining marks and emoji saves and lists identically after reload.

Evidence: Playwright traces and videos under `testing/evidence/F049/e2e/`.
