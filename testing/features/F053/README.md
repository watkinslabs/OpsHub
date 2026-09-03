# F053 — DataMesh harness

Feature-gated tests for `F053`. Keep test code in this directory.

- Gate: `F053_FEATURE`
- Targeted: `cargo xtask test-feature F053`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixture: `testing/fixtures/datamesh.rs` (tenant A data-admin/editor/viewer, tenant B without entitlement, `datamesh` entitlement with `max_mappings 5` and `max_rows_per_sync 50000`, `Vendors master` with 1,000 rows, `Purchase requests` with 1,200 rows: 840 matching, 12 unmatched, 2 ambiguous; one mapping with a completed run and two open conflicts).
- External services: JetStream subject `datamesh.sync`; recorded `row.updated.v1` payloads for the change listener; two-worker compose profile for exactly-once tests.
