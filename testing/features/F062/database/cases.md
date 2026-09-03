# F062 database cases

F062 owns no table and no migration. This lane proves that absence stays true, in `testing/features/F062/database/`. Flag `F062_FEATURE`.

- `feature_adds_no_migration_file` — NFR-F062-04: no file matching `services/api/migrations/*_design-system_*.sql` exists and the feature's owned paths contain no `.sql` file.
- `theme_and_density_are_browser_state_only` — FR-F062-04, FR-F062-06: the only persistence is `localStorage` keys `opshub.theme` and `opshub.density`; no cookie is set and no request carries the preference.
- `preferences_survive_reload_and_reset_cleanly` — FR-F062-04: a cleared `localStorage` falls back to `system` theme and `comfortable` density without an error or a flash.

Evidence: scan output and storage traces under `testing/evidence/F062/database/`.
