# F041 performance cases

File: `testing/features/F041/performance/scan_bench.rs`. Runs on the generated tree from `testing/harness/repo.rs::wide_tree(20_000)` (fixed seed, 200 MiB) plus 500 valid work files. Flag `F041_FEATURE`.

- `validate_work_500_items_under_2s` — NFR-F041-01: 500 items, 3 runs, max wall clock < 2,000 ms.
- `scan_20k_files_under_2s` — NFR-F041-01, FR-F041-12: line-limit scan over 20,000 files < 2,000 ms; resident memory < 64 MiB (`/proc/self/status` VmHWM).
- `each_file_read_once` — NFR-F041-01: `strace -c` shows `openat` count ≤ files + 16 for `validate-tickets`.
- `cycle_detection_linear` — FR-F041-06: a 5,000-node dependency chain validates in < 500 ms.

Evidence: timing tables under `testing/evidence/F041/performance/`.
