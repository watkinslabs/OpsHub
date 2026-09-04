---
id: T234
type: task
status: planned
parent_epic: E008
parent_feature: F059
parent_story: S117
depends_on: [T233]
owned_paths: [crates/domain/src/publishing/**, crates/persistence/src/publishing/**, services/api/src/publishing/**, testing/features/F059/api/**, testing/features/F059/requirements/**]
feature_flag: F059_FEATURE
branch: t234-scoped-access-tokens
started_at: null
finished_at: null
---

# T234 — Scoped access tokens

## Identity

- Parent story: `S117` Published artifacts
- Owner: platform
- Branch: `t234-scoped-access-tokens`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F059

## Objective

Implement hashed, scoped, expiring publication tokens with rotation, revocation, and the public render route that serves snapshots with freshness and error states.

## Specification

- Owned paths: `crates/domain/src/publishing/{token.rs, resolve.rs}`, `crates/persistence/src/publishing/token_repository.rs`, `services/api/src/publishing/{handlers_token.rs, handlers_public.rs}`
- Contract/input: `issue_token(publication) -> (plaintext, PublicationToken)` with 32 random bytes, base64url plaintext, SHA-256 `token_hash`, `scope { tenant_id, publication_id, target, read_only: true }`; `POST /api/v1/publications/{id}/rotate-token`; `GET /public/publications/{token}`; `resolve_token(plaintext) -> Result<ResolvedScope, PublishError>`.
- Output/behavior: plaintext is returned exactly once in `TokenIssuedResponse`; rotation inserts a new token, sets `superseded_at = now + 10 min` on the previous one, and publishes `publication.updated.v1` with `changed_fields: ["token"]`; `resolve_token` rejects unknown, expired, revoked, and superseded tokens with `404 not_found` and records `publication_token_rejected_total{reason}`; public render returns `PublicRender { target_kind, title, generated_at, stale, payload }` from the snapshot with the `X-OpsHub-Stale` header, `Cache-Control: max-age=30`, and the `error` state with `reason` when the publication is in `error`; revoke rejects within 5 s because resolution hits the database on every request with a 5 s negative cache.
- Dependencies: T233 schema, service, and snapshots; `crates/auth` hashing helpers; F004 metrics registry.
- Feature flag: `F059_FEATURE`

## TDD

- Failing test first: `testing/features/F059/api/token_tests.rs::token_stored_only_as_hash`, `::token_not_returned_after_creation`, `::rotate_token_grace_then_404`, `::revoked_token_404_within_5s`, `::expired_token_404`, `::public_render_returns_generated_at_and_stale_header`, `::public_render_stale_after_refresh_failure`, `::public_render_error_state_when_target_deleted`
- Targeted command: `cargo xtask test-feature F059`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixed token RNG seed; fixed clock advanced through 10-minute grace and 30-day expiry

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Public route mounted outside session middleware; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S117
- [ ] `finished_at` recorded
