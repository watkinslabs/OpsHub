---
id: E007
type: epic
status: planned
owner: platform
target_milestone: M6
branch: e007-portfolio-and-resource-management
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` rows F031, F032, F033, F034
- Product spec: `docs/product-capability-spec.md` section 5.7 (PPM-01 through PPM-04), section 10 resource actuals decision

# E007 — Portfolio and resource management

## Outcome

A PMO can group provisioned projects into portfolios and see, for every project, its status, schedule variance, budget consumption, risk exposure, business value, and health on one governed surface that preserves source project IDs, last refresh time, missing-data state, and the viewer's permission boundary. Health is computed from weighted schedule, budget, scope, risk, and resource indicators, can be overridden with a recorded reason, and is enforced through stage gates that require evidence, an approver, a decision, a date, and an audit event. Resource managers maintain people and placeholder profiles with skills, availability, and cost rates, allocate them to projects by period with planned hours or percent, and see capacity that accounts for working calendars, leave, holidays, and part-time availability. Workload balancing surfaces over-allocation conflicts, native time entries record actuals, imported actuals are flagged external and reconciled under audit, and planned versus actual effort and cost are visible per task, project, and portfolio.

## Scope

- Included: portfolio records and membership; scheduled and on-demand rollup projections over F015 projects using F021 permission-aware queries; configurable weighted health models with manual override; stage gate definitions, submission with evidence, approval-backed decisions, and audit; governed project intake requests that provision through F015 templates (this epic absorbs the Control Center governance scope from spec 5.11); resource profiles, skills, availability, cost rates; period-based allocations with hours or percent, role, and confidence; capacity accounting per working calendar; workload and conflict queries; native time entries; external actuals import with audited reconciliation; planned versus actual effort and budget summaries.
- Excluded: project templates and baselines themselves (F015), dependency and critical-path scheduling (F012), report and dashboard rendering of rollup data beyond the portfolio page (F021, F023), approval routing engine (F020), Resource Management forecasting and Control Center entitlement packaging (F048 and E008 modules), AI risk insights over portfolio data (F040).

## Child features

- F031 Portfolio rollups: portfolios, project membership, rollup projections with source IDs, refresh time, missing-data state, and permission boundaries.
- F032 Project health/governance: weighted health indicators with override and reason, stage gates with evidence and decisions, governed project intake.
- F033 Resources/capacity: resource profiles, skills, availability, cost rates, period allocations, and capacity calculation.
- F034 Workload/actuals: workload and conflict queries, native time entries, external actuals reconciliation, planned versus actual effort and budget.

## Exit criteria

- [ ] Spec Phase 6 scenario passes end to end: a PMO administrator provisions three projects from a template, adds them to a portfolio, refreshes the rollup, sees per-project schedule, budget, risk, value, and health with source IDs and last refresh, overrides one project's health with a reason, submits and approves a stage gate with evidence, allocates two resources across the projects, sees an over-allocation conflict, records time entries, imports external actuals, reconciles one conflict, and views planned versus actual effort; a portfolio viewer without access to one project sees that project as denied with no leaked values.
- [ ] Every child feature has passed its permission-negative, tenant-isolation, audit, migration, accessibility, and performance gates.
- [ ] `portfolio.rollup-refreshed.v1`, `project-health.computed.v1`, `stage-gate.decided.v1`, `capacity.computed.v1`, `workload-conflict.detected.v1`, and `time-entry.reconciled.v1` are observed in the outbox for the scenario above.
- [ ] Feature flags `F031_FEATURE` through `F034_FEATURE` roll back independently with verified down migrations.
