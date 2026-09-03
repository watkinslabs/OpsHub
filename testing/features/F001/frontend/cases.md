# F001 frontend cases

File: `testing/features/F001/frontend/{StatusPage.test.tsx,cli_output.test.ts}`. Vitest with MSW. Flag `F001_FEATURE`.

No UI beyond status page: covered by `StatusPage.test.tsx`; the remaining product UI arrives with F005 onward. CLI output cases verify the developer-facing surface.

- `status_page_renders_ok_state` — FR-F001-05: `GET /healthz` → `{ status: "ok" }` renders badge `ok` with version text.
- `status_page_renders_degraded_checks` — FR-F001-05: `degraded` with a failed `database` check lists the failed dependency.
- `status_page_shows_unreachable_with_retry` — FR-F001-05: network error renders `unreachable` and a retry button that refetches.
- `status_page_offline_badge` — FR-F001-05: `navigator.onLine=false` renders the `offline` badge and disables retry.
- `status_page_loading_sets_aria_busy` — NFR-F001-03: pending query sets `aria-busy="true"` on the region.
- `status_route_hidden_when_flag_off` — FR-F001-05: `F001_FEATURE=off` does not register `/status`; navigation renders not-found.
- `status_page_emits_view_telemetry` — FR-F001-05: mount emits `status_page_viewed` with `state`.
- `cli_build_output_lists_five_binaries` — FR-F001-01: captured `cargo build --workspace` output names `api`, `worker`, `realtime`, `mcp`, `xtask` with `Finished`.
- `cli_blocked_line_format` — FR-F001-08: captured `audit-range` failure output matches `^BLOCKED: .+: forbidden token: .+$`.
- `cli_line_limit_output_format` — FR-F001-09: captured `line-limit` output matches `^"?.+"?: \d+ lines; limit is 500$`.

Evidence: Vitest JUnit under `testing/evidence/F001/frontend/`.
