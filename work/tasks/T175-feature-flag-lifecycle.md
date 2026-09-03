---
id: T175
type: task
status: planned
parent_epic: E000
parent_feature: F044
parent_story: S088
depends_on: [T174]
owned_paths: [automation/xtask/src/release.rs, testing/features/F044/api/**, testing/features/F044/frontend/**, testing/features/F044/accessibility/**]
feature_flag: F044_FEATURE
branch: t175-feature-flag-lifecycle
started_at: null
finished_at: null
---

# T175 — Feature-flag lifecycle

## Identity

- Parent story: `S088` Release evidence
- Owner: platform
- Branch: `t175-feature-flag-lifecycle`
- Decision references: `docs/architecture-decisions.md` section 9 (one flag per suite, off by default); spec section 10 flag decision; `docs/capability-contracts.md` row F044

## Objective

Implement `check-flags`: registry parsing, ticket and harness parity, code-reference scanning, and lifecycle state rules, plus the shared expected/found output style used by every F044 command.

## Specification

- Owned paths: `automation/xtask/src/release.rs` (`FlagDef`, `FlagState`, `FlagDefault`, `load_flags`, `check_flag_registry`, `check_flag_references`, `check_flag_lifecycle`, `check_flags`, `drift_message(expected, found)`)
- Contract/input: `crates/contracts/src/feature_flags.rs` with `pub const FLAGS: &[FlagDef]` entries parsed by a line-oriented reader (`key`, `feature`, `default`, `state`, `introduced` fields in any order); references found by scanning `crates/`, `services/`, `apps/` for `cfg(feature = "<KEY>")`, `flags.enabled("<KEY>")`, `useFlag('<KEY>')`; milestone completion derived from epics whose features are all archived
- Output/behavior: `flag.name` (ticket flag not `<id>_FEATURE` or default not `off`), `flag.unregistered` (in-progress or archived feature without entry), `flag.missing_ticket`, `flag.harness_mismatch` (`feature.toml` flag differs), `flag.unknown_reference <path>:<line>`, `flag.stale` (archived feature still `Active` two milestones after its epic completed), `flag.premature_default` (`Graduated` while feature not archived), `flag.removed_reference`; absent registry prints `skipped` and passes; `--json` includes `checked: { flags, references }`; drift messages use `expected: <x>, found: <y>`
- Dependencies: T174 (shared `release.rs` reporter helpers)
- Feature flag: `F044_FEATURE`
- Budget: reference scan over 20,000 files under 2 s (reuses the F041 streaming walker)

## TDD

- Failing test first: `testing/features/F044/api/flag_tests.rs::ticket_flag_name_or_default_wrong_reported`, `::inprogress_feature_without_registry_entry_reported`, `::registry_entry_without_ticket_reported`, `::harness_toml_flag_mismatch_reported`, `::unregistered_flag_reference_reported_with_line`, `::archived_feature_with_stale_flag_reported`, `::graduated_flag_on_unarchived_feature_is_premature`, `::removed_flag_reference_reported`, `::absent_registry_skipped`, `testing/features/F044/frontend/output_tests.rs::check_flags_json_shape`, `testing/features/F044/accessibility/output_tests.rs::expected_found_pairs_in_plain_text`
- Targeted command: `cargo xtask test-feature F044`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F044/fixtures/flags` with a registry source, Rust and TypeScript files referencing flags, and a work tree with planned, in-progress, and archived features across two milestones

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `check-flags` dispatched from `main()`; live repository passes with the registry skipped
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S088
- [ ] `finished_at` recorded
