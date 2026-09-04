---
id: E008
type: epic
status: planned
owner: platform
target_milestone: M7
branch: e008-advanced-modules-and-ai
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9, 10
- Capability contract: `docs/capability-contracts.md` rows F050–F061, F039, F040
- Product spec: `docs/product-capability-spec.md` sections 5.1 (mobile, publishing, conditional formatting), 5.3 (update requests), 5.10, 5.11, and section 10 resolved decisions

# E008 — Advanced modules and AI

## Outcome

Every premium module from spec section 5.11 (Dynamic View, WorkApps, Data Shuttle, DataMesh, Bridge, Calendar App, Pivot App, DAM assets) ships as an entitlement-gated layer over the canonical record model, never as a second source of truth. A tenant administrator turns a module on with an entitlement record plus a feature flag that defaults off, sets tenant limits, and can turn it off again without data loss; every module route checks entitlement and flag state through the F048 evaluator before touching domain data. Mobile clients, published/embedded artifacts, conditional formatting, and update requests complete the spec 5.1 and 5.3 low-level bullets that were deferred from earlier epics. AI features run through a provider-neutral adapter, retrieve only permission-filtered data, and never commit a write without an explicit human confirmation recorded as an audit event.

## Scope

- Included: the premium modules themselves, gated by the F006-epic entitlement records they consume; feature flags with owner/rollout state/disable procedure/cleanup ticket, tenant overrides, and the evaluation endpoint (F048); restricted filtered views with field/row policies and controlled external editing (F050); no-code app shells with pages, role navigation, and published versions (F051); scheduled file ingestion/export with mapping, validation, archive, run history, and replay (F052); reference-data mapping, match engine, controlled sync, and conflict resolution across sheets (F053); multi-step cross-system workflows reusing the F019 runtime and F030 connector actions with a run console and step retry (F054); multi-source calendar aggregation, permissions, ICS publishing, and timezone handling (F055); pivots with saved outputs (F056); asset library with metadata, renditions, rights, and collections (F057); responsive PWA, offline queue, push, deep links (F058); scoped revocable publication and embed tokens (F059); typed conditional-formatting rules with deterministic visual states (F060); update requests with reminders and response audit trail (F061); AI formula/query proposals (F039) and evidence-backed insights and confirmed actions (F040).
- Excluded: new core primitives (sheets, columns, formulas, views, forms, reports, dashboards, workflows, connectors are owned by E002–E007 and only consumed here); packaging, billing, and plan catalogs (administration concern per spec section 10, not domain behavior); offline document co-editing (spec section 10 mobile decision); AI training on tenant data; arbitrary code execution in Bridge or workflow steps.

## Child features

- F050 Dynamic View: row/field filter policies, controlled external editing, public token access on top of F013 views and F036 sharing.
- F051 WorkApps: app manifest, pages embedding sheets/forms/reports/dashboards, role navigation, published versions at `/apps/{slug}`.
- F052 Data Shuttle: scheduled file ingestion/export flows with mapping, validation, archive, run history, and replay over F010 jobs.
- F053 DataMesh: reference-data mappings, match engine, controlled sync between sheets, conflict detection and resolution.
- F054 Bridge: multi-step cross-system flows reusing the F019 runtime and F030 connector actions, run console, per-step retry.
- F055 Calendar App: multi-source calendar aggregation, calendar permissions, ICS publishing, timezone-correct rendering.
- F056 Pivot App: configurable pivot dimensions/measures over reports with saved and materialized outputs.
- F057 DAM assets: asset library, metadata, renditions, rights, approvals, and collections over F017 files.
- F058 Mobile clients: responsive PWA shell, offline queued edits and forms, push, deep links, reconnect reconciliation.
- F059 Publishing/embedding: published sheets/reports/dashboards and embeds with scoped, revocable, expiring tokens.
- F060 Conditional formatting: typed rules evaluated against current values with deterministic visual states in every view.
- F061 Update requests: field/row update requests with recipients, due dates, reminders, and a response audit trail.
- F039 AI formulas/queries: formula proposals and natural-language report plans through the provider adapter with permission-filtered retrieval.
- F040 AI insights/automation: risk/anomaly/trend insights with evidence rows and diff-based actions gated by explicit confirmation.

## Exit criteria

- [ ] End-to-end scenario from spec section 7 Phase 7: an administrator enables a module for one tenant through an entitlement record and flag override, a module owner builds a Dynamic View, WorkApp, Data Shuttle flow, DataMesh mapping, Bridge flow, and Calendar and exercises each through the real UI and API; the administrator then disables the flag and every module route returns `denied` with reason `flag_disabled` while stored data remains intact and recoverable.
- [ ] Each module has entitlement, permission, audit, usage telemetry, support runbook, and rollback behavior verified in `testing/features/F0##/` and `testing/evidence/F0##/`.
- [ ] AI features pass the permission, citation, refusal, and mutation-safety evaluation suites; no AI path writes business data without a confirmed proposal and audit event.
- [ ] Mobile offline queue, publication tokens, conditional formatting, and update requests pass their permission-negative and reconciliation cases.
- [ ] All child features accepted, archived, and their flags recorded in the flag registry with owner, rollout state, and cleanup ticket.
