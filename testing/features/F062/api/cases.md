# F062 api cases

F062 owns no HTTP route. This lane holds the negative controls that keep the UI layer free of server coupling, in `testing/features/F062/api/`. Flag `F062_FEATURE`.

- `ui_modules_perform_no_network_call` — NFR-F062-04: a `fetch` and `XMLHttpRequest` spy renders every story in the matrix and asserts zero calls originate from `apps/web/src/ui/**`.
- `no_primitive_renders_raw_html` — NFR-F062-02: a static scan plus a render pass proves no component under `apps/web/src/ui/**` uses `dangerouslySetInnerHTML`, including via a prop.
- `external_links_force_noopener` — NFR-F062-02: any link primitive given `target="_blank"` emits `rel="noopener noreferrer"` even when the caller passes its own `rel`.
- `theme_bootstrap_is_a_static_literal` — NFR-F062-02: the inline script in `index.html` contains no interpolation of a stored value and sets only the two root attributes.
- `ui_barrel_is_the_only_import_surface` — FR-F062-07: no file under `apps/web/src/features/**` imports a path deeper than `apps/web/src/ui`.

Evidence: spy logs and the static scan report under `testing/evidence/F062/api/`.
