---
id: T107
type: task
status: planned
parent_epic: E006
parent_feature: F027
parent_story: S054
depends_on: [S054]
owned_paths: [crates/domain/src/compliance/**, crates/persistence/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, testing/features/F027/api/**, testing/features/F027/frontend/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F027

## Objective

Implement access-review generation, flagging, storage as JSON and CSV, decision recording with real revocation, the list route, and the review pages.

## Specification

- Owned paths: `crates/domain/src/compliance/{review.rs, review_query.rs, decisions.rs}`, `crates/persistence/src/compliance/review_repository.rs`, `services/api/src/compliance/handlers_review.rs`, `services/worker/src/compliance/access_review.rs`, `apps/web/src/features/compliance/{AccessReviewList.tsx, AccessReviewDetail.tsx, DecisionTable.tsx, ReviewScopePicker.tsx}`
- Contract/input: `GenerateAccessReviewRequest { scope: "tenant" | "workspace:{id}", as_of? }` or `{ report_id, decisions: [ { principal_id, decision: keep|revoke, note? } ] }`; list query `{ cursor?, limit? ≤ 100, scope? }`.
- Output/behavior: routes `GET /api/v1/compliance/access-reviews`, `POST /api/v1/compliance/access-reviews`; `review_query.rs` composes the report from one set-based named repository query per principal kind (users, guests) over F003 `role_bindings` and `resource_acls`, F036 `shares` and `share_links`, F038 `api_tokens` and `sessions.last_seen_at`, and F016 `activity_entries`, each read through that feature's repository; `AccessReviewRepository::insert_review_with_principals` writes the parent row and one `access_review_principals` row per principal in one `UnitOfWork`, setting `flag_reason` to `inactive_90d` for principals idle over 90 days and `stale_guest_link` for guest links older than 30 days, and `flagged_count` to the count of flagged rows; `report.json` and `report.csv` renderings are stored under `access-reviews/<tenant>/<id>/` for download while the queryable report lives in the child table; `decisions.rs` upserts `access_review_decisions` rows and applies `revoke` through F003 `acl::remove_principal`, F036 `share_links::revoke`, and F038 `api_tokens::revoke`, setting each row's `outcome` and writing `access-review.decide` per decision; events `access-review.generated.v1`; `AccessReviewResponse { id, scope, as_of, principal_count, flagged_count, decided_count, download_json, download_csv }` with `decided_count` from `count_decided` and the decision list kept as a JSON array in the DTO while stored as rows; UI lists reports, shows the detail table with flagged rows first, supports bulk `revoke` of flagged guests, and shows per-decision outcome.
- Data access: `review.rs`, `review_query.rs`, `decisions.rs`, `handlers_review.rs`, and `services/worker/src/compliance/access_review.rs` hold no SQL. `AccessReviewRepository` in `crates/persistence/src/compliance/review_repository.rs` owns `access_reviews`, `access_review_principals`, and `access_review_decisions`, and exposes `insert_review_with_principals`, `list_reviews_by_scope` (cursor), `list_principals_flagged_first`, `upsert_decisions`, and `count_decided`; no other class writes those tables and no generic query hatch is exposed (decision section 2.1).
- Dependencies: T106 router and storage helpers; F003, F036, F038 revocation APIs; F016 activity entries.
- Feature flag: `F027_FEATURE`

## TDD

- Failing test first: `testing/features/F027/api/review_tests.rs::access_review_lists_roles_shares_links_tokens`, `::access_review_flags_inactive_and_stale_guests`, `::access_review_revoke_removes_acl_and_tokens`, `::access_review_list_filters_by_scope`, `::access_review_keep_writes_audit_only`, `::access_review_foreign_report_not_found`, `::access_review_redecide_updates_existing_row`, `::access_review_flagged_count_matches_principal_rows`; `testing/features/F027/frontend/DecisionTable.test.tsx::flagged_rows_first`, `::decision_table_bulk_revoke_flagged`
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
