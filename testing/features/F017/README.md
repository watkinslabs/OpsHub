# F017 — Files and proofing harness

Feature-gated tests for `F017`. Keep test code in this directory.

- Gate: `F017_FEATURE`
- Targeted: `cargo xtask test-feature F017`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/files.rs` (tenant A with sheet, row "Kickoff", editor `eli`, viewer `vic`, reviewers `rae` and `ron`, outsider `oz`; tenant B foreign user; sample `spec.pdf`, `logo.png`, `eicar.txt`, `big-250mb.bin`; seeded row with 12 files across scan states and one file with 3 versions and an open proof)
- Services: MinIO bucket prefix per worker from `testing/harness/minio.rs`; `ClamScanner` stub keyed by EICAR content; embedded JetStream from `testing/harness/nats.rs`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
