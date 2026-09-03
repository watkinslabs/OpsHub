# F041 database cases

No PostgreSQL table exists for this feature; persistence is the file system (`work/**` front matter and `work/plan.md`), so this lane holds file-system persistence cases instead of migration cases. File: `testing/features/F041/database/fs_tests.rs`. Flag `F041_FEATURE`.

- `file_with_501_lines_reported` — FR-F041-12: `line.limit` at line 501 with message `501 lines; limit is 500`.
- `binary_file_skipped` — FR-F041-12: a 2,000-line file with a NUL byte at offset 100 produces no finding.
- `symlink_outside_root_reported_not_followed` — NFR-F041-02: symlink `work/tasks/link.md -> /etc/passwd` → `io.symlink_escape`; the target is never opened (checked with `strace -e openat`).
- `crlf_counts_lines_once` — FR-F041-12: 500 CRLF lines pass; 501 fail.
- `unreadable_file_continues_run` — NFR-F041-02: mode 000 file → `io.unreadable`, other findings still reported.
- `archived_timestamps_ordered` — FR-F041-11: `finished_at` earlier than `started_at` → `lifecycle.timestamp`.

Evidence: test log under `testing/evidence/F041/database/`.
