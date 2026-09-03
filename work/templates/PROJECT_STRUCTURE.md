# Project structure

```text
OpsHub/
├── Claude.md             # required rules; read first
├── MANIFEST.md           # optional-document index
├── automation/           # deterministic project gates
├── testing/              # isolated feature-gated harnesses
├── work/
│   ├── templates/
│   ├── plan.md
│   ├── epics/
│   ├── tickets/
│   ├── stories/
│   ├── tasks/
│   ├── inprogress/
│   └── archived/
└── docs/
    └── product-capability-spec.md
```

## Ticket movement

`tickets/F001-slug.md` → `inprogress/F001-slug.md` → `archived/F001-slug.md`

The same single feature ticket moves through all folders, keeping its ID, filename, branch, and history.

## Initial milestones

| ID | Name | Outcome |
|---|---|---|
| M001 | Foundation | Repository, CI, tenancy, identity, authorization, API conventions, test harness foundation |
| M002 | Core Work OS | Workspaces, sheets/boards, typed columns, rows/items, grid |
| M003 | Planning and Intake | Hierarchy, dates, dependencies, views, forms, templates |
| M004 | Automation and Collaboration | Workflows, approvals, notifications, comments, files |
| M005 | Reporting | Reports, dashboards, KPIs, charts, drill-through |
| M006 | Enterprise and Integrations | SSO, SCIM, audit/compliance, APIs, first connectors |
| M007 | PPM and Resources | Portfolios, health, baselines, capacity, workload |
| M008 | Advanced Modules and AI | Restricted app surfaces, data tools, AI |
