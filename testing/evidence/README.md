# Release and CI evidence

Per-feature `F###/` folders hold lane artifacts (JUnit output, traces, videos, `EXPLAIN` plans, k6 summaries) and the `manifest.json` recording each run's command, fixture seed, and result. `verify-release` writes `F###/release.json` and `milestones/M#.json` as the signed record that a feature met its gates.

Lane artifacts are regenerated and stay out of git; `release.json`, `manifest.json`, and the milestone signatures are the audit record and are tracked.
