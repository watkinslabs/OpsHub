# Milestones

Every feature ticket declares a `target_milestone`. This file says what each milestone is, what it
contains, and how you know it is finished. Source: `docs/product-capability-spec.md` section 7 build
order and section 8 release gates. The feature tables are generated from the `target_milestone` of
every ticket, so this file and the backlog cannot disagree about scope.

## Gates that apply to every milestone

No milestone is complete until, for each of its features:

- happy-path and permission-negative acceptance tests pass;
- API contract and migration tests pass, and the down migration is exercised;
- audit events and notifications are verified, not assumed;
- accessibility and responsive checks pass on every surface it ships;
- the load profile for its scale tier passes (F067);
- every async path has a failure, retry and recovery test;
- the support runbook, analytics events and the flag rollback plan exist;
- `cargo xtask verify-release <ID>` records the evidence and the release signature (F044).

## M0 — Foundation and delivery control plane

Spec Phase 0. Epics E000. 5 features, 34 estimate points.

**Goal.** The control plane every later milestone is judged by exists and is enforced, not aspirational.

| Feature | Title | Epic |
|---|---|---|
| F041 | Work-item schema | E000 |
| F042 | xtask audit/gates | E000 |
| F043 | Fanout orchestration | E000 |
| F044 | Contract/release control | E000 |
| F067 | System scale and load validation | E000 |

**Exit criteria**

- [ ] Every gate runs in CI and in the git hooks, and a deliberately broken fixture fails each one.
- [ ] `validate-decisions`, `validate-plan`, `validate-work`, `check-contracts`, `check-persistence`, `check-migrations`, `test-all` and `self-test` pass on a clean clone.
- [ ] A lane can be claimed, isolated and released with evidence, and two lanes build concurrently without contending.
- [ ] `verify-release` produces a signature no one can forge by editing a ticket.

## M1 — Platform foundation and core work OS

Spec Phase 0–1. Epics E001, E002. 15 features, 118 estimate points.

**Goal.** A team can run a real project tracker end to end, on a floor of tenancy, identity, permissions and observability.

| Feature | Title | Epic |
|---|---|---|
| F001 | Repository and CI | E001 |
| F002 | Tenant, users, and groups | E001 |
| F003 | Authorization and audit | E001 |
| F004 | Runtime operations | E001 |
| F005 | Workspace navigation | E002 |
| F006 | Sheets/boards/items | E002 |
| F007 | Typed columns | E002 |
| F008 | Grid editing | E002 |
| F009 | Hierarchy and links | E002 |
| F010 | Search/import/export | E002 |
| F035 | Formula engine | E002 |
| F038 | Authentication and MFA | E001 |
| F062 | Design system and UI primitives | E001 |
| F066 | Service levels and error budgets | E001 |
| F068 | Persistence layer and data access classes | E001 |

**Exit criteria**

- [ ] A tenant, its first admin, users and groups exist, and every cross-tenant read returns `not_found`.
- [ ] Sign-in, sessions, MFA and API tokens work; every role-negative mutation returns `denied`.
- [ ] One request produces a JSON log line, an OTLP trace and Prometheus samples sharing a `correlation_id`; a restore drill completes and stores its evidence.
- [ ] Design tokens, the MUI theme and the component library are in place, and every later screen composes them rather than restyling.
- [ ] The repository contract and `UnitOfWork` exist; `check-persistence` proves no SQL lives outside `crates/persistence` and no array column survives.
- [ ] Availability and latency objectives are measured with burn-rate alerts wired to the runbook.
- [ ] A team creates a workspace and a sheet with typed columns, edits cells in the grid, and recovers a mistake through undo and cell history.
- [ ] Search finds a row by content and never returns one the actor cannot read; CSV and xlsx round-trip a 100,000-row sheet.

## M2 — Planning views and intake

Spec Phase 2. Epics E003. 6 features, 47 estimate points.

**Goal.** A standard project is provisioned from a template and work enters through a form.

| Feature | Title | Epic |
|---|---|---|
| F011 | Dates and schedules | E003 |
| F012 | Dependencies and Gantt | E003 |
| F013 | Views | E003 |
| F014 | Forms | E003 |
| F015 | Templates and baselines | E003 |
| F049 | Localization | E003 |

**Exit criteria**

- [ ] A project is provisioned from a template as one job that rolls back as a unit if any step fails.
- [ ] Dependencies, the critical path and a Gantt render over the same rows the grid shows — one record set, many presentations.
- [ ] A public form submits into a sheet with validation, spam defence, and no tenant discovery.
- [ ] Saved views — board, calendar, timeline, card — are shared and filtered per reader, and a baseline can be captured and compared.
- [ ] Dates, working calendars and recurrence behave correctly across timezones and daylight-saving boundaries.

## M3 — Collaboration and automation

Spec Phase 3. Epics E004. 9 features, 63 estimate points.

**Goal.** Intake to approval to assignment runs without manual handoffs, and is diagnosable when it fails.

| Feature | Title | Epic |
|---|---|---|
| F016 | Comments and activity | E004 |
| F017 | Files and proofing | E004 |
| F018 | Workflow builder | E004 |
| F019 | Workflow runtime | E004 |
| F020 | Approvals and escalation | E004 |
| F036 | Sharing, guests, and links | E004 |
| F037 | Notification service | E004 |
| F045 | Documents/folders | E004 |
| F046 | Live collaboration | E004 |

**Exit criteria**

- [ ] A workflow triggers, evaluates conditions, acts, and its run history explains every step.
- [ ] An approval escalates on its timer and every decision is audited.
- [ ] Notifications reach in-app, email and push under the recipient's preferences, quiet hours and digest.
- [ ] Documents support live co-editing with presence, comments and version recovery.
- [ ] Files are attached, versioned and proofed with markup and reviewer sign-off.
- [ ] Sharing, guest access and link expiry are one system, and every async path has a retry, a dead letter and a replay a support engineer can run.

## M4 — Reporting and dashboards

Spec Phase 4. Epics E005. 5 features, 37 estimate points.

**Goal.** A PMO runs weekly portfolio reviews from governed dashboards without spreadsheet consolidation.

| Feature | Title | Epic |
|---|---|---|
| F021 | Cross-source reports | E005 |
| F022 | Metrics and summaries | E005 |
| F023 | Dashboard builder | E005 |
| F024 | Charts and insights | E005 |
| F025 | Export/drill-through | E005 |

**Exit criteria**

- [ ] Cross-source reports join sheets without copying them, and every row respects the reader's permissions.
- [ ] Metrics, dashboards and charts refresh on schedule, and each number drills through to the rows behind it.
- [ ] Exports to CSV, xlsx and PDF carry only what the requester may read.
- [ ] A dashboard renders under 500 ms p95 at the stated scale tier and degrades honestly when a source is unavailable.

## M5 — Enterprise security and integrations

Spec Phase 5. Epics E006. 10 features, 72 estimate points.

**Goal.** A security review passes and a pilot enterprise tenant administers itself, buys, and pays.

| Feature | Title | Epic |
|---|---|---|
| F026 | SSO/SCIM | E006 |
| F027 | Governance/compliance | E006 |
| F028 | API/webhooks | E006 |
| F029 | Microsoft/Google/Slack | E006 |
| F030 | Jira/Salesforce/files | E006 |
| F047 | MCP access server | E006 |
| F048 | Entitlements and feature flags | E006 |
| F063 | Microsoft Entra integration | E006 |
| F064 | Billing and subscriptions | E006 |
| F065 | Self-serve signup and trials | E006 |

**Exit criteria**

- [ ] SAML, SCIM and Microsoft Entra federate identity beside password and OIDC, none replacing another.
- [ ] OAuth connections, connectors, conflict policy and replay are observable and recoverable.
- [ ] Retention, legal hold, tenant export and verified purge work, and a hold always beats a policy.
- [ ] The public API, webhooks and MCP surface are versioned, signed, rate-limited and audited.
- [ ] Entitlements, billing, credit codes and self-serve signup let a customer buy, pay and be provisioned without an operator.
- [ ] The security review passes on token handling, redaction, cross-tenant negatives and every unauthenticated surface.

## M6 — Portfolio and resource management

Spec Phase 6. Epics E007. 4 features, 37 estimate points.

**Goal.** Governance, portfolio health and capacity planning work across projects with traceable roll-ups.

| Feature | Title | Epic |
|---|---|---|
| F031 | Portfolio rollups | E007 |
| F032 | Project health/governance | E007 |
| F033 | Resources/capacity | E007 |
| F034 | Workload/actuals | E007 |

**Exit criteria**

- [ ] Portfolios roll up health, progress and spend from the projects beneath them, and every number drills to its rows.
- [ ] Resource profiles, capacity and allocations expose over-allocation before it happens, with a suggested rebalance.
- [ ] Planned versus actual effort reconciles, and a correction never rewrites history.
- [ ] Stage gates and health models are configurable per portfolio and every transition is audited.

## M7 — Advanced modules and AI

Spec Phase 7. Epics E008. 14 features, 80 estimate points.

**Goal.** Each module is entitled, permission-aware, audited and reversible; AI proposes and never silently acts.

| Feature | Title | Epic |
|---|---|---|
| F039 | AI formulas/queries | E008 |
| F040 | AI insights/automation | E008 |
| F050 | Dynamic View | E008 |
| F051 | WorkApps | E008 |
| F052 | Data Shuttle | E008 |
| F053 | DataMesh | E008 |
| F054 | Bridge | E008 |
| F055 | Calendar App | E008 |
| F056 | Pivot App | E008 |
| F057 | DAM assets | E008 |
| F058 | Mobile clients | E008 |
| F059 | Publishing/embedding | E008 |
| F060 | Conditional formatting | E008 |
| F061 | Update requests | E008 |

**Exit criteria**

- [ ] Every module degrades honestly without its entitlement and rolls back cleanly with its flag.
- [ ] Dynamic View, WorkApps, Data Shuttle, DataMesh, Bridge, Calendar, Pivot, DAM, publishing and conditional formatting each ship their own permission-negative suite.
- [ ] AI retrieval is permission-filtered, every proposal is reviewed as a diff before it applies, and the offline evaluation set runs in CI with no live model call.
- [ ] MCP exposes resources and tools scoped to the caller, with every mutation stopping at a human approval.
- [ ] The full-scale load profile passes for the composite target before the milestone is signed.

## Totals

68 features, 488 estimate points across 8 milestones.
