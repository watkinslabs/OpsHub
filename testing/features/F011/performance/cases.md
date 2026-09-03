# F011 performance cases

File: `testing/features/F011/performance/{schedule_bench.rs,calendar_math_bench.rs}`. Runs against a 100,000-row seeded sheet with fixed seed. Flag `F011_FEATURE`.

- `schedule_read_100k_p95` — NFR-F011-01: 200 sequential `GET /schedule?limit=500` requests on a 100,000-row sheet; p95 < 500 ms warm.
- `reschedule_p95` — NFR-F011-01: 200 reschedules spread across rows with the `Berlin` calendar; p95 < 800 ms.
- `add_working_days_10y_under_5ms` — NFR-F011-01: 10,000 calls adding 2,500 working days on a calendar with 400 exceptions; each under 5 ms, no allocation growth.
- `working_days_between_symmetry` — FR-F011-07: property test over 10,000 random date pairs; `between(a, add(a, n)) == n` for the `Standard` and `Berlin` calendars.

Evidence: criterion summaries under `testing/evidence/F011/performance/`.
