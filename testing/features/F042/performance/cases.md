# F042 performance cases

File: `testing/features/F042/performance/audit_bench.rs`. Scratch repositories generated with fixed seeds: 200 staged files totalling 20 MiB, and a 1,000-commit (and a 6,000-commit) linear history. Flag `F042_FEATURE`.

- `audit_staged_200_files_under_1s` — NFR-F042-01: 3 runs, max wall clock < 1,000 ms.
- `audit_range_1000_commits_under_2s` — NFR-F042-01: < 2,000 ms; 6,000-commit batch run finishes with an exact finding count (FR-F042-13).
- `self_test_under_500ms` — NFR-F042-01.
- `windowed_scan_memory_bounded` — FR-F042-13: 64 MiB staged blob scanned with resident memory < 32 MiB above baseline.

Evidence: timing tables under `testing/evidence/F042/performance/`.
