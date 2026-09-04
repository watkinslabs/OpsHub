# F064 requirements cases

Feature: Billing and subscriptions. Flag `F064_FEATURE`. Every case maps to a ticket requirement ID. The payment provider is mocked in every row.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F064-REQ-001` | FR-F064-01 | api | subscription read returns plan, status, periods, trial, schedule, dunning, seats, allowances, payment-method summary; tenant with no row → synthetic free at `version: 0` |
| `F064-REQ-002` | FR-F064-02 | api | `plan` outside the F002 set of `free`, `team`, `enterprise` → 400 with `field_errors.plan`; `preview: true` writes nothing; `enterprise` without a payment method → 409 |
| `F064-REQ-003` | FR-F064-03 | api | mid-period upgrade credit, charge, and net match provider line items to the cent; mismatch → 502 and no local write |
| `F064-REQ-004` | FR-F064-04 | api, e2e | downgrade stores `scheduled_plan` and applies within 5 minutes of period end; `apply: immediate` issues a credit note |
| `F064-REQ-005` | FR-F064-05 | api | plan change upserts F048 records with `source: plan` for the plan module list; a `manual` row is left untouched; no billing-owned entitlement table exists |
| `F064-REQ-006` | FR-F064-06 | api | every provider call crosses the `PaymentProvider` port; a grep gate proves no provider type outside `adapters/stripe.rs` |
| `F064-REQ-007` | FR-F064-07 | api | portal session returns a 15-minute URL; sixth session in an hour → 429; the URL appears in no log and no table |
| `F064-REQ-008` | FR-F064-08 | api | forged signature or skew above 300 s → 400, no state change, `billing.webhook-rejected` audited; unknown provider → 404 |
| `F064-REQ-009` | FR-F064-09 | api, database | redelivered `provider_event_id` → 200 `duplicate` and nothing applied; unhandled type and unknown customer → `ignored` |
| `F064-REQ-010` | FR-F064-10 | api | `invoice.finalized` → `invoice.issued.v1`; `invoice.paid` clears dunning; `invoice.payment_failed` → `invoice.payment-failed.v1`; provider state wins on reconcile |
| `F064-REQ-011` | FR-F064-11 | api, performance | only `seats`, `storage_gb`, `automation_runs` are metered; daily samples at 00:05 UTC, hourly automation deltas; no other counter is written |
| `F064-REQ-012` | FR-F064-12 | api, database | corrections append an `adjustment` with reason and target; `UPDATE`/`DELETE` raise; usage query folds adjustments; overage reported, never blocking |
| `F064-REQ-013` | FR-F064-13 | api, e2e | day 0 `past_due`, day 7 `restricted` with only plan entitlements suspended, day 14 `suspended` read-only with export, day 30 `canceled` to free; a notification at every stage |
| `F064-REQ-014` | FR-F064-14 | api | trial notices at 7, 3, 1 days; expiry converts with a payment method and falls back to free without one; cancellation keeps access to period end |
| `F064-REQ-015` | FR-F064-15 | api, frontend | invoices page newest first with filters and per-line metric and quantity; `hosted_url` fetched on read; foreign tenant id in body → 400 |
| `F064-NFR-001` | NFR-F064-01 | performance | subscription read p95 < 300 ms; invoices p95 < 500 ms; 13-month usage query < 800 ms; meter of 10,000 tenants < 10 min; webhook p95 < 2 s |
| `F064-NFR-002` | NFR-F064-02 | api | no card data stored beyond brand, last4, expiry; signing secrets rotate in pairs; portal URLs and raw bodies absent from logs and exports; cross-tenant → `not_found` |
| `F064-NFR-003` | NFR-F064-03 | accessibility | axe serious and critical = 0 on all three billing routes and both dialogs; status by text plus icon; dunning banner announced with stage, consequence, and date |
| `F064-NFR-004` | NFR-F064-04 | api, database | replay guard by unique constraint; meter idempotent by source ref; failed webhook retried 5 times then dead-lettered; the four metric families exported |

| `F064-REQ-016` | FR-F064-16 | api, database | a platform operator mints a batch of 50 codes and receives each plaintext exactly once; only `code_hash` is stored and no plaintext appears in the row, log, audit or event; a `billing-admin` who is not an operator gets 403 |
| `F064-REQ-017` | FR-F064-17 | api | redemption succeeds once and returns the new balance; a second attempt returns 409 `already_redeemed`; two concurrent redemptions of one code yield exactly one success; `invalid_code`, `expired` and `not_applicable` are distinguished; the 6th attempt in an hour is rate limited |
| `F064-REQ-018` | FR-F064-18 | api, e2e | balance covering an invoice marks it `paid_by_credit` with no provider charge; a partial balance reduces the amount due and carries the remainder; unused credit expires with a ledger entry and a 14-day warning; a tenant whose credit covers a failed payment leaves `past_due` and never enters dunning |

Evidence: command, fixture seed, provider mock log, result, and artifact path recorded under `testing/evidence/F064/`.
