# OpsHub delivery plan

Status: READY FOR IMPLEMENTATION. Source: `docs/product-capability-spec.md`; decisions: `docs/architecture-decisions.md`; contracts: `docs/capability-contracts.md`.

## Rules

- Hierarchy: `Epic → Feature ticket → Story → Task`.
- One feature ticket is the complete product contract. Stories are vertical slices. Tasks are owned implementation units. Each story owns the two tasks listed after it, in order.
- Every item has a branch: `e###-slug`, `f###-slug`, `s###-slug`, or `t###-slug`.
- The `Depends on` column is authoritative. A feature ticket's `depends_on` must match it exactly.
- Every feature owns disjoint module paths defined in `docs/capability-contracts.md` plus `testing/features/F###/**`. Catch-all paths such as `services/api/**` are invalid.
- `work/plan.md` is the backlog index. Item files are hand-written contracts validated by `cargo xtask validate-work`; `scaffold-plan` only creates missing skeletons and never overwrites.

## Global completion gates

- Requirements, API/data/UI contracts, dependencies, and owned paths approved.
- Frozen architecture decisions and capability contracts are linked from every work item.
- Failing tests exist before production code.
- Rust unit/API/database tests, React/component/E2E tests, permission tests, accessibility, and applicable performance tests pass.
- Feature path is wired and integration-tested.
- `cargo xtask validate-tickets`, line-limit, contract, security, and migration gates pass.
- Feature flag, telemetry, audit, docs, rollback, and handoff evidence complete.

## E000 — Developer workflow and delivery control plane

Outcome: agents and humans can create, claim, validate, fan out, integrate, and archive work deterministically. Milestone M0.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F041 Work-item schema | S081 epic/feature schema; S082 story/task schema | T161 YAML front matter; T162 hierarchy/reference checks; T163 branch/file checks; T164 line-limit check | — |
| F042 xtask audit/gates | S083 staged/commit/PR audit; S084 ticket/ownership audit | T165 forbidden-token gate; T166 dependency/conflict gate; T167 owned-path gate; T168 positive-control self-test | F041 |
| F067 System scale and load validation | S133 load profiles and seeds; S134 scale gate and evidence | T265 seed generator; T266 load profiles; T267 load-test gate; T268 scale evidence tests | F043, F044 |
| F043 Fanout orchestration | S085 lane claiming; S086 isolated execution | T169 worktree allocator; T170 target-dir allocator; T171 fixture/tenant allocator; T172 artifact collector | F041, F042 |
| F044 Contract/release control | S087 contract drift; S088 release evidence | T173 OpenAPI/event drift; T174 migration safety; T175 feature-flag lifecycle; T176 release/rollback verifier | F041, F042 |

Exit: a clean checkout can validate the complete work graph, reject invalid or attributed changes, claim non-conflicting lanes, run targeted/full gates, and produce auditable release evidence.

## E001 — Platform foundation

Outcome: secure, observable, reproducible multi-tenant runtime. Milestone M1.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F068 Persistence layer and data access classes | S135 repository contract and unit of work; S136 normalization and access gate | T269 repository base contract; T270 unit of work and pagination; T271 check-persistence gate; T272 persistence harness | F001 |
| F066 Service levels and error budgets | S131 objectives and measurement; S132 burn alerts and reporting | T261 objective definitions; T262 recording rules and burn alerts; T263 verify-slo gate; T264 SLO harness | F004 |
| F001 Repository and CI | S001 workspace; S002 quality gates | T001 Rust workspace; T002 React app; T003 CI matrix; T004 line/attribution gates | F041, F042 |
| F062 Design system and UI primitives | S123 design tokens and theming; S124 UI primitives and patterns | T245 token scales and themes; T246 MUI theme and component surface; T247 pattern components and app shell layout; T248 visual and accessibility harness | F001 |
| F002 Tenant, users, and groups | S003 tenant lifecycle; S004 users and groups | T005 tenant schema; T006 user/group API; T007 membership state; T008 tenant harness | F001 |
| F038 Authentication and MFA | S075 OIDC login and sessions; S076 MFA and API tokens | T149 OIDC client and session store; T150 WebAuthn/TOTP; T151 API tokens and rate limits; T152 auth negative tests | F002 |
| F003 Authorization and audit | S005 roles/policies; S006 activity history | T009 policy engine; T010 ACL middleware; T011 audit schema; T012 negative tests | F002, F038 |
| F004 Runtime operations | S007 config/secrets; S008 observability | T013 container/compose baseline; T014 outbox and JetStream transport; T015 tracing/metrics; T016 health/backup/readiness | F001 |

Exit: clean environment boots API/web/worker/realtime, tenant isolation is tested, MFA and sessions work, CI blocks invalid tickets and forbidden attribution, logs/traces/health are usable.

## E002 — Core work record engine

Outcome: canonical typed work data that every feature consumes. Milestone M1.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F005 Workspace navigation | S009 create workspace; S010 membership and folders | T017 workspace migration/API; T018 React shell; T019 permission fixtures; T020 E2E | F003, F004 |
| F006 Sheets/boards/items | S011 create sheet; S012 create/update row | T021 schema migration; T022 CRUD service; T023 grid API; T024 board UI | F005 |
| F007 Typed columns | S013 column lifecycle; S014 validation | T025 column types; T026 validation engine; T027 column editor; T028 contract tests | F006 |
| F008 Grid editing | S015 inline edit; S016 bulk operations | T029 optimistic concurrency and undo; T030 bulk API; T031 virtual grid; T032 conflict tests | F007 |
| F009 Hierarchy and links | S017 parent/child rows; S018 linked records | T033 hierarchy model; T034 link model; T035 rollup service; T036 relationship UI | F007 |
| F035 Formula engine | S069 parser and evaluation; S070 dependency graph and recalculation | T137 parser/AST; T138 function library; T139 incremental recalculation; T140 cross-sheet references and errors | F007, F009 |
| F010 Search/import/export | S019 search; S020 CSV/XLSX jobs | T037 full-text index; T038 import worker; T039 export worker; T040 fixtures/load tests | F008, F004 |

Exit: a user can create, edit, validate, compute, search, import, export, relate, and recover work records through the real UI/API path.

## E003 — Planning, views, and intake

Outcome: teams plan work, visualize it, and collect requests. Milestone M2.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F011 Dates and schedules | S021 dates/calendars; S022 working time | T041 date types/timezones; T042 working calendar; T043 schedule API; T044 date UI tests | F007 |
| F049 Localization | S097 locale formatting; S098 translations | T193 locale/timezone formatting; T194 message catalog; T195 tenant locale settings; T196 i18n tests | F005 |
| F012 Dependencies and Gantt | S023 dependency links; S024 schedule shifts | T045 dependency engine; T046 cycle detection and critical path; T047 Gantt view; T048 schedule E2E | F009, F011 |
| F013 Views | S025 card/calendar; S026 timeline | T049 saved-view schema; T050 card view; T051 calendar/timeline; T052 view permissions | F008, F011 |
| F014 Forms | S027 form builder; S028 public submission | T053 form schema; T054 conditional rules; T055 submission endpoint; T056 abuse/upload tests | F007 |
| F015 Templates and baselines | S029 project template; S030 baseline compare | T057 template versioning; T058 provisioning job; T059 baseline snapshot; T060 variance UI | F012, F013, F014 |

Exit: a project can be planned from a template, visualized in supported views, localized, and populated from a safe intake form.

## E004 — Collaboration and automation

Outcome: work moves through communication, approval, and repeatable automation. Milestone M3.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F016 Comments and activity | S031 row conversations; S032 mentions/history | T061 thread API; T062 mention events; T063 activity feed; T064 collaboration E2E | F006, F003 |
| F017 Files and proofing | S033 attachments; S034 review/versioning | T065 object storage; T066 scan/preview worker; T067 file versions; T068 proofing tests | F006, F004 |
| F036 Sharing, guests, and links | S071 resource sharing grants; S072 guest identity and links | T141 share grants API; T142 sharing UI; T143 guest and link tokens; T144 sharing negative tests | F003, F005 |
| F037 Notification service | S073 channels and delivery; S074 preferences and digests | T145 notification outbox; T146 email/push adapters; T147 preferences/quiet hours/digest; T148 notification tests | F004, F002 |
| F018 Workflow builder | S035 trigger/condition; S036 actions | T069 workflow schema; T070 expression evaluator; T071 builder UI; T072 workflow fixtures | F007, F035 |
| F019 Workflow runtime | S037 queued runs; S038 retries/dead letters | T073 worker queue; T074 idempotency; T075 retry/DLQ; T076 runtime integration tests | F018, F004 |
| F020 Approvals and escalation | S039 approvals; S040 routing/escalation | T077 approval state machine; T078 approval notifications; T079 escalation scheduler; T080 audit tests | F019, F037 |
| F045 Documents/folders | S089 document library; S090 sharing and permissions | T177 document metadata/storage; T178 folder tree/search; T179 document editor/versioning; T180 document access tests | F005, F017, F036 |
| F046 Live collaboration | S091 presence/co-editing; S092 change recovery | T181 realtime session service; T182 operation ordering; T183 presence UI; T184 reconnect/conflict tests | F045, F004 |

Exit: intake-to-assignment-to-approval workflows run asynchronously, safely, observably, and without duplicate side effects.

## E005 — Reporting and dashboards

Outcome: teams and leaders see current cross-work performance. Milestone M4.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F021 Cross-source reports | S041 source selection; S042 filters/joins | T081 report query model; T082 permission-aware query; T083 report API; T084 query tests | F008, F035, F003 |
| F022 Metrics and summaries | S043 KPIs; S044 rollups/trends | T085 metric definitions; T086 aggregate jobs; T087 KPI UI; T088 calculation fixtures | F021 |
| F023 Dashboard builder | S045 widget layout; S046 sharing | T089 dashboard schema; T090 widget registry; T091 React builder; T092 visual/access tests | F021, F036 |
| F024 Charts and insights | S047 charts/time series; S048 burndown/workload | T093 chart query adapters; T094 time-series projections; T095 chart components; T096 render tests | F022, F023 |
| F025 Export/drill-through | S049 source drill-through; S050 PDF/CSV export | T097 secure drill-through; T098 export worker; T099 export UI; T100 permission tests | F023, F010 |

Exit: PMO dashboard supports source-linked KPIs, charts, trends, drill-through, export, permissions, and refresh state.

## E006 — Enterprise security and integrations

Outcome: organizations can administer and connect OpsHub safely. Milestone M5.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F026 SSO/SCIM | S051 SAML login; S052 lifecycle sync | T101 SAML service; T102 SCIM endpoints; T103 group mapping; T104 identity tests | F038, F002 |
| F027 Governance/compliance | S053 retention/export; S054 access review | T105 retention and legal hold; T106 tenant export/purge; T107 access reports; T108 compliance tests | F003, F010 |
| F028 API/webhooks | S055 REST API; S056 event delivery | T109 OpenAPI generation; T110 pagination/errors; T111 signed webhooks; T112 contract harness | F003, F038, F004 |
| F029 Microsoft/Google/Slack | S057 OAuth connections; S058 notifications/sync | T113 OAuth vault; T114 provider adapters; T115 conflict policy; T116 mocked connector tests | F028, F037 |
| F048 Entitlements and feature flags | S095 entitlement records; S096 flag administration | T189 entitlement schema; T190 entitlement middleware; T191 flag admin UI; T192 entitlement tests | F002, F003 |
| F064 Billing and subscriptions | S127 subscription and plan lifecycle; S128 usage metering and invoicing | T253 billing schema and provider adapter; T254 plan lifecycle API; T255 usage metering and invoices; T256 billing negative tests | F002, F048 |
| F065 Self-serve signup and trials | S129 public signup and verification; S130 trial provisioning and conversion | T257 signup schema and public API; T258 verification and anti-abuse; T259 tenant provisioning; T260 signup negative tests | F002, F038, F064 |
| F063 Microsoft Entra integration | S125 Entra sign-in and directory; S126 Graph mail and group sync | T249 Entra connection and app registration; T250 OIDC sign-in and claims; T251 Graph mail transport; T252 group sync and negative tests | F026, F037, F038 |
| F030 Jira/Salesforce/files | S059 work sync; S060 CRM/file sync | T117 connector framework; T118 field mapping; T119 cursor/retry state; T120 replay tests | F029 |
| F047 MCP access server | S093 MCP resources; S094 MCP tools and safety | T185 MCP server boundary; T186 resource adapters; T187 mutation approval; T188 protocol harness | F028, F045 |

Exit: enterprise admin, API, webhook, OAuth, connector, MCP, audit, retry, and conflict behavior is documented and tested.

## E007 — Portfolio and resource management

Outcome: PMOs govern portfolios, programs, capacity, and project health. Milestone M6.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F031 Portfolio rollups | S061 portfolio setup; S062 project rollup | T121 portfolio schema; T122 rollup projections; T123 portfolio UI; T124 permission tests | F015, F021 |
| F032 Project health/governance | S063 health indicators; S064 stage gates and intake | T125 health model; T126 gate state machine; T127 health dashboard; T128 governance E2E | F031, F020 |
| F033 Resources/capacity | S065 resource profiles; S066 allocations | T129 resource schema; T130 capacity calendar; T131 allocation UI; T132 capacity tests | F011, F002 |
| F034 Workload/actuals | S067 workload conflicts; S068 time entries and planned vs actual | T133 workload query; T134 time entry tracking; T135 balancing UI; T136 performance tests | F033, F012 |

Exit: multiple projects roll up to governed portfolio health and resource capacity without leaking unauthorized data.

## E008 — Advanced modules and AI

Outcome: entitlement-gated modules and safe assisted work. Milestone M7.

| Feature | Stories | Tasks | Depends on |
|---|---|---|---|
| F050 Dynamic View | S099 restricted views; S100 controlled editing | T197 filter policy; T198 external access; T199 restricted UI; T200 isolation tests | F013, F036, F048 |
| F051 WorkApps | S101 app composition; S102 role experiences | T201 app manifest; T202 embedded surfaces; T203 role navigation; T204 app security tests | F013, F014, F023, F048 |
| F052 Data Shuttle | S103 scheduled file flows; S104 mapping and run history | T205 file scheduler; T206 import/export mapping; T207 archive UI; T208 replay tests | F010, F048 |
| F053 DataMesh | S105 reference mapping; S106 controlled sync | T209 mapping schema; T210 match engine; T211 sync controls; T212 conflict tests | F009, F035, F048 |
| F054 Bridge | S107 cross-system workflows; S108 run operations | T213 connector actions; T214 multi-step runtime; T215 run console; T216 failure tests | F019, F030, F048 |
| F055 Calendar App | S109 multi-source calendar; S110 publishing | T217 calendar aggregation; T218 calendar permissions; T219 calendar UI; T220 timezone tests | F013, F011, F048 |
| F056 Pivot App | S111 pivot configuration; S112 saved outputs | T221 pivot query engine; T222 pivot permissions; T223 pivot UI; T224 calculation tests | F021, F048 |
| F057 DAM assets | S113 asset library; S114 asset governance | T225 asset collections; T226 metadata/rights; T227 rendition UI; T228 lifecycle tests | F017, F020, F048 |
| F058 Mobile clients | S115 mobile work; S116 mobile offline/sync | T229 mobile shell; T230 mobile editing; T231 push/deep links; T232 mobile tests | F008, F014, F037 |
| F059 Publishing/embedding | S117 published artifacts; S118 embeds/access | T233 publish service; T234 scoped access tokens; T235 embed UI; T236 publish security tests | F013, F023, F036 |
| F060 Conditional formatting | S119 formatting rules; S120 visual states | T237 rule engine; T238 formatting UI; T239 evaluation path; T240 rule tests | F008, F035 |
| F061 Update requests | S121 request lifecycle; S122 recipient experience | T241 request schema/API; T242 reminder scheduler; T243 recipient form; T244 request tests | F008, F037 |
| F039 AI formulas/queries | S077 formula help; S078 natural-language reports | T153 provider boundary; T154 permission-filtered retrieval; T155 proposal/diff UI; T156 evaluation harness | F035, F021, F048 |
| F040 AI insights/automation | S079 risks/trends; S080 assisted actions | T157 evidence-backed insight jobs; T158 approval gate; T159 cost/safety controls; T160 red-team tests | F039, F018, F020 |

Exit: advanced modules are entitlement-gated, audited, reversible, and AI writes require explicit confirmation with evidence.

## Capability coverage ledger

| Source capability | Planned ID |
|---|---|
| Sheets/boards/rows/items/columns | F006–F008 |
| Grid/Gantt/calendar/card/timeline | F008, F012–F013 |
| WBS/dependencies/milestones/critical path/baselines | F009, F012, F015 |
| Formula parser, functions, incremental recalculation, cross-sheet references | F035 |
| Linked records and rollups | F009 |
| Search/import/export/large datasets | F010 |
| Reports/dashboards/KPIs/charts/trends/burndown/export | F021–F025 |
| Comments/mentions/activity/attachments/proofing/versioning | F016–F017 |
| Documents/folders/live editing/presence | F045–F046 |
| Sharing, guests, expiring links, external collaboration | F036 |
| Roles, ACLs, audit log | F003 |
| Approvals, routing, escalation | F020 |
| Notifications, channels, digests, quiet hours, push | F037 |
| Forms/conditional logic/embedded/mobile intake | F014 |
| Automation workflows and runtime | F018–F019 |
| Update requests and reminders | F061 |
| Conditional formatting | F060 |
| Published and embedded sheets/reports/dashboards | F059 |
| Mobile PWA, offline queue, push, deep links | F058 |
| Tenants, users, groups | F002 |
| OIDC login, sessions, MFA (WebAuthn/TOTP), API tokens, rate limits | F038 |
| SAML SSO, SCIM, group mapping | F026 |
| Retention, legal hold, export, purge, access review | F027 |
| REST API, OpenAPI, webhooks | F028 |
| Microsoft 365/Google/Slack/Jira/Salesforce/Box/Dropbox/Tableau/database adapters | F029–F030 |
| MCP resources/tools with permission and approval controls | F047 |
| Project templates, provisioning, baselines (Control Center provisioning) | F015 |
| Project health, stage gates, intake governance (Control Center governance) | F032 |
| Portfolio rollups | F031 |
| Resource profiles, skills, cost rates, capacity (Resource Management) | F033 |
| Workload, time entries, planned vs actual | F034 |
| Entitlements and feature-flag administration | F048 |
| Dynamic View restricted external access | F050 |
| WorkApps role-based app surfaces | F051 |
| Data Shuttle scheduled file movement | F052 |
| DataMesh reference-data synchronization | F053 |
| Bridge cross-system workflow orchestration | F054 |
| Calendar App multi-source publishing | F055 |
| Pivot App saved analysis | F056 |
| DAM/Brandfolder asset governance | F057 |
| AI formulas/queries/insights/assisted actions | F039–F040 |
| Localization, timezones, translations | F049 |
| Outbox, JetStream, worker, tracing, health, backups | F004 |
| Use-case solutions: PMO, IT, incidents, onboarding, change, vendors, marketing, CRM, budget, compliance | F015 template catalog |

## Cross-cutting task packs

Apply these to every feature where relevant:

- INFRA: container, local environment, secrets, migrations, health, deployment, rollback.
- SERVICE: Rust domain, application service, authorization, error contract, tracing.
- API: OpenAPI, request/response examples, idempotency, pagination, events, webhooks.
- UI: route, loading/empty/error/denied/success states, responsive layout, tokens, icons, accessibility.
- MOCK: deterministic fixture factory, isolated tenant, external-service mock, replayable seed.
- TEST: failing requirement test, unit, integration, E2E, permission, accessibility, performance.
- OPS: metrics, audit, alerts, runbook, feature flag, rollout, migration evidence.

## Build order

Complete epics in order. Within an epic, features are listed in build order; a feature may start when every ID in its `Depends on` column is accepted. Within a feature, complete contract and harness tasks before service/UI fanout. Do not start an item with unresolved dependencies or overlapping `owned_paths`.
