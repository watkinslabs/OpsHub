# F046 performance cases

File: `testing/features/F046/performance/{round_trip_bench.rs,sessions_bench.rs,replay_bench.rs,propagation_bench.rs}`. Load generator from `fixtures/load_generator.rs`, change corpus from `fixtures/change_corpus.rs`. Flag `F046_FEATURE`.

- `change_round_trip_50_editors_p95` — NFR-F046-01: 50 clients on one document each sending 2 changes per second for 60 s; send-to-ack p95 < 250 ms.
- `thousand_sessions_one_node_memory` — NFR-F046-01: 1,000 sessions across 100 documents on one node renewing presence every 10 s; resident memory < 512 MB and no lease expiries.
- `presence_propagation_two_nodes` — FR-F046-13, NFR-F046-01: 200 joins split across two nodes; cross-node visibility p95 < 1 s.
- `replay_1000_changes_p95` — NFR-F046-01: `GET /changes?since=0&limit=1000` on the 1,000-change corpus; p95 < 500 ms.
- `snapshot_materialization_bounded` — FR-F046-06: materializing 500 changes into a revision completes in < 2 s.

Evidence: criterion and k6 summaries under `testing/evidence/F046/performance/`.
