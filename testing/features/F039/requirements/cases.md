# F039 requirements cases

Feature: AI formulas/queries. Flag `F039_FEATURE` with the F048 `ai-assist` entitlement seeded `active`. Every case maps to a ticket requirement ID. No case may reach a live model: `AI_PROVIDER=recorded` and the socket guard are active in every lane.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F039-REQ-001` | FR-F039-01 | api | formula request → `ai_requests` row, pending `ai_proposals` row, `ai-proposal.created.v1`, response with formula, explanation, referenced fields, confidence, limitations, `expires_at` |
| `F039-REQ-002` | FR-F039-02 | api | preview built from F035 evaluate over 5 readable rows; error row keeps its `error_code` and caps confidence at `0.5`; two parse failures → `502 unavailable` `unusable_output` |
| `F039-REQ-003` | FR-F039-03 | api | question → compiled `ReportDefinition`, `plan_hash`, `sources`, `excluded_sources` with reason, `estimated_rows`; no row data read; `sensitive` column → `requires_preview: true` |
| `F039-REQ-004` | FR-F039-04 | api | plan failing the F021 validator regenerates once with `field_errors`; second failure → `502 unavailable` `uncompilable_plan` with the rejected plan stored |
| `F039-REQ-005` | FR-F039-05 | api | `GET /ai/queries/{id}` returns plan and `last_execution` to the requester; other actor → `403 denied`; foreign tenant → `404 not_found` |
| `F039-REQ-006` | FR-F039-06 | api, e2e | execute runs the plan under the caller's permissions, returns rows plus `meta`, publishes `ai-query.executed.v1`; wrong `plan_hash` → `409 conflict` |
| `F039-REQ-007` | FR-F039-07 | api | scope resolved by one batched `authz/check`; envelope holds ≤ 20 sheets, ≤ 3 samples per column, ≤ 200 samples, and no unreadable sheet, column, or row value |
| `F039-REQ-008` | FR-F039-08 | api | strict profile removes email, phone, card values and `sensitive` columns, writes `<redacted:kind>`, stores only `envelope_hash` |
| `F039-REQ-009` | FR-F039-09 | api | every model call goes through `AiProvider` with a budget; a grep gate proves no model HTTP client exists outside the adapters module |
| `F039-REQ-010` | FR-F039-10 | api | timeout/overload → `unavailable`; rate limit → `429` with `Retry-After`; refusal → `422 invalid`; malformed output repairs once; 5 failures open the breaker for 60 s |
| `F039-REQ-011` | FR-F039-11 | api, e2e | apply writes through F035 or F021 with apply-time role check, `Idempotency-Key`, and `If-Match`; stale version → `409 conflict` with `current_version` |
| `F039-REQ-012` | FR-F039-12 | api, frontend | reject stores the reason and publishes `ai-proposal.rejected.v1`; expired, applied, or rejected proposal → `409 conflict`; expiry job runs every 15 minutes |
| `F039-REQ-013` | FR-F039-13 | api, frontend | proposal stores `baseline`, `proposed`, ordered `diff`; read recomputes the diff and sets `stale` when the baseline version moved |
| `F039-REQ-014` | FR-F039-14 | api, frontend | tenant-admin patches `ai-settings` with `If-Match`; `enabled: false` → every route `403 denied` `ai_disabled`; non-admin → `403 denied` |
| `F039-REQ-015` | FR-F039-15 | api, database | usage metered per `(tenant, day, actor, kind)`; daily or monthly limit → `429 rate_limited` before egress; missing entitlement → `403 denied` `not_entitled` |
| `F039-REQ-016` | FR-F039-16 | frontend, e2e | both panels render prompt, generating with cancel, proposal card, diff, preview, apply/reject/regenerate, and the loading, empty, error, denied, disabled, not-entitled, rate-limited, stale, expired states |
| `F039-NFR-001` | NFR-F039-01 | performance | scope for 20 sheets < 300 ms p95; generate/compile < 6 s p95 excluding provider; apply < 800 ms p95; query read < 300 ms p95 |
| `F039-NFR-002` | NFR-F039-02 | api, database | no prompt text in logs, events, audit, or telemetry; envelope carries `tenant_hash` only; retention purge clears request text; cross-tenant IDs → `not_found` |
| `F039-NFR-003` | NFR-F039-03 | accessibility | axe serious/critical = 0 on panels, diff, settings; diff uses `ins`/`del` and text labels; live-region announcements; keyboard apply and focus trap |
| `F039-NFR-004` | NFR-F039-04 | api | one repair retry, no retry on refusal, breaker open and close, idempotent expiry job, and the five named metrics emitted with no prompt content in spans |
| `F039-NFR-005` | NFR-F039-05 | evaluation | offline suites with the socket guard: leakage 0, grounding 0, refusal ≥ 0.98 of 40, formula ≥ 0.85 of 120, plan ≥ 0.95 of 80; missing cassette fails the run |

Evidence: command, fixture seed, cassette set, result, and artifact path recorded under `testing/evidence/F039/`.
