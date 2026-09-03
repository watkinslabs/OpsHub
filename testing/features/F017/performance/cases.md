# F017 performance cases

File: `testing/features/F017/performance/{upload_bench.rs,scan_bench.rs,list_bench.rs}`. Runs against MinIO, the ClamAV stub with real streaming, and a row seeded with 5,000 files with fixed seed. Flag `F017_FEATURE`.

- `upload_start_and_complete_p95` — NFR-F017-01: 200 upload start plus complete pairs for 1 MB objects; each call p95 < 800 ms; job acknowledgement < 2 s.
- `scan_250mb_within_120s` — NFR-F017-01: `scan_file` on `big-250mb.bin` streams to the scanner and hashes in one pass; completes under 120 s; memory stays under 64 MB.
- `preview_pdf_within_30s` — NFR-F017-01: 50-page PDF first-page render p95 < 30 s.
- `file_list_5k_target_p95` — NFR-F017-01: 200 sequential `GET /api/v1/row/{id}/files?limit=100` requests; p95 < 500 ms warm using the target index.
- `presign_throughput` — NFR-F017-02: 1,000 download redirects; p95 < 200 ms; every URL expires within 15 minutes.

Evidence: criterion/k6 summaries under `testing/evidence/F017/performance/`.
