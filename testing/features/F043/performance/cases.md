# F043 performance cases

File: `testing/features/F043/performance/{lane_bench.rs,collect_bench.rs}`. Scratch repository with a 50 MiB checkout and 100 pre-generated lane files. Flag `F043_FEATURE`.

- `claim_under_5s_with_100_lanes` — NFR-F043-01: including `git worktree add`, max of 3 runs < 5,000 ms.
- `allocate_under_100ms` — NFR-F043-01: `allocate-target` and `allocate-fixture` each < 100 ms.
- `collect_500mb_under_64mb_resident` — NFR-F043-01, FR-F043-10: 500 MiB of generated artifacts collected with VmHWM < 64 MiB above baseline and correct hashes.
- `slot_acquire_under_contention` — FR-F043-05: 20 concurrent claims complete in < 10 s with 20 distinct slots.

Evidence: timing tables under `testing/evidence/F043/performance/`.
