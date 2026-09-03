---
id: B___
type: bug
status: planned
priority: P1
owner: [human-or-agent]
estimate: 1
target_milestone: M___
parent_epic: E___
depends_on: []
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: []
feature_flag: B____FEATURE
flag_default: off
branch: b___-[kebab-case-description]
started_at: null
finished_at: null
---

# B___ — [bug title]

## 1. Requirement specification

- Observed behavior: [measured behavior]
- Expected behavior: [contract]
- Reproduction: [deterministic steps and fixture]
- Scope: [included and excluded paths]

## 2. Root cause and repair

- Cause: [mechanism, not symptom]
- Repair: [code/data/API/UI change]
- Rollback: [safe reversal]

## 3. TDD and harness

- Failing regression test: `testing/features/B___/requirements/cases.md`
- Targeted command: `cargo xtask test-feature B___`
- Negative, permission, recovery, and concurrency cases: [list]

## 4. Exit criteria

- [ ] Regression test fails before repair and passes after repair.
- [ ] Production caller is verified.
- [ ] Relevant unit/API/database/UI/E2E gates pass.
- [ ] Audit, telemetry, release notes, and `finished_at` are recorded.
