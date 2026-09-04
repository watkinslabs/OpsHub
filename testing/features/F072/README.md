# F072 — Inbound email harness

Feature-gated tests for `F072`. Keep test code in this directory.

- Gate: `F072_FEATURE`
- Targeted: `cargo xtask test-feature F072`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/inbound_email.rs` (tenants A and B; sheet `Vendor intake` with text, long-text, date, contact and file columns and a primary column; a sheet editor and a viewer; one active address per sender policy and one per auth policy; a revoked address and one inside its 7-day rotation grace; a reply token bound to row 1482; fixed clock `2026-09-03T00:00:00Z` in UTC; a fixed CSPRNG stream so local parts and reply tokens are reproducible; fixed current and previous webhook secrets per provider).
- Mock provider: `testing/harness/providers/inbound-email/` signs and posts the `.eml` corpus in the Postmark, SendGrid and Mailgun webhook shapes with programmable `spf`, `dkim`, `dmarc` and alignment results, a replay switch, and a clock-skew switch for signature tests.
- Adversarial corpus: `e2e/corpus/` holds one `.eml` per abuse case — spoofed sender, unaligned `dmarc = none`, `temperror`, oversize message, auto-reply, mailing list, `X-Loop`, 26 `Received` headers, HTML-only body with a script tag and a remote image, a body beginning with `=`, a five-deep forward, a truncated MIME tree, eleven attachments, a valid plus-token reply, a forged `In-Reply-To`, and a token on its 21st use — each with a one-line description and no real personal data.
- Stubs: F017 upload and scan stub returning `clean`, `quarantined` or a MIME/size rejection on demand; F037 transport stub recording every bounce, its suppression decision and the `Reply-To` header of row notifications; F027 retention policy stub for `inbound_raw_message`.
- Isolation: one schema, one tenant, one mock provider port and one inbound address domain per test worker, so rate-limit windows in one test never affect another.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
