---
id: F___
type: feature
status: planned
priority: P1
owner: [human-or-agent]
estimate: 3
target_milestone: M___
parent_epic: E___
depends_on: []
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: []
feature_flag: F____FEATURE
flag_default: off
branch: f___-[slug]
started_at: null
finished_at: null
---

# F___ — [Feature title]

## 1. Identity and dates

- Type: Feature ticket
- ID: `F___`
- Status: planned
- Priority: [P0/P1/P2/P3]
- Owner: [name/team]
- Estimate: [1/2/3/5/8/13 points]
- Target milestone: [M___]
- Parent epic: [E___ — title or N/A]
- Capability area: [area]
- Branch: `f___-[kebab-case-description]` (for feature tickets; use the matching lowercase type for bugs/spikes)
- Owned paths: [paths this ticket may change]
- Parallel safe: [true/false]
- Feature flag: `F____FEATURE`
- Flag default: off
- Started at: `YYYY-MM-DDTHH:MM:SS±HH:MM` or `N/A`
- Finished at: `YYYY-MM-DDTHH:MM:SS±HH:MM` or `N/A`

## 2. Requirement specification

### Problem and user outcome

[Who has the problem, current behavior, and desired measurable outcome.]

As a [persona], I want [capability], so that [outcome].

### Functional requirements

- **FR-F___-01:** The system shall [testable requirement].
- **FR-F___-02:** The system shall [testable requirement].

### Non-functional requirements

- **NFR-F___-01 Performance:** [target]
- **NFR-F___-02 Security/privacy:** [target]
- **NFR-F___-03 Accessibility:** [target]
- **NFR-F___-04 Reliability/observability:** [target]

### Scope

Included: [list]

Excluded: [list]

## 3. UX specification

- Entry points: [routes/actions]
- Primary flow: [numbered steps]
- Empty/loading/error/success states: [behavior]
- Permission-denied/conflict states: [behavior]
- Responsive behavior: [mobile/tablet/desktop]
- Keyboard, focus, screen-reader, contrast, motion: [requirements]
- Font/icon/design tokens: [shared system references]

## 4. Technical specification

### Rust backend

- Domain entities/value objects: [detail]
- Use cases/services: [detail]
- API endpoints and schemas: [method/path/request/response]
- Events/jobs/webhooks: [detail or N/A]
- Authorization policy: [roles, scopes, tenant rules]
- Validation, idempotency, concurrency: [detail]
- Error mapping: [typed error → HTTP response]

### PostgreSQL/SQLx

- Tables/columns and migration: [detail]
- Relationships/invariants: [detail]
- Indexes/query patterns: [detail]
- Audit events: [actions/fields]
- Retention/deletion: [detail]

### React/TypeScript

- Routes/screens/components: [detail]
- State/data fetching: [detail]
- API client calls: [detail]
- Optimistic updates/concurrency: [detail]
- Telemetry: [events]

## 5. TDD and isolated test harness

Tests must be written before production implementation. Test code belongs in the separate `testing/` area and is feature-gated; it is not mixed into live application code.

- [ ] Requirement tests for: FR-F___-01, FR-F___-02
- [ ] Failure/edge-case tests: [list]
- [ ] Permission-negative and tenant-isolation tests: [list]
- [ ] Rust unit tests: [modules]
- [ ] API contract/integration tests: [cases]
- [ ] Database migration/constraint tests: [cases]
- [ ] React component tests: [components/states]
- [ ] Browser E2E tests: [user flows]
- [ ] Accessibility tests: [keyboard/axe/screen-reader cases]
- [ ] Visual regression tests: [screens or N/A]
- [ ] Performance/load tests: [scenario/threshold or N/A]

### Fast fanout configuration

- Test harness path: `testing/features/F___/`
- Feature flag: `F____FEATURE`
- Fixture/seed factory: [location]
- Deterministic test data: [strategy]
- Mock/stub contracts: [services]
- Parallel isolation: [worker/tenant/database strategy]
- Targeted command: `[command with feature flag]`
- Full command: `[command enabling all feature flags]`
- CI artifact/evidence: [link]

## 6. Acceptance criteria

```gherkin
Feature: [feature title]

Scenario: [happy path]
  Given [initial state]
  When [user action]
  Then [observable result]

Scenario: [failure or permission path]
  Given [initial state]
  When [user action]
  Then [safe observable result]
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: [IDs, decisions, contracts, or none]
- Blocks: [IDs or none]
- Conflicts with: [IDs or none]
- External dependencies: [services/packages or none]
- Risks and mitigations: [list]
- Open questions and owner/date: [list]

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first. Empty until then.

| Date | Caused by | What changed | Why |
|---|---|---|---|

## 7.1 Agent handoff

### Implemented

[Concise summary]

### Files changed

[Paths]

### Commands and evidence

[Commands, results, artifact links]

### Known issues

[Issues or none]

### Follow-up tickets

[IDs or none]

### Migration and rollback

[Status and procedure]

## 8. Entry criteria — ready for implementation

- [ ] Requirements and non-goals approved
- [ ] UX states and design references complete
- [ ] API/data/security design complete
- [ ] Test cases written and harness location identified
- [ ] Feature flag and fanout strategy defined
- [ ] Fixtures and parallel test isolation defined
- [ ] Dependencies resolved or explicitly accepted
- [ ] Estimate, owner, milestone, and branch assigned
- [ ] Owned paths and dependency fields validated
- [ ] Feature flag and default state defined

## 9. Exit criteria — accepted and releasable

- [ ] All functional and non-functional acceptance tests pass
- [ ] TDD evidence shows tests preceded implementation
- [ ] Rust unit/API/integration/database tests pass
- [ ] React/component/E2E tests pass
- [ ] Permission-negative and tenant-isolation tests pass
- [ ] Accessibility and performance gates pass
- [ ] Targeted and full feature-gated test suites pass
- [ ] CI format/lint/typecheck/build/migration gates pass
- [ ] Audit, telemetry, logs, and alerts verified
- [ ] Security/privacy review complete
- [ ] Documentation and runbook updated
- [ ] All changed files are ≤500 lines and split by function/responsibility
- [ ] Comments are limited to implementation-specific gotchas and constraints
- [ ] Release notes, migration, feature flag, and rollback plan complete
- [ ] Human approval obtained for protected changes, if applicable
- [ ] Pull request approved and linked: [URL]
- [ ] `finished_at` recorded and file moved to `archived/`

## 10. Implementation checklist

- [ ] Add failing tests to isolated testing harness
- [ ] Implement migration/domain/API
- [ ] Implement React experience
- [ ] Run targeted fanout suite
- [ ] Run full release test matrix when requested
- [ ] Update docs and operational artifacts

## 10. Release notes

- [user-visible behavior, migration, flag, rollback]

## 11. Evidence and change log

- Test run links/artifacts: [links]
- Performance/accessibility evidence: [links]

| Date/time | Change | Author |
|---|---|---|
| YYYY-MM-DDTHH:MM:SS±HH:MM | Created | [name] |
