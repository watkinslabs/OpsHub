# F073 — Announcements and in-app help harness

Feature-gated tests for `F073`. Keep test code in this directory.

- Gate: `F073_FEATURE`
- Targeted: `cargo xtask test-feature F073`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/announcements.rs` (tenant A on `enterprise` holding the `assets` entitlement, tenant B on `free`; a `platform-operator` principal, a `tenant-admin` and a member in each tenant; six announcements spanning `info`, `change` and `action_required` and the four target kinds `plan`, `entitlement`, `role` and `tenant`; one superseded pair; one announcement already dismissed by the tenant A member; a help bundle of eight `en-US` articles with four `de-DE` translations, six context mappings and one withdrawn slug; F048 entitlement and F049 locale stubs; fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seeds and a fixed bundle signing key).
- Corpora: `api/fixtures/injection/` holds the authored-content attack strings the `SafeDoc` renderer must reduce to text, and `api/fixtures/editorial/` holds body pairs on either side of the 5% token-distance line that separates an editorial revision from a material change.
- Bundles: `api/fixtures/bundles/` holds one correctly signed help bundle and one with a broken signature, so the import job's refusal path is exercised without a network.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Privacy control: the frontend lane asserts that the what's-new panel and the help drawer contact no origin other than the OpsHub API, which is how FR-F073-14 is verified rather than merely stated.
