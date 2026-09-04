---
id: T258
type: task
status: planned
parent_epic: E006
parent_feature: F065
parent_story: S129
depends_on: [S129, T257]
owned_paths: [crates/domain/src/signup/**, services/api/src/signup/**, apps/web/src/features/signup/**, testing/features/F065/api/**, testing/features/F065/frontend/**, testing/features/F065/accessibility/**]
feature_flag: F065_FEATURE
branch: t258-verification-and-anti-abuse
started_at: null
finished_at: null
---

# T258 — Verification and anti-abuse

## Identity

- Parent story: `S129` public signup and verification
- Owner: platform
- Branch: `t258-verification-and-anti-abuse`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F065

## Objective

Implement the defences that make an unauthenticated door safe: rate-limit buckets, the bot check, the disposable-domain and MX rejection, peppered email hashing, constant-time token verification with capped attempts and capped resends, the single F037 mail path, and the public React pages that surface all of it without leaking who already uses OpsHub.

## Specification

- Owned paths: `crates/domain/src/signup/{risk.rs, bot_check.rs, mx.rs, mail.rs, disposable_domains.txt}`, `services/api/src/signup/handlers_public.rs` rejection path and the constant-time floor, `apps/web/src/features/signup/{SignupPage.tsx, SignupForm.tsx, TurnstileField.tsx, HoneypotField.tsx, VerifySentPage.tsx, SlugField.tsx, ExpiredTokenPage.tsx, InvitationForm.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `BotCheck::verify(bot_token, remote_ip) -> Verdict` with `TurnstileBotCheck` against the Cloudflare siteverify endpoint and `StaticBotCheck` in tests; `MxResolver::has_mx(domain)` with a 2-second timeout; `RiskAssessment::evaluate(bot, domain, rate) -> (Vec<RiskFlag>, MailDecision)`; `normalize_email` plus `SHA-256(pepper ‖ normalized)`.
- Output/behavior: buckets enforce 5 signups per hour per IP, 20 per hour per IPv4 `/24` or IPv6 `/48`, 3 per 24 hours per `email_hash`, 60 availability calls per minute per IP, and 10 token calls per hour per IP; availability and token breaches return `429 rate_limited` with `Retry-After` while signup breaches are absorbed into the standard `202` and counted in `signup_rejected_total{reason}`. The honeypot `company_website` must be empty and `elapsed_ms` must be 2,000–3,600,000. A listed disposable domain or a domain with no MX record is absorbed with `risk_flags` `disposable_domain` or `no_mx`; consumer domains are accepted and flagged `consumer_domain`. A Turnstile outage degrades to honeypot, timing, and rate checks with `botcheck_unavailable` instead of rejecting every caller. All mail is one call to the F037 `NotificationService` with category `system` and `dedupe_key` `signup:{request_id}:{kind}`, choosing the verification, existing-account, or invitation message; resends are capped at 3 and 60 seconds apart and reuse the same token row. Token comparison hashes the presented value and compares in constant time; the raw token, `bot_token`, and the address never reach logs, spans, or responses. The React pages debounce availability at 400 ms, keep the honeypot `aria-hidden` and out of the tab order, announce availability through a polite live region, and show one message for every unavailable-slug reason.
- Dependencies: T257 schema and route skeletons; F037 notification service; F038 rate-limit buckets; F004 secret source for the pepper and the Turnstile secret; F062 design tokens and form primitives.
- Feature flag: `F065_FEATURE` gates the public pages and the router mount; the disposable-domain list ships with the crate.

## TDD

- Failing test first: `testing/features/F065/api/anti_abuse_tests.rs::sixth_signup_from_one_ip_is_absorbed`, `::network_bucket_caps_twenty_per_hour`, `::third_signup_per_email_hash_is_absorbed`, `::honeypot_filled_sends_no_mail`, `::elapsed_under_two_seconds_rejected`, `::disposable_domain_absorbed_with_flag`, `::domain_without_mx_absorbed_with_flag`, `::turnstile_outage_degrades_not_rejects`, `::token_compare_is_constant_time`, `::fourth_resend_rejected`, `::resend_within_cooldown_rejected`, `::logs_never_contain_email_or_raw_token`; `testing/features/F065/frontend/SignupForm.test.tsx::honeypot_is_hidden_and_untabbable`, `::availability_message_is_identical_for_every_reason`; `testing/features/F065/accessibility/signup.a11y.spec.ts::public_pages_have_no_serious_violations`
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/signup.rs` `StaticBotCheck` verdict map, `StaticMxResolver` domain map, in-memory `NotificationSender` recording category, `dedupe_key`, and rendered link, per-test IP range, fixed pepper and clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every rejection path proven to return the FR-F065-02 response and to send at most the one permitted mail
- [ ] Owned-path check passes; axe reports zero serious or critical violations on the three public pages
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S129
- [ ] `finished_at` recorded
