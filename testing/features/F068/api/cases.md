# F068 api cases

F068 owns no route, so this lane is not an HTTP lane. It holds the two kinds of proof that need no database: `trybuild` compile-fail expectations under `testing/features/F068/api/ui/`, which are the primary evidence that a rule cannot be forgotten, and connection-free unit cases over the statement builder, the cursor codec, and the error mapping. Files: `testing/features/F068/api/{compile_fail_tests.rs,base_tests.rs,cursor_tests.rs,user_repository_tests.rs,error_mapping_tests.rs}` plus `api/ui/*.rs`. Flag `F068_FEATURE`.

- `hand_written_repository_impl_does_not_compile` — FR-F068-02: `api/ui/hand_written_repository.rs` writes `impl Repository for MyRepository` in a downstream crate; the expected stderr is `error[E0603]: module 'sealed' is private`, so a second implementation that skips the tenant predicate cannot exist.
- `spec_cannot_return_sql_text` — FR-F068-03: `api/ui/spec_returning_sql.rs` adds `fn where_clause(&self) -> String` to a `RepositorySpec` implementation; the trait has no such member and the build fails, so a specification cannot smuggle a predicate.
- `foreign_column_is_rejected_at_compile_time` — FR-F068-03: `api/ui/foreign_column.rs` uses a `Column<GroupSpec>` in a `UserFilter`; the type parameter mismatch fails the build.
- `two_live_repository_handles_do_not_compile` — FR-F068-11: `api/ui/two_handles.rs` holds `uow.repo::<UserSpec>()` while calling `uow.repo::<GroupMemberSpec>()`; the second mutable borrow fails, so repositories are used in sequence on one transaction.
- `unit_of_work_use_after_commit_does_not_compile` — FR-F068-11: `api/ui/use_after_commit.rs` calls `uow.repo()` after `uow.commit()`; the moved value fails the build, so no handle outlives the transaction.
- `purge_ctx_requires_a_grant` — FR-F068-09: `api/ui/purge_without_grant.rs` builds a `PurgeCtx` from a `TenantCtx`; there is no such constructor, no `Default`, and no `From`, so the build fails.
- `select_always_binds_tenant_predicate` — FR-F068-04, NFR-F068-02: the SQL captured from `QueryBuilder` for `get`, `list`, and each named query starts its `where` clause with `tenant_id = $1`; the assertion runs over every registered specification.
- `select_adds_soft_delete_filter_by_default` — FR-F068-04: `Visibility::Live` adds `and deleted_at is null`; `Visibility::Deleted` inverts it; `Visibility::Any` omits it; `list` defaults to `Live`.
- `update_statement_carries_expected_version` — FR-F068-05: the built statement contains `version = $` in the `where` clause and `version = version + 1` in the `set` clause, and no `list` or `get` statement contains `offset`.
- `field_diff_covers_changed_columns_only` — FR-F068-06: a patch touching `display_name` yields a diff naming that column alone, computed by the base from `COLUMNS`, with `before` and `after` values present.
- `event_mapping_is_total_over_mutations` — FR-F068-07: `UserSpec::event` returns `user.created.v1`, `user.updated.v1`, `user.deactivated.v1`, `user.updated.v1`, and `EventName::Silent` for the five operations, and every `Named` value appears in `docs/capability-contracts.md`.
- `cursor_round_trips_and_rejects_tampering` — FR-F068-10: a payload encodes and decodes intact; a flipped byte, a changed `filter_hash`, and a 25-hour-old `issued_at` each yield `InvalidCursor`.
- `unknown_sort_key_is_invalid_sort` — FR-F068-10: a sort key outside `S::SORTABLE` is rejected before any statement is built.
- `find_by_email_uses_the_citext_column` — FR-F068-13: the built statement compares `email = $2` with no `lower()` wrapper, matching F002's `citext` column and `users_tenant_email_idx`.
- `crate_surface_has_no_escape_hatch` — FR-F068-13, NFR-F068-02: the crate's public items contain no `query`, `execute`, `exec`, `raw`, `sql`, or `pool` member, no `Deref` to a SQLx type, and no re-exported SQLx type.
- `errors_map_to_the_documented_status_codes` — NFR-F068-02: `VersionConflict` maps to `409 conflict`, `NotFound` to `404 not_found`, `InvalidCursor` and `InvalidSort` to `400 invalid` with `field_errors.cursor` and `field_errors.sort`, `Forbidden` to `403 denied`; `Display` output carries no row value, email, or bound parameter.

Evidence: `trybuild` expectation files and JUnit output under `testing/evidence/F068/api/`.
