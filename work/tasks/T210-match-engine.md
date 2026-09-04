---
id: T210
type: task
status: planned
parent_epic: E008
parent_feature: F053
parent_story: S105
depends_on: [T209]
owned_paths: [crates/domain/src/datamesh/**, crates/persistence/src/datamesh/**, services/api/src/datamesh/**, services/worker/src/datamesh/**, testing/features/F053/api/**, testing/features/F053/requirements/**, testing/features/F053/performance/**]
feature_flag: F053_FEATURE
branch: t210-match-engine
started_at: null
finished_id: null
finished_at: null
---

# T210 — Match engine

## Identity

- Parent story: `S105` Reference mapping
- Owner: platform
- Branch: `t210-match-engine`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 7; `docs/capability-contracts.md` row F053

## Objective

Implement key normalization, the streaming match engine that fills `datamesh_matches` and flags ambiguous matches, and the preview route that reports counts and a redacted sample without writing cells.

## Specification

- Owned paths: `crates/domain/src/datamesh/{matching.rs, preview.rs, plan.rs}`, `crates/persistence/src/datamesh/match_repository.rs`, `services/worker/src/datamesh/{mod.rs, match_engine.rs}`, `services/api/src/datamesh/handlers_preview.rs`
- Contract/input: `normalize_key(value, Normalize)` where `trim` strips edges, `case_insensitive` lowercases, `whitespace` collapses internal runs, `date` reduces datetimes to the tenant-local date, `exact` leaves the raw value; `key_hash = blake3(normalized key parts joined by 0x1f)`; `compute_matches(mapping, source_rows, target_rows)` reads the mapping's `datamesh_mapping_match_keys` rows in `ordinal` order, streams both sheets through the F006 row list by `key_column_ids` in pages of 5,000, and performs a hash join bounded at 500 MB, spilling beyond that into the run-scoped temporary table owned by `MatchRepository::spill_batch_insert` / `drain_spill_batch`; `plan_changes(matches, source_rows, target_rows, cursor, field_maps)` returns `ChangePlan { writes, write_backs, creates, clears, conflicts }` without side effects.
- Output/behavior: `datamesh_matches` rebuilt per mapping version by `MatchRepository::replace_matches_for_mapping` with one row per source row and unique target rows; one-to-many and many-to-one keys produce `ambiguous_match` plan entries and no match rows; `POST /api/v1/datamesh/mappings/{id}/preview` returns `PreviewResponse { matched, unmatched_source, unmatched_target, would_create, would_update, would_clear, conflicts, sample }` with the sample limited to 50 rows and columns the caller cannot read removed, cached by `(mapping_id, version)` for 10 minutes, and `unavailable` with `error_code = preview_timeout` after 30 seconds; nothing is written to `cells`, `cell_links`, or `datamesh_conflicts` by preview.
- Data access: `matching.rs`, `preview.rs`, `plan.rs`, and `match_engine.rs` contain no SQL, connection, or temporary-table statement; match keys and field maps come from `MappingRepository::list_match_keys` and `list_field_maps`, match rows are written and streamed through `MatchRepository::replace_matches_for_mapping` and `stream_matches_by_key_hash`, and the spill table is created, filled, and drained only by `MatchRepository` inside the caller's `UnitOfWork` (decision section 2.1).
- Dependencies: T209 tables and mapping service; F006 row list; F007 column types; F009 row hierarchy readers; F048 guard on the route.
- Feature flag: `F053_FEATURE`.

## TDD

- Failing test first: `testing/features/F053/api/match_tests.rs::normalize_key_per_mode`, `::key_hash_is_stable_across_runs`, `::match_engine_matches_fixture_840_rows`, `::match_engine_flags_ambiguous_matches`, `::match_engine_leaves_unmatched_both_sides`, `::plan_changes_honours_overwrite_modes`, `::plan_changes_detects_both_changed`; `testing/features/F053/api/preview_tests.rs::preview_counts_match_fixture`, `::preview_writes_nothing`, `::preview_redacts_unreadable_columns`, `::preview_cached_by_version`, `::preview_viewer_without_sheet_read_denied`, `::match_keys_hash_in_ordinal_order`, `::spill_path_writes_and_drains_through_repository`; `testing/features/F053/performance/preview_bench.rs::preview_100k_by_100k_under_30s`
- Targeted command: `cargo xtask test-feature F053`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `Vendors master` and `Purchase requests` sheets with 840 matches, 12 unmatched source, 2 ambiguous keys; 100,000-row generators with 5 % ambiguous keys for the benchmark; memory-limit harness for the spill path

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Preview route mounted; engine reused by the S106 sync consumer without duplication
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S105
- [ ] `finished_at` recorded
