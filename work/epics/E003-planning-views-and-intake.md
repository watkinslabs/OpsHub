---
id: E003
type: epic
status: planned
owner: platform
target_milestone: M2
branch: e003-planning-views-and-intake
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7
- Capability contract: `docs/capability-contracts.md` rows F069, F070, F071, F072, F073, F011, F049, F012, F013, F014, F015
- Product spec: `docs/product-capability-spec.md` sections 5.1, 5.3, 5.7, 6, 7 (Phase 2)

# E003 — Planning, views, and intake

## Outcome

After E002 a team can store typed work records but cannot plan with them: rows have dates without a working calendar, there is no notion of predecessor and successor, the only presentations are grid and board, requests still arrive by email, and every new project is rebuilt by hand. E003 turns the canonical record model into a planning system. Dates become timezone-aware and calendar-aware (F011), text and numbers render in each tenant and user's locale with translated UI strings (F049), rows can depend on each other with FS/SS/FF/SF links, lag, cycle detection, critical path, and calendar-aware schedule shifts drawn on a Gantt (F012), the same sheet can be saved as card, calendar, and timeline views that are shareable and permission-aware (F013), work enters through internal and public forms with conditional logic, spam controls, and an immutable intake trail (F014), and a standard project is provisioned from a versioned template and measured against named baselines (F015). Milestone M2 corresponds to spec section 7 Phase 2.

## Scope

- Included: working calendars and calendar exceptions, sheet schedule settings and single-row reschedule, locale and timezone resolution (user, then tenant, then default), ICU message catalogs, row dependencies with four link types and signed lag, forward/backward-pass critical path, sheet-wide schedule shift with dry run, saved views of kind card, calendar, and timeline with typed filters, sorts, grouping, and view shares, form builder with immutable published versions, public submission tokens, rate limits, CAPTCHA/honeypot, draft submissions, immutable intake events, versioned project templates with a built-in use-case catalog, asynchronous provisioning runs with rollback, baselines and variance.
- Excluded: workflow execution triggered by form submissions (F018/F019), approvals (F020), notifications (F037), portfolio roll-ups and health (F031/F032), resource capacity that consumes working calendars (F033), published/embedded read-only views with public tokens (F059), conditional formatting (F060), update requests (F061), Dynamic View and WorkApps (F050/F051), mobile offline queues (F058).

## Child features

- `F072` Inbound email: per-sheet email addresses that turn a message and its attachments into a row, with the abuse defences an internet-facing mailbox needs (depends on F006, F017, F037).
- `F073` Announcements and in-app help: what changed and contextual help, targeted by plan and role, dismissible per user (depends on F002, F037).
- `F069` Home and my work: the landing surface after sign-in — assigned work, pending approvals, recents and favourites, all permission-filtered (depends on F005, F006, F013).
- `F070` Trash and recovery: one place to see and restore soft-deleted items across kinds, restoring under the original ACL (depends on F005, F006).
- `F071` Migration import: bringing a Smartsheet, Airtable or Excel workbook in as sheets, typed columns, views and links rather than flat rows (depends on F007, F010, F013).
- `F011` Dates and schedules: date/datetime semantics, working calendars, sheet schedule settings, row reschedule (depends on F007).
- `F049` Localization: locale and timezone settings per tenant and user, locale-aware date/number formatting, UTF-8 rules, translation message catalogs (depends on F005).
- `F012` Dependencies and Gantt: row dependencies (FS/SS/FF/SF, lag), cycle detection, critical path, schedule shift with working calendars, Gantt view (depends on F009, F011).
- `F013` Views: saved card, calendar, and timeline views with filters, sorts, grouping, sharing, and permission-aware row queries (depends on F008, F011).
- `F014` Forms: form builder, conditional rules, immutable published versions, public submission tokens with abuse controls, immutable intake events (depends on F007).
- `F015` Templates and baselines: versioned project templates, use-case catalog, provisioning jobs, baselines and variance (depends on F012, F013, F014).

## Integration path

The end-to-end path runs through the real API and web app: a portfolio admin publishes a template version, provisions a project into a workspace, the worker creates sheets, rows, dependencies, views, and a form; a project editor opens the Gantt, adds a dependency, shifts the schedule, and captures a baseline; an external requester submits the public form and the row appears in the card view; the same pages render in `de-DE` with the tenant timezone.

## Exit criteria

- [ ] All six child features accepted and archived with harness evidence under `testing/evidence/F011`, `F049`, `F012`, `F013`, `F014`, `F015`.
- [ ] Spec Phase 2 exit scenario passes as a Playwright suite: a standard project is provisioned from a template, planned with dependencies and critical path on a working calendar, visualized in card, calendar, timeline, and Gantt views, localized for a `de-DE`/`Europe/Berlin` user, and populated by a public form submission that survives replay, rate limiting, and honeypot checks.
- [ ] The section 8 MVP scenario steps "creates a workspace and project from a template" and "adds dates/dependencies, collects a request through a form" are green against the seeded pilot tenant.
- [ ] Cross-tenant, guest, link, and role-negative suites pass for every route in the six contract rows; no route leaks existence across tenants.
- [ ] p95 targets hold under load: view row query and schedule read under 500 ms, dependency create and reschedule under 800 ms, provisioning acknowledged under 2 s.
- [ ] Accessibility lanes report zero serious or critical axe violations on Gantt, card, calendar, timeline, form builder, public form, and template catalog pages.
- [ ] All six feature flags are off by default, each rollback verified on an empty tenant, and `cargo xtask validate-work`, `check-contracts`, and `check-migrations` pass.
