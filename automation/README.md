# Project automation

Required automation belongs here or in the implementation repository's `xtask`/CI system.

- `xtask`: Rust policy gate and audit commands.
- `validate-tickets`: metadata, IDs, branches, folders, dependencies, owned paths, flags, timestamps, required sections, and 500-line limit.
- `validate-work`: validates every Epic, Feature, Story, and Task file: front matter, parent links, branches, `depends_on` parity with `work/plan.md`, module-scoped owned paths and story/task subsets, placeholder rejection, requirement/scenario/test-name minimums, harness case coverage, and duplicate-body detection.
- `validate-plan`: proves every ID in `work/plan.md` has exactly one file at the expected path, each feature row lists 2 stories and 4 tasks, and no item exists outside the plan.
- `validate-decisions`: rejects missing or unresolved architecture decisions before scaffolding or implementation.
- `scaffold-plan`: create missing skeleton files and harness directories for plan rows from `work/templates/`; never overwrites and never edits the contract catalog.
- `audit-staged`: reject forbidden attribution tokens in staged content.
- `audit-message FILE`: reject forbidden tokens in commit messages.
- `audit-range RANGE`: reject forbidden tokens in pushed commit subjects/bodies.
- `audit-pr TITLE BODY`: reject forbidden tokens in pull request title/body.
- `self-test`: prove the policy rejects blocked text and accepts clean text, and that the content gate rejects a boilerplate ticket while accepting the gold ticket `F006`.
- `install-hooks`: configure `.githooks` as the repository hook path.
- `check-ownership`: reject changes outside active ticket `owned_paths`.
- `check-contracts`: every ticket reproduces its catalog aggregate, module slug, routes, events, and tables; every plan feature has a catalog row and vice versa.
- `test-feature <ID>`: verify the harness manifest and, once a workspace `Cargo.toml` exists, run `cargo test --features <ID>_FEATURE`.
- `test-all`: enable all feature gates and run the release matrix.
- `check-migrations`: migration files are `<version>_<module>_<description>.sql` with a matching `.down.sql`.

All commands must be deterministic, produce machine-readable output, and return nonzero on failure.

The policy gate rejects the configured provider/assistant attribution tokens case-insensitively. Enforcement files and `Claude.md` are excluded from staged-content scanning because they define the policy itself; commit messages, pushed history, PR titles, and PR bodies have no exemption.

Modules: `main.rs` dispatch, `policy.rs` attribution and ownership audits, `backlog.rs` plan model and structural validation, `content.rs` content-quality gates, `release.rs` contract, migration, and harness commands, `support.rs` shared helpers.
