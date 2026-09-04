---
id: F066
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M1
parent_epic: E001
depends_on: [F004]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [automation/xtask/src/slo.rs, infra/slo/objectives.yml, infra/slo/exceptions.yml, infra/slo/runbook.md, infra/slo/README.md, infra/slo/tests/**, infra/alerts/burn-rate.yml, infra/prometheus/rules/slo-recording.yml, testing/fixtures/slo/**, testing/features/F066/**]
feature_flag: F066_FEATURE
flag_default: off
branch: f066-service-levels-and-error-budgets
started_at: null
finished_at: null
---

# F066 — Service levels and error budgets

## 1. Identity and dates

- Branch: `f066-service-levels-and-error-budgets`
- Capability area: reliability governance (spec section 6 availability, performance, and observability bullets; section 8 release gates)
- Aggregate: `service-level`
- Module slug: `slo`

### Decision references

- Architecture: `docs/architecture-decisions.md` sections 1, 3, 9, 10
- Canonical contract: `docs/capability-contracts.md` row F066 (aggregate `service-level`, module `slo`)

- Design: this feature has no user surface; it ships tooling, runtime or contracts only.

## 2. Requirement specification

### Problem and user outcome

`docs/product-capability-spec.md` section 6 states four numbers — 99.5% monthly availability for core read/write APIs, p95 interactive reads under 500 ms, p95 single-row writes under 800 ms, and async acknowledgement under 2 seconds — and nothing measures them. F004 exports `http_request_duration_seconds`, `outbox_publish_lag_seconds`, `job_runs_total`, and `dead_letters_total` on `/metrics`, and its `infra/alerts/rules.yml` pages on symptoms (`outbox_pending_events > 1000`, dead-letter increase, `/readyz` failure). A symptom alert says a queue is deep; it never says whether the promise to the customer is being kept, and nobody can answer "may we ship today?".

This feature turns those four numbers into measured service level indicators over F004's existing metrics, an error budget with an explicit window, multi-window multi-burn-rate alerts derived from that budget, a written exhaustion policy, and `cargo xtask verify-slo` as a release gate. It adds no route, no table, and no screen; it adds `infra/slo/objectives.yml` as the single declaration, generated Prometheus recording rules, `infra/alerts/burn-rate.yml`, and one xtask module.

As an operator, I want one file that states what we promise, rules that compute how much of the promise we have spent, alerts that distinguish "wake someone now" from "file a ticket", and a gate that refuses a release when the budget is gone, so that reliability is a measured account rather than an opinion.

### Functional requirements

- **FR-F066-01:** `infra/slo/objectives.yml` is the only declaration of service levels. It carries `version: 1`, `window: 28d`, a `classes` map, an `objectives` list, a `burn_alerts` list, and a `policy` block. Every other artefact in this feature — recording rules, burn alerts, the report — is derived from it; `cargo xtask verify-slo` rejects the file with `slo.schema` (exit 1) when a key is unknown, a target is outside `0 < target < 1`, a class is referenced by no objective, or two objectives share an `id`.
- **FR-F066-02:** Traffic is classified by route template and method, never by guesswork. `classes` declares `core_read` (`GET`, `HEAD`), `core_write` (`POST`, `PUT`, `PATCH`, `DELETE`), `async_ack` (`POST` responses with status 202), and the excluded classes `analytics`, `integration`, and `exempt`, each with an explicit list of axum route templates. The M1 seed puts `/api/v1/tenants/{id}`, `/api/v1/users`, `/api/v1/users/{id}`, `/api/v1/groups`, `/api/v1/groups/{id}`, `/api/v1/roles`, `/api/v1/sessions`, `/api/v1/api-tokens`, and `/api/v1/audit-events` in `core_read`; `/api/v1/tenants`, `/api/v1/tenants/{id}`, `/api/v1/users`, `/api/v1/users/{id}`, `/api/v1/groups`, `/api/v1/groups/{id}/members`, `/api/v1/roles`, `/api/v1/resources/{kind}/{id}/acl`, `/api/v1/sessions/{id}`, and `/api/v1/api-tokens` in `core_write`; `/api/v1/tenants/{id}/suspend`, `/api/v1/reports/{id}/refresh`, `/api/v1/metrics/{id}/recompute`, and `/api/v1/webhook-deliveries/{id}/replay` in `async_ack`; `/api/v1/reports`, `/api/v1/reports/{id}/rows`, `/api/v1/metrics/{id}/values`, and `/api/v1/dashboards` in `analytics`; `/api/v1/webhooks`, `/api/v1/webhooks/{id}/deliveries`, `/api/v1/applications`, and `/auth/integrations/{provider}/callback` in `integration`; and `/healthz`, `/readyz`, `/metrics`, `/auth/oidc/start`, and `/auth/oidc/callback` in `exempt`, because their latency is dominated by a third party or by the probe itself. Classes must be disjoint per `(route, method)` pair (`slo.class_overlap`), and a route present in the metrics sample but in no class fails with `slo.route_unclassified` naming the route and the feature id that must declare it.
- **FR-F066-03:** Objective `availability_core` is `sum(rate(http_request_duration_seconds_count{class=~"core_read|core_write",status!~"5.."}[w])) / sum(rate(http_request_duration_seconds_count{class=~"core_read|core_write"}[w]))` with target `0.995`. A request counts bad only on a 5xx status; `4xx` is a caller outcome and stays good, and `exempt`, `analytics`, and `integration` classes are absent from both numerator and denominator, which is exactly the "graceful degradation for analytics and integrations" the spec allows.
- **FR-F066-04:** Objective `latency_core_read` is `sum(rate(http_request_duration_seconds_bucket{class="core_read",le="0.5"}[w])) / sum(rate(http_request_duration_seconds_count{class="core_read"}[w]))` with target `0.95`, which is the ratio form of "p95 interactive reads under 500 ms". Requests that failed with 5xx are counted bad in this objective too, so a fast error cannot buy latency credit.
- **FR-F066-05:** Objective `latency_core_write` uses the same shape with `class="core_write"`, `le="0.8"`, target `0.95` (p95 single-row writes under 800 ms).
- **FR-F066-06:** Objective `ack_async` is `sum(rate(http_request_duration_seconds_bucket{class="async_ack",status="202",le="2"}[w])) / sum(rate(http_request_duration_seconds_count{class="async_ack"}[w]))` with target `0.99`. The measured event is the acknowledgement — the 202 that hands the caller a job id — not the job's completion, which F004's `job_run_duration_seconds` already covers.
- **FR-F066-07:** The window is a rolling 28 days, not a calendar month. A calendar month makes the budget vary by 10% between February and March, resets the account at midnight on the 1st so an incident on the last day is forgiven hours later, and cannot be expressed as a single Prometheus range selector; 28 days is a constant 40,320 minutes, covers exactly four whole weeks so the weekday and weekend traffic mix is identical in every window, and is written directly as `[28d]`. Budgets follow: `availability_core` 0.5% of 40,320 = **201.6 minutes**; `latency_core_read` and `latency_core_write` 5% = **2,016 minutes**; `ack_async` 1% = **403.2 minutes**. The recording rule `slo:budget:remaining_ratio28d{objective}` = `1 - (1 - slo:sli:ratio_rate28d) / (1 - target)` and `slo:budget:remaining_minutes28d{objective}` = `slo:budget:remaining_ratio28d * <budget minutes>` publish the account; remaining ratio is clamped at `-1` for display and the raw value is kept in the report.
- **FR-F066-08:** `infra/prometheus/rules/slo-recording.yml` is generated from `objectives.yml`, never hand-edited. It contains, per objective, `slo:sli:ratio_rate<w>` for `w` in `5m, 30m, 1h, 2h, 6h, 24h, 3d, 28d`, plus `slo:burn_rate:ratio_rate<w>` = `(1 - slo:sli:ratio_rate<w>) / (1 - target)` and the two budget rules from FR-F066-07. Class attribution happens in the rule text: each objective's selector is expanded to the explicit `route=~"..."` and `method=~"..."` alternation from its classes and `label_replace` stamps `class`, so no change to F004's exporter label set is required. `cargo xtask verify-slo` regenerates the file in memory and reports `slo.rule_drift` with the differing rule name when the checked-in file does not match byte for byte.
- **FR-F066-09:** `infra/alerts/burn-rate.yml` is generated with four multi-window pairs per objective. The burn factor is computed, not copied: `factor = consumed_fraction * 672 h / long_window_h`. Pairs are `1h/5m` at 2% of budget → **13.44** (`severity: page`, `for: 2m`), `6h/30m` at 5% → **5.6** (`severity: page`, `for: 15m`), `24h/2h` at 10% → **2.8** (`severity: ticket`, `for: 1h`), `3d/6h` at 10% → **0.93** (`severity: ticket`, `for: 6h`). Each alert requires both windows over the factor (`slo:burn_rate:ratio_rate<long> > f and slo:burn_rate:ratio_rate<short> > f`); the short window is one twelfth of the long one so the alert clears within minutes of recovery instead of dragging a spent spike across the long window. Every rule carries labels `objective`, `severity`, `window: <long>/<short>`, and annotations `summary`, `budget_minutes`, and `runbook: infra/slo/runbook.md#<anchor>`. `verify-slo` recomputes each factor and reports `slo.threshold_drift` with expected and found values on any mismatch, and `slo.window_pair` when a short window is not one twelfth of its long window.
- **FR-F066-10:** Meaning is written into the runbook and enforced by routing, not left to the reader. `13.44` means the 28-day budget is gone in 50 hours at the current rate: page the on-call immediately, any hour. `5.6` means gone in 5 days: page the on-call with a 30-minute response expectation. `2.8` means gone in 10 days: open a ticket by the next working day, assigned to the owning module's feature owner. `0.93` means a sustained low burn that will exhaust the budget within the window: open a ticket for the weekly operations review. A `SloNoData` alert (`severity: page`, `for: 15m`) fires when `absent(slo:sli:ratio_rate5m{objective="<id>"})`, because a silent measurement pipeline is indistinguishable from perfect service; an objective whose 28-day denominator is under 100 requests is reported `insufficient_data`, never `breached`, and is excluded from the freeze in FR-F066-14.
- **FR-F066-11:** F004's symptom alerts are linked to the objectives they threaten instead of being duplicated. `verify-slo` reads every rule file under `infra/alerts/` and reports `slo.alert_unlinked` (exit 1) for any alerting rule that lacks an `objective` label naming an id from `objectives.yml` and a `runbook` annotation resolving to an existing anchor. `infra/slo/runbook.md` documents the mapping: `outbox_pending_events > 1000` and dead-letter growth threaten `ack_async`, `/readyz` failure threatens `availability_core`. No rule in this feature restates a condition already covered by `infra/alerts/rules.yml`.
- **FR-F066-12:** The objectives depend on histogram bucket boundaries, so they are asserted, not assumed. `verify-slo` parses a Prometheus text exposition (`--metrics <file|url>`, default `http://127.0.0.1:9464/metrics`) and reports `slo.bucket_missing` naming the objective and the boundary when `http_request_duration_seconds_bucket` lacks an exact `le` series for `0.5`, `0.8`, or `2`, or when the metric is not a histogram. F004 owns the exporter; this gate is the contract that keeps its bucket list from drifting under the objectives.
- **FR-F066-13:** `cargo xtask verify-slo [--metrics PATH] [--json]` in static mode validates the schema (FR-F066-01), class disjointness and coverage (FR-F066-02), rule and threshold drift (FR-F066-08, FR-F066-09), alert linkage (FR-F066-11), and bucket boundaries (FR-F066-12). It follows the F041/F044 output rules exactly: one `BLOCKED: <code> <path>:<line>: <message>` line per finding on stderr sorted by path then line then code, `verify-slo passed (4 objectives, 7 classes)` on stdout when clean, and with `--json` (or `XTASK_FORMAT=json`) exactly one object `{ "command", "ok", "checked", "findings": [{ "code", "path", "line", "message" }], "duration_ms" }`. Exit codes are the shared convention: `0` clean, `1` findings, `2` usage or I/O error, `3` refusal.
- **FR-F066-14:** `cargo xtask verify-slo --budget --source <file|url> [--json]` reads the four `slo:budget:remaining_ratio28d` and `slo:sli:ratio_rate28d` series from a Prometheus instant-query URL or from a recorded snapshot JSON, and writes `testing/evidence/F066/slo-report.json` `{ generated_at, window: "28d", objectives: [{ id, target, ratio, remaining_ratio, remaining_minutes, budget_minutes, state, sample_count }], state, exceptions: [...] }` plus a plain-text table on stdout. State per objective is `ok` (remaining > 0.25), `guarded` (0 < remaining ≤ 0.25), `exhausted` (remaining ≤ 0), or `insufficient_data`. Any `exhausted` objective without a live exception prints `REFUSED: slo.budget_exhausted <id>` and exits `3`; `--budget` never writes the report when it exits 2.
- **FR-F066-15:** Exhaustion has a policy a team can follow, recorded in `infra/slo/runbook.md` and enforced by the exit code. In `ok` state nothing changes. In `guarded` state, a change to a module owned by a failing objective needs a named second reviewer on the pull request and a verified rollback entry in its `testing/evidence/<ID>/rollback.json`, and no feature flag is turned on in production. In `exhausted` state the release gate refuses: `verify-slo --budget` exits 3, so `verify-release` cannot record a signature, and only changes labelled `reliability`, `security`, or `rollback` may ship. The first item of the next iteration is the largest burn contributor named in the report. The freeze lifts automatically when the rolling window recovers above 25% remaining — no meeting is required to unfreeze — or by an entry in `infra/slo/exceptions.yml` `{ objective, reason, owner, ticket, expires_at }` with `expires_at` at most 14 days out; an expired or malformed entry is `slo.exception_expired` (exit 1) and does not suppress the refusal.
- **FR-F066-16:** The objectives are proven without a cluster. `infra/slo/tests/*.promtool.yml` are `promtool test rules` suites (Prometheus 3.4) that feed synthetic series into the real generated recording and alerting rules and assert both the computed ratios and which alerts fire at which minute; `testing/fixtures/slo/expositions/*.txt` are recorded `/metrics` snapshots (healthy, missing `le="0.8"`, unclassified route `/api/v1/widgets`) for the static gate; `testing/fixtures/slo/windows/*.json` are recorded instant-query snapshots (all `ok`, one `guarded`, one `exhausted`, one `insufficient_data`, one with an unexpired exception) for `--budget`. No test in `testing/features/F066/` starts Prometheus, a database, or the API.

### Non-functional requirements

- **NFR-F066-01 Performance:** static `verify-slo` completes in under 2 seconds over `objectives.yml`, both rule files, and a 2 MiB exposition; `--budget` against a recorded snapshot completes in under 500 ms and against a live Prometheus in under 5 seconds; the promtool suite completes in under 60 seconds on `ubuntu-latest`. Generated rules are cardinality-bounded: at most 8 classes and 6 objectives, producing at most 40 recorded series regardless of route count, because every rule aggregates `route` and `status` away with `sum by (objective)`. `verify-slo` reports `slo.cardinality` when a generated rule would keep `route` in its output labels.
- **NFR-F066-02 Security/privacy:** `objectives.yml`, the generated rules, and `slo-report.json` contain no tenant id, user id, or request payload — only route templates, methods, status classes, and aggregate ratios. Static mode makes no network call at all; `--source` accepts a URL only when explicitly passed, sends no credentials on the command line (bearer token read from `secret://slo-prometheus` through the F004 secret source), and `/metrics` stays on the internal port F004 defined. The gate never writes outside `infra/slo/`, `infra/alerts/burn-rate.yml`, `infra/prometheus/rules/`, and `testing/evidence/F066/`.
- **NFR-F066-03 Accessibility:** all output is ASCII, honours `NO_COLOR`, never conveys state by colour alone (`ok`, `guarded`, `exhausted`, `insufficient_data` are printed as words in a column), wraps no line beyond 200 characters, and the `--json` form is a complete structural equivalent of the text report. `infra/slo/runbook.md` uses a heading hierarchy with one anchor per alert severity and plain-text tables that read correctly in a screen reader.
- **NFR-F066-04 Reliability/observability:** the alerting pipeline is itself monitored by `SloNoData` (FR-F066-10); every alert resolves to a runbook anchor (FR-F066-11); rules are generated and drift-checked so a hand edit fails CI rather than silently changing the promise; two runs of `--budget` over the same snapshot produce byte-identical `slo-report.json` apart from `generated_at`, and the report records the objectives file's SHA-256 so a report can be tied to the promise it measured.
- **NFR-F066-05 Governance:** every exception is bounded — owner, linked ticket, reason, and expiry at most 14 days — and the report lists live exceptions next to the objective they suppress, so an audit of "why did this ship" is a file read. The weekly operations review reads `slo-report.json`, not a dashboard screenshot.

### Scope

Included: `infra/slo/objectives.yml` and its schema, the route class registry and coverage gate, four objectives with a rolling 28-day window and budget arithmetic, generated recording rules, generated multi-window multi-burn-rate alerts with computed factors, the no-data alert, alert-to-objective linkage for F004's existing rules, the histogram bucket contract, `cargo xtask verify-slo` in static and budget modes with exit codes 0/1/2/3, the exhaustion policy and exception lifecycle, `infra/slo/runbook.md`, promtool rule suites, and recorded exposition and window fixtures.

Excluded: exporting the metrics themselves and the `/metrics` endpoint (F004); alert delivery, routing, and paging schedules (deployment configuration, out of the first release); dashboards and Grafana boards; per-tenant service levels and any customer-facing status page; load generation to prove the targets (F067); `verify-release` itself and its evidence signing (F044); adding routes to the class registry for features that do not exist yet — each later feature adds its own rows when it releases.

## 3. UX specification

No UI. The operator surface is one declaration file, two generated rule files, a runbook, and one command.

- Entry points: `cargo xtask verify-slo`, `cargo xtask verify-slo --json`, `cargo xtask verify-slo --metrics testing/fixtures/slo/expositions/healthy.txt`, `cargo xtask verify-slo --budget --source http://prometheus:9090`, `cargo xtask verify-slo --budget --source testing/fixtures/slo/windows/guarded.json --json`.
- Primary flow: an operator edits `infra/slo/objectives.yml`, runs `cargo xtask verify-slo --write-rules` to regenerate `infra/prometheus/rules/slo-recording.yml` and `infra/alerts/burn-rate.yml`, commits all three, and CI re-runs `verify-slo` without `--write-rules` so a hand edit to either generated file fails as `slo.rule_drift`.
- Success: `verify-slo passed (4 objectives, 7 classes)`, exit 0. Budget mode prints a five-column table `objective | target | 28d ratio | remaining | state` and `slo report written testing/evidence/F066/slo-report.json`.
- Findings: `BLOCKED: slo.route_unclassified infra/slo/objectives.yml:31: /api/v1/widgets seen in metrics sample; classify it in the owning feature's release`, then `verify-slo failed: 3 findings`, exit 1.
- Refused: `REFUSED: slo.budget_exhausted availability_core (remaining -37.2 minutes of 201.6)` after the full table is printed, exit 3, no partial report suppressed.
- Empty and error: no exposition available → `skipped: metrics sample absent` and the bucket check passes, matching F044's treatment of absent optional inputs; an unreadable file or unknown flag → message on stderr, exit 2.
- Permission-denied: writing the report requires the `operator` role of the catalog row, asserted as `XTASK_ROLE=operator` or CI on `main`; otherwise `--budget` runs every check, prints `dry run: operator role required to record`, and exits 3 without writing, mirroring F044 FR-F044-14.
- Responsive and keyboard: not applicable; output is line-oriented and wraps at 100 columns.

## 4. Technical specification

### Rust backend

Canonical contract: aggregate `service-level`; module `slo`; surface `cargo xtask verify-slo`, `infra/slo/objectives.yml`, `infra/alerts/burn-rate.yml`, `/metrics` recording rules; events none; persistence `infra/slo/**` and the Prometheus recording rules; role operator.

- `automation/xtask/src/slo.rs` (single module, under 500 lines) with: `Objectives` (serde model of the whole file), `Class { methods, routes, excluded }`, `Objective { id, sli: Sli::Availability | Sli::Latency { threshold_seconds }, classes, target, status_filter }`, `BurnAlert { severity, long, short, consumed }`, `Policy { guarded_below, exception_max_days }`, `Budget { minutes(window), remaining_ratio(ratio, target) }`, `render_recording_rules(&Objectives) -> String`, `render_burn_alerts(&Objectives) -> String`, `check_exposition(&str, &Objectives)`, `check_alert_links(&Path)`, `budget_report(&Snapshot, &Objectives) -> Report`, and `verify_slo(args) -> Result<(), String>`.
- Reuses F041's `support::{OutputFormat, front_value}` reporter and F042's finding type; adds no new dependency beyond `serde_yaml`, already required by the workspace.
- Production call path: `verify_slo` is dispatched from `automation/xtask/src/main.rs` (`Some("verify-slo") => slo::verify_slo(args)`), a one-line addition made under the F041 owner's review at integration, and is invoked from `.github/workflows/gates.yml` as a step owned by F001; `infra/slo/README.md` carries the exact dispatch line and CI step text so both edits are mechanical.
- Error mapping: `serde_yaml` failure → `slo.schema` at the reported line, exit 1; unreadable file or unknown flag → exit 2; `slo.budget_exhausted` and the missing operator role → exit 3; every other check returns findings and never panics.
- No event is published and no aggregate is persisted; the catalog row lists `none` for events and this feature adds none.
- Data access (decision 2.1): the `service-level` aggregate owns no table and no repository; `verify-slo` reads YAML and queries Prometheus only, holds no SQL string, `sqlx` dependency, or database connection, and the harness proves it by running the command with no database reachable.

### Interface

This feature has no HTTP surface, so its interface is four shapes and one command: the declaration
file that is the only place a service level is stated, the exception file that is the only way a
refusal is suppressed, the report that is the only artefact a release decision reads, and the
arguments, findings and exit codes of `verify-slo`. Every generated rule is derived from the first of
those, so the schema below is the whole authored surface. Ratios are decimals in `0 < x <= 1`; minutes
are decimal minutes; timestamps are RFC 3339 UTC. An unknown key anywhere is `slo.schema`, exit `1`.

**`Objectives`** — the top level of `infra/slo/objectives.yml`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `version` | integer | yes | `1`; any other value is `slo.schema` |
| `window` | string | yes | `28d`; the rolling window of FR-F066-07, written directly as a Prometheus range selector |
| `classes` | map<string, Class> | yes | 1–8 entries (NFR-F066-01's cardinality bound); a class referenced by no objective and not marked `excluded` is `slo.schema` |
| `objectives` | Objective[] | yes | 1–6 entries; a duplicate `id` is `slo.schema` |
| `burn_alerts` | BurnAlert[] | yes | the four pairs of FR-F066-09; a short window that is not one twelfth of its long window is `slo.window_pair` |
| `policy` | Policy | yes | |

**`Class`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `methods` | string[] | yes | HTTP methods this class covers; `async_ack` additionally pins status `202` |
| `routes` | string[] | yes | axum route templates, never concrete paths; two classes covering the same `(route, method)` pair is `slo.class_overlap`, and a route seen in the metrics sample and in no class is `slo.route_unclassified` naming the route and the feature id that must declare it |
| `excluded` | bool | no | default `false`; `true` keeps the class out of every objective's numerator and denominator, which is what `analytics`, `integration` and `exempt` are for |

**`Objective`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `id` | string | yes | `^[a-z][a-z0-9_]{2,40}$`; unique; the `objective` label on every generated rule and alert |
| `sli` | `"availability" \| "latency"` | yes | `availability` counts a request bad only on a 5xx; `latency` counts a request good when it fell in the `le` bucket **and** did not 5xx, so a fast error buys no latency credit |
| `threshold_seconds` | decimal | when `sli` is `latency` | one of the histogram boundaries the exporter publishes; a boundary with no exact `le` series is `slo.bucket_missing` naming the objective and the boundary |
| `classes` | string[] | yes | keys of `classes`; naming an `excluded` class is `slo.schema` |
| `target` | decimal | yes | strictly `0 < target < 1`; `1.0` is `slo.schema`, because a budget of zero minutes cannot be spent or reported |
| `status_filter` | string? | no | an extra status selector, used by `ack_async` to pin `202` |

**Budget arithmetic**, derived from `target` and the 40,320 minutes of a 28-day window, never authored:

| Objective | `target` | Budget minutes |
|---|---|---|
| `availability_core` | 0.995 | 201.6 |
| `latency_core_read` | 0.95 | 2,016 |
| `latency_core_write` | 0.95 | 2,016 |
| `ack_async` | 0.99 | 403.2 |

**`BurnAlert`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `severity` | `"page" \| "ticket"` | yes | the routing decision, and the word the runbook anchor is named for |
| `long` / `short` | string | yes | Prometheus durations; `short` must be exactly one twelfth of `long`, so an alert clears within minutes of recovery instead of dragging a spent spike across the long window |
| `consumed` | decimal | yes | the fraction of the 28-day budget the pair fires at — 0.02, 0.05, 0.10, 0.10 |
| `for` | string | yes | the pending duration: `2m`, `15m`, `1h`, `6h` |

`factor = consumed * 672h / long_window_h`, giving 13.44, 5.6, 2.8 and 0.93, and both windows must
exceed it for the alert to fire. `verify-slo` recomputes every factor and reports
`slo.threshold_drift` with `expected` and `found` on a mismatch, which is what makes a hand-edited
threshold fail rather than silently change the promise.

**`Policy`** — `{ guarded_below: decimal (0.25), exception_max_days: integer (14) }`.

**`Exception`** — one entry of `infra/slo/exceptions.yml`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `objective` | string | yes | an `id` from `objectives.yml`; an exception for a different objective suppresses nothing |
| `reason` | string | yes | non-empty |
| `owner` | string | yes | the person accountable while the freeze is lifted |
| `ticket` | string | yes | a work-item id |
| `expires_at` | timestamp | yes | at most `exception_max_days` from now; expired or malformed is `slo.exception_expired`, exit `1`, and does not suppress the refusal |

**Generated rule names.** `infra/prometheus/rules/slo-recording.yml` is regenerated in memory and
compared byte for byte; a difference is `slo.rule_drift` naming the differing rule.

| Rule | Windows | Meaning |
|---|---|---|
| `slo:sli:ratio_rate<w>{objective}` | `5m, 30m, 1h, 2h, 6h, 24h, 3d, 28d` | good events over all events in `w` |
| `slo:burn_rate:ratio_rate<w>{objective}` | the same eight | `(1 - ratio) / (1 - target)` |
| `slo:budget:remaining_ratio28d{objective}` | 28d only | `1 - (1 - ratio) / (1 - target)`, clamped at `-1` for display, raw in the report |
| `slo:budget:remaining_minutes28d{objective}` | 28d only | the remaining ratio scaled by the objective's budget minutes |

Every rule aggregates `route` and `status` away with `sum by (objective)`, so at most 40 series exist
regardless of route count; a generated rule that would keep `route` in its output labels is
`slo.cardinality`.

**`SloReport`** — `testing/evidence/F066/slo-report.json`, and the `--budget --json` object

| Field | Type | Notes |
|---|---|---|
| `generated_at` | timestamp | the only non-deterministic field; two runs over one snapshot are otherwise byte-identical |
| `window` | string | `"28d"` |
| `objectives_sha256` | string | hex digest of `objectives.yml`, so a report is tied to the promise it measured |
| `objectives` | ObjectiveResult[] | one per objective, in declaration order |
| `state` | `"ok" \| "guarded" \| "exhausted" \| "insufficient_data"` | the worst objective state present, ignoring `insufficient_data` |
| `exceptions` | Exception[] | live exceptions only, listed beside the objective they suppress |

**`ObjectiveResult`**

| Field | Type | Notes |
|---|---|---|
| `id` / `target` | string / decimal | |
| `ratio` | decimal | `slo:sli:ratio_rate28d` |
| `remaining_ratio` | decimal | raw, not clamped; negative once the budget is overspent |
| `remaining_minutes` | decimal | `remaining_ratio * budget_minutes` |
| `budget_minutes` | decimal | from the table above |
| `state` | `"ok" \| "guarded" \| "exhausted" \| "insufficient_data"` | `ok` above 0.25 remaining, `guarded` in `(0, 0.25]`, `exhausted` at or below 0, and `insufficient_data` under 100 requests in the window — which is never `breached` and never freezes a release |
| `sample_count` | integer | the 28-day denominator, which is what makes `insufficient_data` checkable rather than asserted |

**Command arguments.** `cargo xtask verify-slo [args]`.

| Argument | Type | Required | Constraint |
|---|---|---|---|
| `--metrics <PATH\|URL>` | string | no | a Prometheus text exposition; defaults to the internal metrics endpoint; absent → `skipped: metrics sample absent` and the bucket check passes |
| `--budget` | flag | no | switches to budget mode, which requires `--source` |
| `--source <PATH\|URL>` | string | with `--budget` | a recorded instant-query snapshot or a Prometheus URL; a bearer token is read from the F004 secret source, never from the command line |
| `--write-rules` | flag | no | regenerates both rule files; CI runs without it so a hand edit fails as `slo.rule_drift` |
| `--json` | flag | no | one object on stdout: `{ command, ok, checked, findings: [{ code, path, line, message }], duration_ms }`, or the `SloReport` in budget mode |

`XTASK_ROLE=operator` with `XTASK_OWNER`, or CI on `main`, is required to record the report; without
it `--budget` runs every check, prints `dry run: operator role required to record`, and exits `3`.

**Findings and exit codes.** One line per finding on stderr as `BLOCKED: <code> <path>:<line>:
<message>`, sorted by path then line then code; ASCII, `NO_COLOR`-aware, no line past 200 characters.

| Code | Produced when |
|---|---|
| `slo.schema` | an unknown key, a target outside `0 < t < 1`, a duplicate `id`, or a class no objective references |
| `slo.class_overlap` / `slo.route_unclassified` | two classes cover one `(route, method)` pair / a sampled route belongs to no class |
| `slo.rule_drift` / `slo.threshold_drift` / `slo.window_pair` | a generated file edited by hand / a burn factor that is not the computed one / a short window that is not one twelfth of its long window |
| `slo.alert_unlinked` | an alerting rule under `infra/alerts/` with no `objective` label naming a declared id, or a `runbook` annotation whose anchor does not exist |
| `slo.bucket_missing` | a latency objective's boundary has no exact `le` series, or the metric is not a histogram |
| `slo.cardinality` | a generated rule would keep `route` in its output labels |
| `slo.exception_expired` | an exception past `expires_at` or missing a required field |
| `slo.budget_exhausted` | budget mode found an `exhausted` objective with no live exception — a refusal, not a finding |

| Exit | Meaning |
|---|---|
| `0` | clean; `verify-slo passed (4 objectives, 7 classes)` |
| `1` | findings; `verify-slo failed: <n> findings` |
| `2` | usage or I/O error; `--budget` writes no report on this path |
| `3` | refused: `slo.budget_exhausted`, or the operator role absent after a full dry run |

### Use case signatures

In `automation/xtask/src/slo.rs`. There is no `Ctx` and no `UnitOfWork`: the `service-level` aggregate
owns no table, and `verify-slo` holds no SQL string, no SQLx dependency and no database connection —
the harness proves it by running the command with no database reachable. `Finding` is F042's type and
the reporter is F041's.

```rust
fn load_objectives(path: &Path) -> Result<Objectives, Vec<Finding>>;
fn check_classes(objectives: &Objectives) -> Vec<Finding>;
fn render_recording_rules(objectives: &Objectives) -> String;
fn render_burn_alerts(objectives: &Objectives) -> String;
fn check_rule_drift(objectives: &Objectives, committed: &Path) -> Vec<Finding>;
fn check_exposition(exposition: &str, objectives: &Objectives) -> Vec<Finding>;
fn check_alert_links(alerts_dir: &Path, objectives: &Objectives, runbook: &Path) -> Vec<Finding>;
fn budget_minutes(target: f64, window_minutes: f64) -> f64;
fn burn_factor(consumed: f64, long_window_hours: f64) -> f64;
fn remaining_ratio(ratio: f64, target: f64) -> f64;
fn load_exceptions(path: &Path, now: Timestamp) -> Result<Vec<Exception>, Vec<Finding>>;
fn budget_report(snapshot: &Snapshot, objectives: &Objectives, exceptions: &[Exception], now: Timestamp) -> SloReport;
fn verify_slo(args: &Args) -> Result<(), String>;
```

`budget_minutes`, `burn_factor` and `remaining_ratio` are pure arithmetic taking no file and no
client, which is why the four burn factors and the four budgets are unit-tested as values rather than
asserted against a rendered file; `render_recording_rules` and `render_burn_alerts` are pure functions
of `Objectives`, which is what makes drift a byte comparison rather than a judgement.

Write boundaries, in place of a transaction boundary this feature has no database to open:

- `--write-rules` regenerates **both** rule files or neither: recording rules and burn alerts are
  derived from one declaration, and a tree holding a new recording rule beside an old alert would
  page on a factor computed from a target that no longer exists.
- `budget_report` writes `slo-report.json` as one temp file plus rename, and only after the snapshot
  parsed and the role check passed; an exit `2` writes nothing, and an exit `3` still writes the
  report when the role permitted it, because a refusal a reader cannot inspect is not evidence.
- `infra/slo/exceptions.yml` is authored, never written by this command. Nothing else in this feature
  writes, and it never writes outside its four owned directories.

### PostgreSQL/SQLx

No schema change. This feature adds no migration, no table, no index, and no audit action, and `services/api/migrations/` is untouched — `cargo xtask check-migrations` must report the same file count before and after. The negative control is enforced in `testing/features/F066/database/cases.md`: no `*_slo_*.sql` file exists, `verify-slo` opens no database connection (the harness runs it with `OPSHUB_DATABASE_URL` unset and with a listener on the configured port that fails the test on any accepted connection), and the only durable state this feature writes is `infra/slo/exceptions.yml` and `testing/evidence/F066/slo-report.json`.

### React/TypeScript

No UI, no component, and no client. `apps/web/` is untouched and no route reaches `openapi/v1.json`. The report is the surface, and it renders twice: a plain-text table on stdout and the `--json` object of FR-F066-13 and FR-F066-14, following the F041 output rules (single JSON object, findings array, `NO_COLOR`, ASCII, 200-column limit). The files delivered in place of a component tree are `infra/slo/objectives.yml`, `infra/slo/exceptions.yml`, `infra/slo/runbook.md`, `infra/slo/README.md`, `infra/prometheus/rules/slo-recording.yml`, `infra/alerts/burn-rate.yml`, and `infra/slo/tests/{availability,latency,ack,no_data}.promtool.yml`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F066-01 through FR-F066-16 and NFR-F066-01 through NFR-F066-05 in `testing/features/F066/requirements/cases.md`
- [ ] Failure/edge-case tests: unknown schema key, target of 1.0, duplicate objective id, class overlap on `(route, method)`, unclassified route, missing `le="0.8"` bucket, hand-edited recording rule, hand-edited burn factor, short window not one twelfth of the long window, alert without an `objective` label, runbook anchor that does not exist, zero-traffic window, expired exception
- [ ] Permission-negative tests: `--budget` without `XTASK_ROLE=operator` runs dry and writes nothing (exit 3); an exhausted budget refuses regardless of role; an exception for a different objective does not suppress the refusal
- [ ] Rust unit tests in `testing/features/F066/api/`: budget minutes arithmetic, burn factor derivation for all four pairs, remaining-ratio clamping, exposition parsing, snapshot parsing, report determinism
- [ ] CLI contract tests in place of API integration tests: exit codes 0/1/2/3, `BLOCKED:` line format and ordering, JSON object shape, `skipped:` line when no exposition is available, and a negative control proving no socket is opened in static mode
- [ ] Database negative controls: no migration added, no connection opened, no table referenced
- [ ] Frontend negative controls in place of component tests: text and JSON report parity, `NO_COLOR`, line width, and an assertion that `apps/web/` and `openapi/v1.json` are unchanged
- [ ] PromQL tests: `promtool test rules infra/slo/tests/*.promtool.yml` over the generated rules — ratios, burn rates, and which alert fires at which minute
- [ ] Accessibility tests: ASCII-only, no colour-only state, JSON parity, runbook heading and anchor structure
- [ ] Performance tests: static run under 2 s, budget run under 500 ms on a snapshot, promtool suite under 60 s, generated series count at most 40

### Fast fanout configuration

- Test harness path: `testing/features/F066/`
- Feature flag: `F066_FEATURE`
- Fixture/seed factory: `testing/fixtures/slo/` — `expositions/{healthy,missing_bucket,unclassified_route,no_histogram}.txt` recorded from F004's `/metrics`, `windows/{ok,guarded,exhausted,insufficient_data,exception_live}.json` instant-query snapshots, `objectives/{valid,overlap,bad_target,duplicate_id}.yml`, and `rules/{generated,hand_edited}.yml`
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z` for `generated_at` and exception expiry, integer-valued counter series in the promtool suites so every ratio is exact, and a recorded SHA-256 of each objectives fixture
- Mock/stub contracts: no HTTP client is exercised in static mode; `--source` is fed a local snapshot file, and the one live-URL test points at a loopback listener that returns a canned instant-query body
- Parallel isolation: every case runs in a temporary directory holding its own copy of `infra/slo/` and `infra/alerts/`; nothing is shared, and no port is bound except the loopback listener, which is allocated on port 0
- Targeted command: `cargo xtask test-feature F066`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F066/` holding `slo-report.json`, the promtool output, and the generated-versus-committed rule diff

## 6. Acceptance criteria

```gherkin
Feature: Service levels and error budgets

Scenario: The promise is measured from the runtime metrics
  Given infra/slo/objectives.yml declaring availability_core at 0.995 over a rolling 28-day window
  When cargo xtask verify-slo runs against a recorded /metrics exposition
  Then the generated recording rules contain slo:sli:ratio_rate28d for all four objectives
  And slo:budget:remaining_minutes28d for availability_core is scaled by 201.6 minutes
  And the command prints "verify-slo passed (4 objectives, 7 classes)" with exit code 0

Scenario: Analytics traffic cannot spend the core budget
  Given a window in which every /api/v1/reports request returns 500 and every core request succeeds
  When the promtool suite evaluates the recording rules
  Then slo:sli:ratio_rate1h for availability_core stays at 1
  And no burn-rate alert fires

Scenario: A fast burn pages and a slow burn tickets
  Given core availability at 90 percent for 65 minutes
  When the promtool suite evaluates infra/alerts/burn-rate.yml
  Then SloFastBurn for availability_core fires after 7 minutes with severity page, window 1h/5m, and factor 13.44
  And after recovery it resolves within 7 minutes because the 5m window clears first
  And a sustained 3 percent error rate over three days fires only the 3d/6h rule with severity ticket

Scenario: A hand-edited rule fails the gate
  Given someone changes the 6h burn factor in infra/alerts/burn-rate.yml from 5.6 to 10
  When cargo xtask verify-slo --json runs
  Then the findings array contains slo.threshold_drift with expected 5.6 and found 10
  And the exit code is 1

Scenario: An exhausted budget refuses the release
  Given a recorded snapshot where availability_core has spent 238 of its 201.6 budget minutes
  When XTASK_ROLE=operator cargo xtask verify-slo --budget --source that snapshot runs
  Then the table prints availability_core as exhausted with remaining -37.2 minutes
  And stderr ends with "REFUSED: slo.budget_exhausted availability_core" and the exit code is 3
  When infra/slo/exceptions.yml records that objective with an owner, a ticket, and an expiry 7 days out
  Then the same command exits 0 and the report lists the live exception

Scenario: A silent measurement pipeline is not perfect service
  Given the recording rules stop producing slo:sli:ratio_rate5m for ack_async
  When 15 minutes pass in the promtool suite
  Then SloNoData fires for ack_async with severity page
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F004 (the `/metrics` exporter, `http_request_duration_seconds`, and `infra/alerts/rules.yml` this feature measures and links); decisions sections 1, 3, 9, 10; contracts row F066
- Blocks: nothing formally; every later feature adds its routes to `infra/slo/objectives.yml` when it releases, and `slo.route_unclassified` is the reminder
- Conflicts with: none. F004 owns `infra/**` as an exempt root and is archived before this feature starts, so the narrower paths claimed here are never concurrently owned; this feature reads `infra/alerts/rules.yml` and never writes it
- External dependencies: Prometheus 3.4 `promtool` in CI (pinned in the workflow step text in `infra/slo/README.md`); a Prometheus server is needed only for `--budget --source <url>` and never for the harness
- Risks and mitigations: F004's histogram bucket list could omit `0.5`, `0.8`, or `2`, which would silently make a latency objective unmeasurable, so FR-F066-12 fails the gate instead — the objectives state the boundaries they need; route templates change as features land, so an unclassified route fails the gate rather than quietly leaving traffic out of the denominator; `promtool` output format changes between Prometheus majors, so the version is pinned and the suite is part of the harness; a 28-day window means a bad day stays visible for four weeks, which is the intent, and the exception file is the bounded escape hatch; the `main.rs` dispatch line and the `gates.yml` step live in F041- and F001-owned files and are one-line mechanical additions recorded in `infra/slo/README.md`
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration status (none), and rollback procedure.

## 8. Entry criteria — ready for implementation

- [ ] F004 accepted and archived, with `/metrics` exposing `http_request_duration_seconds` and `infra/alerts/rules.yml` present
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F066/`
- [ ] Owned paths claimed and disjoint; `infra/slo/`, `infra/prometheus/rules/`, and `automation/xtask/src/slo.rs` free
- [ ] `promtool` 3.4 available in the CI image and recorded exposition fixtures captured from a running F004 stack

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] `promtool test rules infra/slo/tests/*.promtool.yml` passes against the committed generated rules
- [ ] `cargo xtask verify-slo` exits 0 on the repository and 1, 2, and 3 on the matching fixtures, with the `--json` shape asserted
- [ ] Production call path named: `automation/xtask/src/main.rs` dispatches `verify-slo` and `.github/workflows/gates.yml` runs it on every pull request
- [ ] A first `slo-report.json` recorded under `testing/evidence/F066/` from the staging Prometheus
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `validate-work`, and `check-contracts` pass
- [ ] Rollback verified: disable `F066_FEATURE` (the CI step is skipped and the alert files stop being generated; no migration exists to revert)
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- The four numbers in spec section 6 are now measured objectives over F004's metrics with a rolling 28-day window and a stated error budget (201.6 minutes for core availability), multi-window burn-rate alerts whose factors are derived from that budget, and a written policy for what a guarded or exhausted budget means.
- `cargo xtask verify-slo` is a release gate: it fails on schema errors, unclassified routes, missing histogram buckets, drifted rules or thresholds, and unlinked alerts, and refuses (exit 3) while an objective's budget is exhausted without a bounded exception.
- No migration, no route, and no UI. Feature is off by default behind `F066_FEATURE`.
