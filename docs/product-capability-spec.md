# OpsHub Work Management Platform

## 1. Purpose and scope

This document converts `specs1.md` from a capability inventory into an implementation-oriented product specification for an OpsHub platform benchmarked against Smartsheet, Monday.com, Asana, Jira, and adjacent tools.

The product is a structured work-management system: teams define work in tables, collect requests through forms, visualize and report on the same data, automate repeatable processes, and govern access across an organization.

The named vendor modules and integrations are benchmark requirements, not a commitment to reproduce vendor internals or branding. Build the shared platform primitives once and expose capabilities as composable modules.

## 1.1 Research-based capability interpretation

The source inventory is directionally correct but mixes core objects, views, premium modules, connectors, use cases, and marketing labels. The following interpretation is the basis for this specification:

- **Smartsheet model:** sheets and rows are the primary work/data surface; columns, formulas, cell linking, forms, reports, dashboards, conversations, attachments, workflows, templates, project/Gantt functions, and WorkApps are layered around that surface. Control Center, Resource Management, Bridge, DataMesh, Data Shuttle, Dynamic View, and Brandfolder are advanced/premium modules.
- **monday.com model:** workspaces contain boards; boards contain groups, items, and columns. Views present a board in different ways, while dashboards aggregate columns from connected boards through widgets. WorkForms feed submissions into boards; updates/comments, automations, integrations, templates, and workdocs extend the core board model.
- **Project/portfolio model:** dependencies, Gantt/timeline, milestones, health, planned/actual effort, budgets, and portfolio rollups are specialized project capabilities over the same work records. Cross-project dependencies, portfolio connection, and resource planning are typically enterprise-level in monday.com; Smartsheet packages related capabilities through project management, Control Center, and Resource Management.
- **Permission model:** an external or role-specific experience is a filtered presentation/editing surface, not a second source of truth. Dynamic View/WorkApps-like functionality therefore belongs after the core authorization and query layers.
- **AI model:** current platforms place AI inside columns, workflows, project/portfolio context, and natural-language assistance. AI must remain a permission-filtered proposal and insight layer over work data, not a separate uncontrolled data store.

This means the correct architectural center is a **typed work-record engine plus saved projections**, not a collection of independent feature screens.

### Product outcomes

1. A team can create a workspace, model work in a sheet, invite collaborators, and manage work in grid, board, calendar, timeline, and Gantt views.
2. A request can enter through a form, be routed and assigned automatically, and remain traceable through completion and approval.
3. Leaders can combine multiple work sources into reports and dashboards with current KPIs and drill-through to source records.
4. PMOs can standardize projects, dependencies, health, resources, governance, and portfolio reporting.
5. Administrators can enforce identity, authorization, auditability, retention, and integration controls.

## 2. Product boundaries and principles

### In scope

- Workspaces, sheets, rows, columns, views, formulas, relationships, and reusable templates.
- Forms, comments, attachments, approvals, notifications, automation, reports, and dashboards.
- Project/portfolio management, resource planning, governance, integrations, APIs, and administration.
- Mobile-responsive experiences and a mobile submission path.
- AI assistance with explicit user confirmation, source attribution, and permission-aware access.

### Non-goals for the first release

- Full spreadsheet compatibility with Excel's entire formula language.
- A general-purpose relational database replacement.
- Arbitrary code execution in workflows.
- Silent AI mutation of business data.
- Rebuilding every third-party application's specialized UX.

### Design principles

- One canonical record model; every view, report, form, and dashboard reads from it.
- Configuration over custom code for normal business processes.
- Immutable history for important changes and explainable automation.
- Permission checks at the API/service boundary, not only in the UI.
- Tenant isolation and least privilege by default.
- Async processing for imports, exports, integrations, formulas, and analytics refreshes.

## 3. High-level architecture

```text
Web / mobile / embedded form clients
              |
       API gateway + auth
              |
  Workspace | Work | Automation | Reporting | Integration services
              |
    PostgreSQL (metadata + records) -- object storage (files)
              |
     event bus / job queue / search index / analytics projections
```

### Recommended logical components

- **Identity service:** users, organizations, sessions, SSO, SCIM, service accounts.
- **Authorization service:** roles, groups, resource ACLs, sharing links, policy evaluation.
- **Work service:** sheets, rows, columns, cells, formulas, links, views, templates.
- **Workflow service:** triggers, conditions, actions, approvals, schedules, run history.
- **Collaboration service:** comments, mentions, activity feed, presence, proofing.
- **File service:** upload, virus scan, versioning, previews, retention, signed URLs.
- **Reporting service:** cross-sheet queries, summaries, calculated metrics, dashboard widgets.
- **Project service:** dependencies, milestones, baselines, critical path, health, portfolios.
- **Resource service:** people, skills, availability, allocations, workload, capacity.
- **Integration service:** OAuth connections, webhooks, mappings, sync jobs, retries.
- **AI service:** permission-filtered retrieval, formula/query/insight generation, approval gate.
- **Notification service:** in-app, email, push, and configurable delivery preferences.

## 4. Core domain model

Every tenant-owned entity has `id`, `tenant_id`, `created_at`, `created_by`, `updated_at`, `updated_by`, and a version/optimistic-lock token.

| Entity | Key fields and relationships |
|---|---|
| Tenant | name, plan, region, security policy; owns all data |
| User / Group | identity, profile, status; groups grant roles |
| Workspace | name, members, folders; contains sheets, reports, dashboards |
| Sheet | name, schema, settings, owner, workspace; contains rows and views |
| Column | type, label, required, formula, options, validation, width, visibility |
| Row / Cell | row order, parent row, cell value, display value, version; row is the work item |
| Link | source record/cell, target record/cell, link type, sync direction |
| View | type, filters, sorts, grouping, columns, timeline/Gantt settings |
| Form | sheet target, fields, layout, conditional rules, submission policy |
| Report | source sheets, filters, joins, grouping, calculated fields, refresh policy |
| Dashboard | widgets, layout, audience, refresh policy; widgets point to reports or sheets |
| Workflow | trigger, conditions, actions, active state, owner, version |
| WorkflowRun | workflow version, input event, status, step results, error, timestamps |
| Comment / Mention | target entity, body, author, thread, mentions, resolution state |
| File / FileVersion | owner, target, storage key, checksum, MIME, scan state, retention |
| Project / Portfolio | template, status, health, dates, budget, owner, child projects |
| Dependency | predecessor, successor, type, lag; used by schedule engine |
| Resource / Allocation | person/team, role, period, planned hours, actual hours, capacity |
| IntegrationConnection | provider, OAuth secret reference, scopes, sync settings, status |
| AuditEvent | actor, action, object, before/after or diff, IP/device, timestamp |

### Record and data rules

- A sheet has a stable column ID; renaming a column must not break formulas, links, reports, or integrations.
- A row has a stable ID independent of display order. Moves and hierarchy changes are events.
- Cell values are typed (`text`, `number`, `currency`, `date`, `datetime`, `boolean`, `person`, `link`, `file`, `select`, `formula`, `duration`).
- Store raw value, normalized value, and validation/error state where applicable.
- Soft-delete records first; restore and permanent purge are separate privileged operations.
- All mutations support idempotency keys and optimistic concurrency.

## 5. Capability requirements

### 5.1 Work management and views

**High-level requirements**

- **WORK-01:** Users can create and edit structured sheets for project, operational, CRM, ticket, and budget data.
- **WORK-02:** Users can manage tasks, subtasks, owners, statuses, dates, priority, tags, milestones, and attachments.
- **WORK-03:** The same sheet supports grid, Gantt, calendar, card/Kanban, timeline, and portfolio-oriented views.
- **WORK-04:** Projects support WBS hierarchy, dependencies, milestones, baselines, schedule variance, and critical-path display.
- **WORK-05:** Views are saved, shareable, permission-aware, filterable, sortable, groupable, and exportable.

**Low-level requirements**

- Grid: virtualized rendering, inline edit, paste/fill, multi-select, undo/redo, column resize/reorder/hide, frozen columns, validation, bulk edit.
- Card: map a status/group field to lanes; drag-and-drop updates status with permission and automation events.
- Calendar/timeline: date or date-range mapping, timezone-aware rendering, drag-to-reschedule, recurrence display.
- Gantt: dependency validation, working calendar, lag, parent roll-up, milestone marker, baseline overlay, critical-path calculation.
- Hierarchy: parent/child row IDs; aggregate status, percent complete, dates, effort, and cost using configurable roll-up rules.
- Search: tenant-scoped full-text search over sheet names, rows, comments, and attachments metadata.
- Import/export: CSV/XLSX import with preview and type mapping; CSV/XLSX/PDF export with permission filtering.
- Conditional formatting evaluates typed rules against current values and exposes deterministic visual states in every supported view.
- Published and embedded views use scoped, revocable access tokens, preserve permission filtering, and expose stale/error state.
- Mobile clients support responsive work editing, push/deep links, queued offline mutations, reconnect reconciliation, and secure local-session handling.

### 5.2 Data management and formulas

**High-level requirements**

- **DATA-01:** Sheets are the primary editable data repository.
- **DATA-02:** Users can reference data across sheets and link related records.
- **DATA-03:** The formula engine evaluates common spreadsheet functions and reports errors clearly.
- **DATA-04:** Data can be imported, exported, synchronized, and processed asynchronously at scale.

**Low-level requirements**

- Formula parser produces an AST with dependency graph; recalculation is incremental and cycle-detected.
- Initial function set: arithmetic, comparison, conditional, text, date/time, lookup, aggregation, and cross-sheet reference functions.
- Formula results expose `value`, `status`, and error code (`invalid`, `missing reference`, `type mismatch`, `cycle`, `timeout`).
- Cross-sheet references resolve by stable sheet/column/row IDs, never display names alone.
- Imports provide schema preview, duplicate strategy, validation report, dry run, and resumable job status.
- Large sheets use pagination/cursors, bulk endpoints, indexed filter fields, and background materialized views.
- Change events include entity ID, actor, version, changed fields, and correlation ID.

### 5.3 Forms and data collection

**High-level requirements**

- **FORM-01:** Authorized users can build branded custom forms targeting a sheet.
- **FORM-02:** Forms support required fields, validation, conditional logic, attachments, confirmation, and spam controls.
- **FORM-03:** Forms can be shared internally, externally, embedded, and submitted from mobile browsers.
- **FORM-04:** Submissions create traceable rows and can initiate routing, approval, and notifications.

**Low-level requirements**

- Form field definitions reference column IDs and support display condition expressions.
- Public forms use a separate submission token, rate limit, CAPTCHA/honeypot option, and configurable identity capture.
- Submission creates an immutable intake event before row creation; retries are idempotent.
- Draft submissions, confirmation page/email, field-level error messages, and upload size/type limits are configurable.
- Form versions are immutable after publication; new edits create a draft version.
- Update requests target selected fields or rows, record requester/recipient/due date/status, send configurable reminders, and preserve the response audit trail.

### 5.4a Documents, folders, and live collaboration

**High-level requirements**

- **DOC-01:** Users can create, rename, move, archive, search, and restore documents and folders inside a workspace.
- **DOC-02:** Documents support shareable links, scoped user/group/guest permissions, version history, comments, and attachments.
- **DOC-03:** Multiple authorized users can edit a document concurrently with presence, ordered changes, reconnect recovery, and conflict visibility.

**Low-level requirements**

- Folder membership is a canonical hierarchy with stable IDs, cycle prevention, inherited access, explicit overrides, and trash retention.
- Documents store type, owner, parent folder, current version, content checksum, and search metadata; content revisions are immutable.
- Live sessions authenticate to the tenant and document, publish presence leases, sequence operations, acknowledge durable versions, and replay missed changes.
- Concurrent edits use a deterministic operation or revision protocol; clients never silently overwrite a newer revision.
- Share links are revocable, scoped, expiring, rate-limited, and excluded from tenant-wide discovery unless explicitly permitted.

### 5.4b Collaboration, sharing, proofing, and approvals

**High-level requirements**

- **COLLAB-01:** Users can comment on sheets, rows, cells, files, and dashboard/report items.
- **COLLAB-02:** Users can mention collaborators, resolve threads, attach files, and view activity/history.
- **COLLAB-03:** Owners can share with users, groups, guests, or controlled links using granular roles.
- **COLLAB-04:** Teams can request review, approve/reject, and maintain visible version history.

**Low-level requirements**

- Comments use threaded records with edit/delete policy, mentions, notifications, and resolution timestamp.
- Activity feed records human and automated mutations with actor attribution; audit log remains append-only.
- Files are stored outside the transactional database, virus-scanned, checksummed, versioned, and served by expiring URLs.
- Approval instance has requested-by, approver set, quorum rule, due date, decision, reason, and escalation state.
- Roles: owner, admin, editor, commenter, viewer, form submitter; sheet/report/dashboard permissions may narrow access.
- External users never inherit tenant-wide access and must be explicitly scoped.

### 5.5 Automation and notifications

**High-level requirements**

- **AUTO-01:** Users can create trigger-condition-action workflows without code.
- **AUTO-02:** Workflows support alerts, assignments, status updates, approvals, routing, and recurring processes.
- **AUTO-03:** Every run is observable, retryable, rate-limited, and safe against duplicate events.

**Low-level requirements**

- Triggers: row created/updated, field changed, form submitted, schedule, date reached, webhook received, approval decision.
- Conditions: typed comparisons, AND/OR groups, changed-field test, user/group test, existence, formula result.
- Actions: update fields, create row, move/copy row, assign, comment, request approval, send email/in-app/push, call webhook, invoke integration.
- Workflow versions are immutable per run; drafts require publish; disabled workflows stop new runs but preserve history.
- Queue execution with per-tenant quotas, exponential retry, dead-letter state, timeout, idempotency key, and correlation ID.
- Notification preferences support channel, digest, quiet hours, mention/assignment/approval categories.

### 5.6 Reporting, analytics, and dashboards

**High-level requirements**

- **REPORT-01:** Users can combine filtered data from multiple sheets into reports.
- **REPORT-02:** Users can build executive dashboards with KPI cards, tables, charts, images, and links.
- **REPORT-03:** Dashboards support real-time or scheduled refresh, drill-through, sharing, and export.
- **REPORT-04:** The system supports portfolio summaries, burndown, time series, trend analysis, and work insights.

**Low-level requirements**

- Report query model supports source selection, joins by stable IDs/keys, filters, grouping, calculated fields, and row-level permission filtering.
- Widget types: KPI, metric comparison, table, bar/line/pie, burndown, timeline, workload, text, image, report embed.
- Every chart declares dimensions, measures, aggregation, timezone, formatting, and empty/error state.
- Refresh jobs are cached and expose last-success, duration, source versions, and stale state.
- Drill-through opens the source row/sheet only if the viewer has access; hidden values are not included in aggregates unless policy allows.
- Export to PDF/PNG/CSV is asynchronous and records who exported what.

### 5.7 Project, portfolio, resource, and governance management

**High-level requirements**

- **PPM-01:** Teams can create projects from templates with standardized phases, fields, views, workflows, and governance checkpoints.
- **PPM-02:** Portfolios aggregate project status, schedule, budget, risk, value, and health.
- **PPM-03:** Resource planning supports allocation, capacity, workload balancing, skills, and planned versus actual effort.
- **PPM-04:** PMOs can monitor project health and enforce intake, stage gates, baselines, and reporting standards.

**Low-level requirements**

- Project template versions contain sheet schema, default rows, dependencies, forms, workflows, reports, dashboard, roles, and metadata.
- Health is configurable from weighted indicators (schedule, budget, scope, risk, resource) with manual override and reason.
- Portfolio roll-up preserves source project IDs, last refresh, missing-data state, and permission boundaries.
- Resource allocations are period-based with planned hours/percent, actuals, role, cost rate, and confidence.
- Capacity calculation accounts for working calendar, leave, holidays, part-time availability, and allocation conflicts.
- Baselines snapshot schedule and selected measures; variance compares current values to a named baseline.
- Stage gates require defined evidence, decision, approver, date, and audit event.

### 5.8 Enterprise security and administration

**High-level requirements**

- **SEC-01:** Tenant administrators can manage roles, groups, sharing, sessions, and security policy.
- **SEC-02:** The platform supports SSO/SAML, lifecycle provisioning, audit logs, and security administration.
- **SEC-03:** Compliance controls cover retention, export, deletion, access review, and administrative activity.

**Low-level requirements**

- Enforce tenant isolation on every query; test cross-tenant access explicitly.
- SAML SSO with signed assertions, configurable domains, certificate rotation, clock-skew handling, and login audit.
- SCIM provisioning/deprovisioning, group sync, suspended-user behavior, and ownership transfer policy.
- MFA policy, session expiration, refresh-token revocation, IP/device metadata, and API token scopes.
- Append-only audit events for authentication, permission changes, data access exports, mutations, automation, and admin actions.
- Configurable retention/legal hold, export of tenant data, soft-delete recovery, and verified purge workflow.
- Encrypt in transit and at rest; secrets live in a secret manager; redact sensitive values from logs.

### 5.9 Integrations and APIs

**High-level requirements**

- **INT-01:** Provide a versioned REST API and webhooks for core objects and events.
- **INT-02:** Support Microsoft 365 assistant, Jira, Salesforce, Google Workspace, Tableau, Slack, Box, Dropbox, databases, and CRM scenarios through adapters.
- **INT-03:** Premium connectors and workflow modules can be enabled by entitlement without changing core data semantics.

**Low-level requirements**

- API resources: tenants, users, workspaces, sheets, columns, rows, cells, views, forms, reports, dashboards, workflows, comments, files, projects, portfolios, resources, integrations.
- Consistent pagination, filtering, field selection, idempotency, optimistic concurrency, error schema, rate-limit headers, and request correlation IDs.
- Webhooks support event filters, signing secret, delivery ID, retry schedule, replay, disable-after-failures, and delivery log.
- OAuth connections encrypt refresh tokens and record scopes, owner, last success, and revocation state.
- Connector mappings define source/target IDs, direction, conflict policy, field transforms, deletion policy, and sync cursor.
- Database connectivity is read-only first, with explicit allowlists, parameterized queries, and isolated credentials.

### 5.9a MCP access server

**High-level requirements**

- **MCP-01:** Provide one versioned MCP server exposing permission-filtered resources for workspaces, documents, folders, projects, tasks, tickets, dashboards, workflows, and audit history.
- **MCP-02:** Expose safe tools for search, read, create, update, comment, assignment, workflow execution, and report retrieval.
- **MCP-03:** Require tenant authentication, scope checks, rate limits, audit events, confirmation for mutations, and feature-gated rollout.

**Low-level requirements**

- Resource and tool schemas are generated from the canonical API contract and checked for drift in CI.
- Every request carries tenant, actor, correlation, and authorization context; responses redact inaccessible fields.
- Read tools are idempotent; mutation tools require an idempotency key and return a reviewable change summary before commit.
- The protocol harness tests discovery, invalid arguments, denied access, pagination, rate limits, retries, audit records, and mutation approval.

### 5.10 AI capabilities

**High-level requirements**

- **AI-01:** Users can request formulas, summaries, dashboards, visualizations, data enrichment, and natural-language questions.
- **AI-02:** AI can identify risk, anomalies, trends, and missing data across authorized work.
- **AI-03:** AI output is reviewable, permission-aware, attributable, and never silently commits changes.

**Low-level requirements**

- Retrieval is tenant- and object-permission filtered; prompts/logs must not leak inaccessible values.
- Formula generation returns formula, explanation, referenced fields, confidence/limitations, and a test preview.
- Natural-language query compiles to a constrained report/query plan shown to the user before execution for sensitive data.
- Insight output includes evidence row IDs, calculation timestamp, source versions, and uncertainty.
- Actions are proposed as a diff; user confirmation is required for writes, workflow creation, sharing, or external sends.
- Provider abstraction supports model selection, token/cost budgets, timeout, safety filters, redaction, and fallback.
- AI access is feature-flagged, admin-controllable, rate-limited, and auditable.

### 5.11 Advanced modules

Implement these as entitlement-gated modules over the primitives above. Delivery backlog: entitlements `F048`; Control Center provisioning and governance `F015`, `F032`; Resource Management `F033`, `F034`; Dynamic View `F050`; WorkApps `F051`; Data Shuttle `F052`; DataMesh `F053`; Bridge `F054`; Calendar App `F055`; Pivot App `F056`; DAM `F057`.

- Control Center: governed project provisioning, template versions, intake, stage gates, and portfolio views.
- Resource Management: resource profiles, capacity, allocations, workload, time capture, and forecasting.
- Dynamic View: restricted filtered views with field/row-level sharing and controlled external editing.
- WorkApps: no-code app shell with navigation, role-specific pages, embedded sheets/forms/reports, and app permissions.
- Data Shuttle: scheduled file ingestion/export with mapping, validation, archive, and run history.
- DataMesh: reference-data mapping and controlled synchronization across sheets.
- Bridge: advanced multi-step cross-system workflows using the same event/action contracts.
- Calendar App: multi-source calendar aggregation and publishing.
- Pivot App: configurable pivot dimensions/measures with saved outputs.
- DAM/Brandfolder-like module: assets, metadata, renditions, approvals, collections, and usage rights.

## 6. Cross-cutting non-functional requirements

- **Availability:** define tier targets; MVP target 99.5% monthly for core read/write APIs, with graceful degradation for analytics and integrations.
- **Performance:** p95 interactive reads under 500 ms for normal views; p95 single-row writes under 800 ms; acknowledge async jobs under 2 seconds.
- **Scale target:** design for 10,000 tenants, 1 million users, 100,000 rows per sheet, 500 columns per sheet, and 1,000 concurrent edits per tenant; validate through load tests.
- **Consistency:** transactional row/cell writes; eventual consistency acceptable for search, analytics, notifications, and integrations.
- **Reliability:** idempotent jobs, retries, dead-letter queues, backups, point-in-time recovery, and tested restore procedures.
- **Observability:** structured logs, metrics, traces, job dashboards, audit correlation, alerting, and customer-visible run status.
- **Accessibility:** WCAG 2.2 AA target, keyboard navigation, screen-reader labels, focus management, contrast, and reduced-motion support.
- **Internationalization:** locale-aware dates/numbers, timezones, UTF-8, translations, and tenant working calendars.
- **Privacy:** data minimization, configurable retention, export/delete workflows, consent where applicable, and regional hosting strategy.

## 7. Recommended build order

### Phase 0 — Foundation and decisions

Define tenancy, identity model, authorization matrix, canonical IDs, event contracts, API conventions, design system, data retention, and key scale targets. Produce threat model and UX prototypes for sheet, form, workflow, and dashboard.

**Exit criteria:** architecture decision records approved; domain schema and permission tests exist; vertical slice is estimable.

### Phase 1 — Core work OS (MVP)

Ship tenants, users, workspaces, sheets, columns, rows/cells, grid view, basic formulas, comments, attachments, roles, audit events, search, CSV import/export, and responsive UI.

**Exit criteria:** a team can create and manage a project tracker with safe sharing, history, and recovery.

### Phase 2 — Planning and intake

Add WBS, subtasks, dependencies, milestones, Gantt, calendar, card view, project templates, forms, conditional logic, and submission routing.

**Exit criteria:** a standard project can be provisioned from a template and requests can enter through a public or internal form.

### Phase 3 — Automation and collaboration maturity

Add workflow builder/runtime, approvals, notifications, recurring jobs, mentions, proofing/version visibility, webhooks, and mobile submission polish.

**Exit criteria:** common intake-to-approval-to-assignment processes run without manual handoffs and are diagnosable.

### Phase 4 — Reporting and executive visibility

Add cross-sheet reports, joins, KPI calculations, dashboards, charts, burndown/time series, drill-through, scheduled refresh, and PDF export.

**Exit criteria:** a PMO can operate weekly portfolio reviews from governed dashboards without spreadsheet consolidation.

### Phase 5 — Enterprise readiness and integrations

Add SAML SSO, SCIM, MFA policy, advanced audit/compliance, API maturity, OAuth connections, Slack, Microsoft 365, Jira, Salesforce, Google Workspace, file storage, and Tableau adapters.

**Exit criteria:** security review passes; integration retries/conflicts are observable; pilot enterprise tenant can administer itself.

### Phase 6 — PPM and resource management

Add portfolios, program structures, health, baselines, critical path, resource profiles, capacity, workload balancing, planned/actual effort, and stage gates.

**Exit criteria:** PMO governance, portfolio health, and capacity planning work across multiple projects with traceable roll-ups.

### Phase 7 — Advanced modules and AI

Add Control Center, Dynamic View, WorkApps, Data Shuttle/DataMesh/Bridge, Calendar/Pivot, DAM, then AI formula/query/insight/enrichment features behind flags.

**Exit criteria:** each module has entitlement, permission, audit, usage, support, and rollback behavior; AI has evaluation sets and human-confirmation UX.

## 8. Release gates and acceptance strategy

For each capability, require:

- happy-path and permission-negative acceptance tests;
- API contract and migration tests;
- audit event and notification verification;
- accessibility and responsive UI checks;
- load test for the expected scale tier;
- failure/retry/recovery test for every async path;
- documentation, support runbook, analytics events, and feature-flag/rollback plan.

### MVP end-to-end acceptance scenario

An authenticated project manager creates a workspace and project from a template, edits tasks in grid and board views, adds dates/dependencies, collects a request through a form, routes it for approval, assigns the approved task, receives a notification, comments with an attachment, and views current status in a dashboard. An administrator can restrict access, inspect the audit trail, export data, and recover a deleted row.

## 9. Prioritization rubric

Prioritize work that increases the value of the canonical record model or unlocks multiple downstream features. Score each feature on customer value, number of dependent capabilities, risk/compliance impact, implementation effort, and differentiation. Do not start a premium module until its underlying primitive is stable and covered by API, permission, audit, and migration tests.

## 10. Resolved implementation decisions

- Initial hosting region is US-East with a tenant `region` field reserved for future residency partitions; target certification is SOC 2 Type II after the pilot.
- PostgreSQL 18 is the sole initial transactional and analytical store; analytics use projections and indexed summary tables, with no separate warehouse in the first release.
- Formula compatibility targets the function groups in section 5.2, with a 10,000-AST-node limit, 2-second evaluation budget, cycle detection, and explicit unsupported-function errors.
- Mobile scope is responsive web plus installable PWA, offline queued row edits/forms, push notifications, and reconnect reconciliation; offline document co-editing is excluded until the live protocol is stable.
- External sharing requires explicit guest identity or expiring links; links expire within 30 days, are revocable, never grant tenant discovery, and cannot perform writes except through published forms or explicitly scoped views.
- Supported enterprise identity is generic OIDC, SAML 2.0, SCIM 2.0, WebAuthn, and TOTP; provider-specific adapters are tested against Microsoft and Google identity fixtures.
- Connector ownership is first-party for the providers in INT-02; every adapter shares the same mapping, cursor, conflict, retry, replay, and audit contracts.
- Resource actuals are native OpsHub time entries; imported actuals are marked external and cannot overwrite native entries without an audited reconciliation.
- AI uses a provider-neutral adapter selected by deployment configuration, stores no training data, retains prompts/results only in tenant-configured audit retention, and is evaluated against permission, citation, refusal, and mutation-safety suites.
- Advanced modules use entitlement records plus feature flags; flags default off, limits are tenant-configured, and packaging is an administration concern rather than domain behavior.

## 11. Source research and benchmark links

Reviewed September 3, 2026. Product plans and availability change; these links establish capability shape, not a permanent pricing or packaging promise.

- [Smartsheet Learning Center](https://help.smartsheet.com/) — sheets/rows, columns, forms, formulas, dashboards, views, conversations, attachments, workflows, templates, project/Gantt, WorkApps, and premium feature categories.
- [Smartsheet capabilities matrix](https://help.smartsheet.com/articles/2480681-gov-capabilities) — examples of activity logs, API, baselines, cell formulas/history/linking, and column types.
- [Smartsheet WorkApps datasheet](https://www.smartsheet.com/sites/default/files/2020-09/workapps-datasheet.pdf) — role-oriented app experiences built from sheets, reports, dashboards, and forms.
- [monday.com introduction](https://support.monday.com/hc/en-us/articles/115005310945-Introduction-to-monday-com) — workspaces, boards, items, groups, columns, workdocs, WorkForms, views, dashboards, updates, automations, integrations, and AI.
- [monday.com dashboards](https://support.monday.com/hc/en-us/articles/360002187819-The-Dashboards) — dashboards aggregate data from connected boards and widgets; mirrored/connected data remains tied to board structure.
- [monday.com project management](https://support.monday.com/hc/en-us/articles/360014437599-Project-management-with-monday-com) — intake, dependency types, Gantt, planned versus actual timeline, automations, and project dashboards.
- [monday.com project boards](https://support.monday.com/hc/en-us/articles/22598441769746-Project-boards-on-monday-com) — project-specific columns and the distinction between standalone project capabilities and enterprise portfolio/resource capabilities.
- [monday.com portfolio solution](https://support.monday.com/hc/en-us/articles/13337066797202-The-portfolio-solution) — portfolio board/project board structure, synchronized project information, project health, rollups, and portfolio AI context.
