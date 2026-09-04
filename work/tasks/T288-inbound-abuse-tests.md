---
id: T288
type: task
status: planned
parent_epic: E003
parent_feature: F072
parent_story: S144
depends_on: [S144, T287]
owned_paths: [testing/features/F072/**]
feature_flag: F072_FEATURE
branch: t288-inbound-abuse-tests
started_at: null
finished_at: null
---

# T288 — Inbound abuse tests

## Identity

- Parent story: `S144` Message to row
- Owner: platform
- Branch: `t288-inbound-abuse-tests`
- Decision references: `docs/architecture-decisions.md` sections 9, 3; `docs/capability-contracts.md` row F072; `docs/threat-model.md` sections 3.1, 3.4, 3.5

## Objective

Build the adversarial corpus and the end-to-end, accessibility and performance lanes that prove the abuse defences hold: no oracle on address existence, no unauthenticated write, no HTML or formula execution, no forged threading, no lost mail, and no unbounded ingestion.

## Specification

- Owned paths: `testing/features/F072/{requirements,api,database,frontend,e2e,accessibility,performance}/`, `testing/features/F072/{README.md, feature.toml}`, the corpus under `testing/features/F072/e2e/corpus/`
- Contract/input: the `.eml` corpus — a clean tenant-member message with a PDF, a DMARC-failing spoof of a tenant member, a DKIM `temperror`, an unaligned `dmarc = none`, an allow-list subdomain sender, an outsider under `tenant_members`, a 30 MB message, a 61st message inside one hour, an eleventh message from one sender, an auto-reply carrying `Auto-Submitted: auto-replied`, a mailing-list message carrying `List-Id`, a loop carrying `X-Loop`, a message with 26 `Received` headers, an HTML-only body with a `script` tag and a remote image, a body whose first character is `=`, a subject of 900 characters with an RFC 2047 encoded word, a five-deep `message/rfc822` forward, a truncated MIME tree, a message with eleven attachments including one the scanner quarantines and one outside the F017 allowlist, a valid plus-token reply, a forged `In-Reply-To` naming another tenant's row, and a token on its 21st use.
- Output/behavior: `e2e/inbound_email.spec.ts` drives the mock provider and the web app for the accept, reject and thread journeys; `accessibility/inbound_email.a11y.spec.ts` runs axe over both routes and the drawer; `performance/{ingest_bench.rs, log_bench.rs}` measure 20 messages per second sustained ingestion, apply latency for a 5 MB message with three attachments, and log paging at 100,000 messages per tenant. The oracle test asserts that the response body and the emitted bounce are byte-identical, and the elapsed time within the measured floor, across unknown recipient, revoked address, DMARC failure, sender-policy failure and rate limit. The cross-tenant lane asserts a local part from tenant A never resolves against tenant B, that a foreign address or message id returns `not_found`, and that `from_address` never leaves the log as more than its domain in any log line, span or metric label. Every lane records its FR and NFR ids in `cases.md`, and `requirements/cases.md` carries every requirement id declared in the ticket. Positive control: each gate is proved by breaking it — disable the signature check, the alignment rule, the sanitiser, the token check and the per-sender limit in turn, observe RED, restore, observe GREEN — and the evidence is stored under `testing/evidence/F072/`.
- Data access: the harness reaches the database only through the fixtures and the repositories under test; no test opens a connection or writes SQL of its own (decision section 2.1).
- Dependencies: T287 applied rows and surfaces; T286 gate; `testing/fixtures/inbound_email.rs`; the mock provider in `testing/harness/providers/inbound-email/`; F017 and F037 stubs.
- Feature flag: `F072_FEATURE` enabled explicitly by both commands; fixtures are isolated per worker by schema, tenant and address domain.

## TDD

- Failing test first: `testing/features/F072/e2e/inbound_email.spec.ts::forwarded_mail_becomes_row_with_attachment`, `::dmarc_failure_never_reaches_the_sheet`, `::reply_to_notification_appends_comment`, `::rejected_and_quarantined_entries_visible_in_log`; `testing/features/F072/api/oracle_tests.rs::refusal_body_identical_across_reasons`, `::refusal_timing_within_measured_floor`, `::local_part_from_other_tenant_does_not_resolve`, `::sender_address_redacted_to_domain_in_telemetry`; `testing/features/F072/accessibility/inbound_email.a11y.spec.ts::routes_have_no_serious_violations`, `::disposition_not_colour_only`; `testing/features/F072/performance/ingest_bench.rs::sustains_twenty_messages_per_second`, `::apply_p95_under_fifteen_seconds`; `testing/features/F072/performance/log_bench.rs::log_paging_p95_under_500ms`
- Targeted command: `cargo xtask test-feature F072`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/inbound_email.rs`; the `.eml` corpus above; mock provider signing in the three webhook formats; F017 scan stub with clean, quarantined and rejected outcomes; F037 transport stub recording bounces and `Reply-To` headers; fixed clock `2026-09-03T00:00:00Z` and UTC

## Exit criteria

- [ ] Every FR and NFR id in the ticket appears in `testing/features/F072/requirements/cases.md` and in at least one executing lane
- [ ] Corpus committed with a one-line description per message and no real personal data
- [ ] Positive controls recorded for the signature, alignment, sanitiser, token and rate gates
- [ ] Targeted and full modes both green; evidence under `testing/evidence/F072/`
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S144
- [ ] `finished_at` recorded
