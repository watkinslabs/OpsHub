# F065 requirements cases

Feature: Self-serve signup and trials. Flag `F065_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F065-REQ-001` | FR-F065-01 | api | valid submission → `202 { status: "pending_verification", expires_in_seconds: 86400 }`; email over 254 chars, company name of 1 char, slug `ab` → same `202`, no row |
| `F065-REQ-002` | FR-F065-02 | api, e2e | new address, existing user's address, taken slug, suppressed request → identical status, headers, body bytes, latency band; only the mail differs |
| `F065-REQ-003` | FR-F065-03 | api, performance | 6th signup per IP per hour, 21st per `/24`, 4th per `email_hash` absorbed; 61st availability call and 11th token call → `429` with `Retry-After` |
| `F065-REQ-004` | FR-F065-04 | api | bad `bot_token`, filled `company_website`, `elapsed_ms` 800 → risk flag recorded, no mail, standard `202`; Turnstile outage degrades to the other two checks |
| `F065-REQ-005` | FR-F065-05 | api | listed disposable domain → `disposable_domain`; domain with no MX → `no_mx`; `gmail.com` accepted with `consumer_domain`; `email_hash` stable across dots and `+tag` |
| `F065-REQ-006` | FR-F065-06 | api, frontend | availability answers one slug only; taken, reserved, and soft-reserved all return `available: false` with no distinguishing field; no email parameter accepted |
| `F065-REQ-007` | FR-F065-07 | api, database | first claimant holds `orbit` through the partial unique index; second stored with null slug and `slug_taken`; F002 `SlugTaken` at completion → `409` without consuming the token |
| `F065-REQ-008` | FR-F065-08 | api, database | only `SHA-256` stored; constant-time compare; 24-hour expiry; 6th attempt rejected; expired, consumed, and unknown tokens all `410 gone`; first read publishes `signup.verified.v1` once |
| `F065-REQ-009` | FR-F065-09 | api | every mail is one F037 `create` with category `system` and `dedupe_key` `signup:{request_id}:{kind}`; 4th resend and a resend within 60 s rejected; no SMTP client in the module |
| `F065-REQ-010` | FR-F065-10 | api, e2e | completion transaction consumes the token, calls F002 `create_tenant`, grants entitlements, starts the trial subscription, publishes `tenant.provisioned.v1`, returns the session cookie |
| `F065-REQ-011` | FR-F065-11 | api | 14 days, 10 users, 5 GB; `dynamic-views`, `workapps`, `calendar-app`, `pivots` at `trial`; the other six at `none`; `tenants.plan` is `free` |
| `F065-REQ-012` | FR-F065-12 | api, e2e | at `trial_ends_at` trial modules read-only and sheets writable; reminders on grace days 0, 3, 6; grace end suspends through F002 with data intact |
| `F065-REQ-013` | FR-F065-13 | api, e2e | `subscription.updated.v1` with `status: active` → entitlements `active`, `trial_ends_at` cleared, suspension lifted, every row, file, and user unchanged |
| `F065-REQ-014` | FR-F065-14 | api, database | pending past expiry → `abandoned` with `signup.abandoned.v1`; PII null at 7 days leaving `email_hash`; row and tokens deleted at 30 days |
| `F065-REQ-015` | FR-F065-15 | api | operator invitation skips bot and domain checks, pins the slug in `reserved_slugs`, mails through F037, returns `201`; anonymous and `tenant-admin` denied |
| `F065-REQ-016` | FR-F065-16 | frontend, e2e | public pages render without a session, availability debounced 400 ms, one message per unavailable reason, redirect to the workspace with the cookie set |
| `F065-NFR-001` | NFR-F065-01 | performance | signup 250–600 ms p95, availability < 150 ms, token read < 200 ms, completion < 3 s, sweep of 100,000 rows < 5 min |
| `F065-NFR-002` | NFR-F065-02 | api | no existence oracle on any route; hashes only; peppered `email_hash`; logs free of address, raw token, and `bot_token`; system operator context never issued as a session |
| `F065-NFR-003` | NFR-F065-03 | accessibility | axe serious and critical = 0 at 320 px and 1,440 px; availability announced politely; honeypot untabbable; errors tied by `aria-describedby` |
| `F065-NFR-004` | NFR-F065-04 | api, performance | replayed completion → `410 consumed` and one tenant; jobs idempotent and resumable; the six signup and trial metrics exported |
| `F065-NFR-005` | NFR-F065-05 | performance | 10,000 attempts from one `/24` in 10 minutes → at most 20 rows and 20 mails per hour, unchanged p95 on authenticated routes, no attacker-controlled mail text |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F065/`.
