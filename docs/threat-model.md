# Threat model

Required by `docs/product-capability-spec.md` Phase 0 before implementation. It is written against
the architecture that actually exists in the decisions and the contract catalog, not a generic
checklist, and every mitigation names the feature that owns it so a gap is a ticket rather than a
worry.

## 1. What we are protecting

| Asset | Why it matters | Where it lives |
|---|---|---|
| Tenant work records | The customer's operational data; the product's reason to exist | `sheets`, `rows`, `cells` and their children |
| Identity and session material | Compromise is total for that user | `sessions`, `refresh_tokens`, `api_tokens`, MFA factors |
| Third-party credentials | Compromise reaches *other* systems, not just ours | `oauth_tokens`, Entra client secrets, connector credentials |
| Tokens that bypass login | Anyone holding one is an actor | share links, publication tokens, update-request links, MCP tokens, signup tokens |
| The audit log | The record of what happened; worthless if forgeable | `audit_events`, partitioned and append-only |
| Cross-tenant isolation | One failure here is an unrecoverable trust event | every table's `tenant_id` predicate |
| Billing state | Money, and the entitlements it drives | `subscriptions`, `invoices`, `credit_ledger` |

## 2. Trust boundaries

1. **Internet → public routes.** `/public/**` and `/embed/**` have no session. The only authority is
   a token that carries its own scope. F014, F036, F059, F061, F065.
2. **Internet → authenticated API.** `/api/v1/**` behind `ActorContext` from F038, permissions from
   F003 and the model in `docs/authorization-model.md`.
3. **Assistant → MCP.** A model-driven caller with a scoped token. F047.
4. **OpsHub → third parties.** Outbound to Graph, Slack, Jira, Salesforce, payment provider. F029,
   F030, F063, F064.
5. **Third parties → OpsHub.** Inbound webhooks and SAML assertions we did not initiate. F026, F028,
   F064.
6. **Tenant → tenant.** The boundary with no user-visible surface and the highest cost of failure.
7. **Service → database.** Every query passes through `crates/persistence`; the tenant predicate is
   applied by the base contract, not by callers. F068.

## 3. Threats and what answers them

### 3.1 Spoofing

- **Forged SAML assertion or ID token.** Signature verified against the connection's cached JWKS or
  certificate, `iss`/`aud` checked, assertion IDs stored to refuse replay, clock skew bounded.
  F026, F063.
- **Stolen share, publication or update-request link.** Tokens are 32 CSPRNG bytes stored only as
  SHA-256, compared in constant time, expiring within 30 days, revocable, rate limited, and scoped
  to one target. A leaked link is bounded and killable, never a session. F036, F059, F061.
- **Webhook impersonation.** HMAC over timestamp and raw body, 300-second skew, two-secret rotation,
  and a unique delivery id inserted in the same transaction as the effect. F028, F064.
- **Session fixation and refresh theft.** Refresh rotation with reuse detection; a replayed refresh
  invalidates the family. F038.

### 3.2 Tampering

- **Client-side validation bypass.** Every typed-column rule is enforced server-side; the client
  cannot submit a value the column rejects. F007, F008.
- **Cursor or filter forgery.** List cursors are signed and carry tenant, table, filter hash and
  expiry, so a cursor cannot be replayed against another tenant, filter or table. F028, F068.
- **Audit forgery.** `audit_events` is append-only and partitioned; no route updates or deletes it,
  and retention is longer than any actor's ability to change it. F003, F027.
- **Argument swap after approval.** An MCP or AI mutation is approved against a hash of its
  arguments; changing them invalidates the approval. F040, F047.

### 3.3 Repudiation

- Every mutation writes an audit row with actor, correlation id and a field-level diff, and external
  actors are recorded by their token identity and email — an update-request response is attributable
  even though the responder has no account. F003, F061.
- A publication read is logged with token id and referrer origin, so "who saw this" is answerable.
  F059.

### 3.4 Information disclosure

- **The dominant risk: reading another tenant's data.** Mitigated structurally rather than by
  discipline — the repository base contract applies the tenant predicate and a runtime conformance
  suite runs against every registered repository, because types cannot prove the absence of a leak
  in a live database. Cross-tenant ids return `not_found`, never `denied`, so existence does not
  leak. F068, F003.
- **Over-broad reads through a scoped surface.** A dynamic view, MCP resource or published page
  renders as the *publisher's or caller's* permissions at request time and never widens them; if
  that access is lost the surface shows an error state rather than stale data. F050, F047, F059.
- **Search and AI as side channels.** Search prefilters by ACL rows rather than filtering after the
  fact; AI retrieval is permission-filtered before the model sees anything, and an insight whose
  evidence the reader cannot see is omitted whole rather than redacted. F010, F039, F040.
- **Secret leakage.** Provider credentials are envelope-encrypted per tenant, never returned by any
  DTO, never logged, never in an audit diff, and covered by redaction tests. Recipient addresses
  appear in logs only as their domain. F029, F063, F027.
- **Enumeration.** Signup answers identically for a taken and a free address, with a latency floor;
  availability accepts no email. F065.

### 3.5 Denial of service

- Per-tenant and per-token rate limits with `Retry-After`; per-connection concurrency caps on
  outbound calls; a circuit breaker after consecutive provider failures. F038, F029, F063.
- Bounded work: 5,000 cells per bulk edit, 366-day windows, 500 mapped groups, 50 filter leaves,
  page limits everywhere. An expensive request is refused, not queued forever.
- Async paths dead-letter after a bounded retry schedule and are replayable, so a poison message
  stops one job rather than the worker. F004.
- The scale target is proven rather than assumed, including pool saturation, queue depth and
  replication lag under load. F067.

### 3.6 Elevation of privilege

- **Scoped token escalation.** A token's authority is the intersection of the minting user's
  permissions and the token's stored scope; a role never widens it. `docs/authorization-model.md`
  section 3.3.
- **Purge as a weapon.** No role grants `purge`; it runs only through the audited governance job,
  and a legal hold refuses it. F027.
- **Entitlement bypass.** `RequireModule` is evaluated server-side; a module the tenant is not
  entitled to returns `denied` regardless of what the client renders. F048.
- **Approval bypass.** A mutating MCP tool or AI action cannot write on first call; the human
  approval is a separate authenticated request by a principal who owns it. F040, F047.

## 4. Residual risks accepted

| Risk | Why accepted | Compensating control |
|---|---|---|
| A tenant-admin can grant themselves access to any resource in their tenant | It is their tenant; removing this would make administration impossible | Every grant is audited and appears in access reviews |
| Polymorphic references carry no database foreign key in five places | Splitting the column would change the request shape | Kind check, resolution inside the writing transaction, reverse-dependency query on delete |
| A published page's viewer is anonymous | That is the feature | Token scope, expiry, revocation within 5 seconds, per-token rate limit, access log |
| The MUI and TanStack supply chain | Any dependency is a supply chain | Pinned versions, no runtime CDN, CSP, and the UI performs no network call of its own |

## 5. Verification

The claims above are tests, not prose. Every feature harness carries a permission-negative and
tenant-isolation lane; F027 owns the redaction suite; F040 owns the prompt-injection corpus; F065
owns the enumeration suite with a positive control; F067 proves the DoS bounds under load. A
mitigation with no test is a finding at review, not a mitigation.
