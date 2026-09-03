# F001 e2e cases

File: `testing/features/F001/e2e/{checkout.spec.ts,gates.spec.ts}`. Playwright plus shell steps against the fixture clone and a throwaway GitHub repository. Flag `F001_FEATURE`.

- `clean_checkout_builds_rust_and_web` — FR-F001-01, FR-F001-04: fresh clone → `cargo build --workspace` and `pnpm --filter web build` exit 0 within the cold budget.
- `dev_server_status_page_reports_health` — FR-F001-05: `pnpm --filter web dev` → browser opens `/status` → badge `ok` after the mocked API answers; stopping the API flips it to `unreachable`.
- `clean_pr_passes_all_five_checks` — FR-F001-06, FR-F001-14: PR with a valid ticket change → five green checks, merge allowed, evidence uploaded.
- `poisoned_pr_cannot_merge` — FR-F001-08: PR whose commit body carries a forbidden token → `policy` red, merge button disabled.
- `oversized_file_pr_cannot_merge` — FR-F001-09: PR adding a 501-line file → `line-limit` red with the limit message.
- `non_maintainer_push_to_main_rejected` — FR-F001-06 (permission-negative): contributor token `git push origin main` → rejected by branch protection; required checks unchanged.

Evidence: Playwright traces, shell transcripts, and check-run JSON under `testing/evidence/F001/e2e/`.
