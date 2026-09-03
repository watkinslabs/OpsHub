# F037 requirements cases

Feature: notification service. Flag `F037_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F037-REQ-001` | FR-F037-01 | api, database | `NotificationService::create` inside the producer transaction writes the notification and its delivery rows; a 201-char title or a 2,001-char body → `InvalidRequest`; a rolled-back producer transaction leaves no rows |
| `F037-REQ-002` | FR-F037-02 | api | each of the eight categories is accepted; `promo` → `NotificationError::InvalidCategory` and nothing is written |
| `F037-REQ-003` | FR-F037-03 | api | routing resolves user preferences, then tenant defaults, then built-in defaults; with no rows anywhere, `approval`, `assignment`, and `mention` fan out to email while the rest are in-app only |
| `F037-REQ-004` | FR-F037-04 | api, performance | `GET /notifications` pages newest-first by cursor, honours `limit` 1–100 and the `unread` and `category` filters, and never returns another user's rows |
| `F037-REQ-005` | FR-F037-05 | api | `POST /{id}/read` sets `read_at` and returns 200 on repeat; `read-all` with `before` marks only older unread rows and leaves newer ones untouched |
| `F037-REQ-006` | FR-F037-06 | api, e2e | `deliver_email` renders the category template and sends through the Mailpit adapter → `status: sent` with `provider_message_id`; a 5xx from the adapter retries on the schedule and records the error |
| `F037-REQ-007` | FR-F037-07 | api, database | `POST /push-subscriptions` stores one row per endpoint (duplicate endpoint updates in place); `DELETE` removes it; a push to a `410 Gone` endpoint prunes the subscription |
| `F037-REQ-008` | FR-F037-08 | api, frontend | `GET /notification-preferences` returns the effective per-category channel matrix plus digest cadence, `send_at_local`, timezone, and quiet hours; `PUT` persists a partial update without clearing untouched categories |
| `F037-REQ-009` | FR-F037-09 | api | a notification created inside the recipient's quiet hours queues email and push with `next_attempt_at` at the window end in the recipient's timezone; in-app is unaffected; a DST boundary resolves to the documented instant |
| `F037-REQ-010` | FR-F037-10 | api, e2e | with `daily` cadence, non-`approval` and non-`system` emails are stored `digested` and `send_digest` sends exactly one summary at `send_at_local`; `approval` still sends immediately |
| `F037-REQ-011` | FR-F037-11 | api | `GET /notification-deliveries/{id}` returns channel, status, attempts, `next_attempt_at`, `sent_at`, `provider_message_id`, error, and reason to the recipient; another user's delivery → 404 `not_found` |
| `F037-REQ-012` | FR-F037-12 | api, e2e | replaying one `source_event_id` creates one notification; `deliver_email` and `deliver_push` skip rows not in `queued`; a re-run of `send_digest` for the same window sends nothing further |
| `F037-REQ-013` | FR-F037-13 | frontend, e2e | the bell badge polls every 30 s, the drawer lists items with category icons and relative times, opening marks visible items read, and `Mark all read` clears the badge without a reload |
| `F037-REQ-014` | FR-F037-14 | api, database | preference and subscription mutations require `Idempotency-Key`, write `audit_events`, and publish no domain event; a replayed key returns the first result |
| `F037-NFR-001` | NFR-F037-01 | performance | 10,000 notifications per user: list and unread count p95 < 500 ms; create plus routing p95 < 50 ms inside the producer transaction; email delivery meets the ticket's queue budget |
| `F037-NFR-002` | NFR-F037-02 | api, accessibility | the router stores only the text it is given and never re-reads cells; push payloads carry title, body, and link only, with no cell values or secrets |
| `F037-NFR-003` | NFR-F037-03 | accessibility | bell, drawer, and settings page report zero serious axe violations; the badge count is announced through `aria-label`; the drawer is a labelled, keyboard-reachable region and the channel matrix is a labelled grid |
| `F037-NFR-004` | NFR-F037-04 | performance, e2e | deliveries dead-letter after the retry schedule and stay `failed`; `notifications_created_total{category}`, `notification_deliveries_total{channel,status}`, and the delivery duration histogram are emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F037/`.
