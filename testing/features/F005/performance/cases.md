# F005 performance cases

File: `testing/features/F005/performance/tree_bench.rs`. Runs against a seeded workspace with 2,000 folders (depth up to 10, fixed seed) and 500 members. Flag `F005_FEATURE`.

- `tree_2000_folders_p95` — NFR-F005-01: 200 sequential `GET /api/v1/workspaces/{id}/tree` requests as an editor with one folder deny; p95 < 500 ms warm, response ≤ 2,000 nodes.
- `folder_move_subtree_p95` — NFR-F005-01: 100 moves of a 400-folder subtree between two parents; path rewrite in one statement; p95 < 800 ms.
- `folder_create_p95` — NFR-F005-01: 200 folder creates spread across depths 1–10; p95 < 800 ms.
- `members_replace_500_entries_p95` — NFR-F005-01: 50 replacements of a 500-entry member set under `for update`; p95 < 800 ms, no deadlocks with a concurrent tree read.
- `workspace_list_index_scan` — FR-F005-03: 10,000 workspaces in a tenant, actor member of 500; list page uses `workspaces(tenant_id, updated_at desc)`, p95 < 300 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F005/performance/`.
