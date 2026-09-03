---
id: T107
type: task
status: planned
parent_epic: E006
parent_feature: F027
parent_story: S054
depends_on: [S054]
owned_paths: [crates/domain/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, testing/features/F027/api/**, testing/features/F027/frontend/**]
feature_flag: F027_FEATURE
branch: t107-access-reports
started_at: null
finished_at: null
---

# T107 — Access reports

## Identity

- Parent story: `S054` Access review
- Owner: platform
- Branch: `t107-access-reports`
- Decision references: `docs/architecture-decisions.md` sections 3, 4; `docs/capability-contracts.md` row F027

## Objective

Implement access-review generation, flagging, storage as JSON and CSV, decision recording with real revocation, the list route, and the review pages.

## Specification

- Owned paths: `crates/domain/src/compliance/{review.rs, review_query.rs, decisions.rs}`, `services/api/src/compliance/handlers_review.rs`, `services/worker/src/compliance/access_review.rs`, `apps/web/src/features/compliance/{AccessReviewList.tsx, AccessReviewDetail.tsx, DecisionTable.tsx, ReviewScopePicker.tsx}`
- Contract/input: `GenerateAccessReviewRequest { scope: "tenant" | "workspace:{id}", as_of? }` or `{ report_id, decisions: [ { principal_id, decision: keep|revoke, note? } ] }`; list query `{ cursor?, limit? ≤ 100, scope? }`.
- Output/behavior: routes `GET /api/v1/compliance/access-reviews`, `POST /api/v1/compliance/access-reviews`; `review_query.rs` runs one set-based query per principal kind (users, guests) joining F003 `role_bindings`, `resource_acls`, F036 `shares` and `share_links`, F038 `api_tokens`, `sessions.last_seen_at`, and `activity_entries`; flags inactive > 90 days and guest links > 30 days; stores `report.json` and `report.csv` under `access-reviews/<tenant>/<id>/`; `decisions.rs` applies `revoke` through F003 `acl::remove_principal`, F036 `share_links::revoke`, and F038 `api_tokens::revoke`, writing `access-review.decide` per decision; events `access-review.generated.v1`; `AccessReviewResponse { id, scope, as_of, principal_count, flagged_count, decided_count, download_json, download_csv }`; UI lists reports, shows the detail table with flagged rows first, supports bulk `revoke` of flagged guests, and shows per-decision outcome.
- Dependencies: T106 router and storage helpers; F003, F036, F038 revocation APIs; F016 activity entries.
- Feature flag: `F027_FEATURE`

## TDD

- Failing test first: `testing/features/F027/api/review_tests.rs::access_review_lists_roles_shares_links_tokens`, `::access_review_flags_inactive_and_stale_guests`, `::access_review_revoke_removes_acl_and_tokens`, `::access_review_list_filters_by_scope`, `::access_review_keep_writes_audit_only`, `::access_review_foreign_report_not_found`; `testing/features/F027/frontend/DecisionTable.test.tsx::flagged_rows_first`, `::decision_table_bulk_revoke_flagged`
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: 40 principals with 3 stale guests and 2 inactive users; MSW handlers for review pages

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Review routes and job wired behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S054
- [ ] `finished_at` recorded
