---
id: T168
type: task
status: planned
parent_epic: E000
parent_feature: F042
parent_story: S084
depends_on: [T167]
owned_paths: [automation/xtask/src/policy.rs, testing/features/F042/api/**, testing/features/F042/accessibility/**, testing/features/F042/frontend/**]
feature_flag: F042_FEATURE
branch: t168-positive-control-self-test
started_at: null
finished_at: null
---

# T168 — Positive-control self-test

## Identity

- Parent story: `S084` Ticket/ownership audit
- Owner: platform
- Branch: `t168-positive-control-self-test`
- Decision references: `docs/architecture-decisions.md` section 9; `docs/capability-contracts.md` row F042

## Objective

Implement `self-test` so every detector, exemption, glob rule, and hook script is proven on each CI run, and finish the shared masked, accessible, deterministic output for all F042 commands.

## Specification

- Owned paths: `automation/xtask/src/policy.rs` (`self_test`, `controls::{clean, token_variants, policy_file_skip, glob_semantics, hooks_parse, hooks_executable}`)
- Contract/input: the compiled `Policy`; `.githooks/{pre-commit,commit-msg,pre-push}`; a synthetic active item with `services/api/src/sheets/**`
- Output/behavior: `self-test` runs each control and reports `policy.selftest <control name>: <expected> vs <actual>` for failures; controls are: clean text yields 0 findings; each token in lower, upper, mixed, zero-width-joined, and full-width form yields exactly one finding with the right token index; the repository rules file and `automation/xtask/src/policy.rs` are skipped by the staged scanner; `services/api/src/sheets/a/b.rs` matches and `services/api/src/sheetsx/b.rs` does not; `sh -n` succeeds for each hook; each hook has mode 0755; the summary line is `policy self-test passed (<n> controls)`; output honours `NO_COLOR`, masks tokens, and is byte-identical across runs
- Dependencies: T167 ownership matcher; T165 scanner
- Feature flag: `F042_FEATURE`
- Budget: under 500 ms

## TDD

- Failing test first: `testing/features/F042/api/selftest_tests.rs::self_test_passes_on_clean_checkout`, `::self_test_fails_when_control_is_broken` (policy compiled with an empty token list), `::self_test_reports_hook_not_executable`, `::self_test_reports_hook_syntax_error`, `testing/features/F042/accessibility/output_tests.rs::findings_never_contain_token`, `::no_color_disables_ansi`, `testing/features/F042/frontend/output_tests.rs::json_shape_for_audit_commands`, `::two_runs_byte_identical`
- Targeted command: `cargo xtask test-feature F042`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: scratch checkout with hooks copied; a fixture hook with a deliberate syntax error; a fixture hook with mode 0644

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `self-test` runs in the `gates.yml` validate step and passes on the live repository
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S084
- [ ] `finished_at` recorded
