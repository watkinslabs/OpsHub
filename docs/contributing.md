# Contributing

## Day one

You need Rust stable (from `rust-toolchain.toml` once F001 lands), Node 22 with pnpm, Docker, and
Python 3 for the design generators. Nothing else.

```sh
git clone https://github.com/watkinslabs/OpsHub && cd OpsHub
git config core.hooksPath .githooks          # the gates run on commit and push
export CARGO_TARGET_DIR=/tmp/opshub-xtask-target
M=automation/xtask/Cargo.toml

cargo run --quiet --manifest-path $M -- validate-decisions
cargo run --quiet --manifest-path $M -- validate-plan
cargo run --quiet --manifest-path $M -- validate-tickets
cargo run --quiet --manifest-path $M -- validate-work
cargo run --quiet --manifest-path $M -- check-contracts
cargo run --quiet --manifest-path $M -- check-persistence
cargo run --quiet --manifest-path $M -- check-roles
cargo run --quiet --manifest-path $M -- check-design
cargo run --quiet --manifest-path $M -- check-references
cargo run --quiet --manifest-path $M -- check-migrations
cargo run --quiet --manifest-path $M -- test-all
cargo run --quiet --manifest-path $M -- self-test
```

All twelve pass on a clean clone. If one fails on a clone you have not touched, that is a bug in the
gate or the backlog, not something to work around — fix it or report it before continuing.

Product code does not exist yet. F001 creates the Cargo and pnpm workspaces; until it is done there
is nothing to compile, and the gates above are the whole build.

To rebuild the designs:

```sh
cd design/generator && for f in *.py; do case $f in _*) continue;; esac; python3 "$f"; done
```

That must leave the tree clean. A diff means an artboard was edited by hand instead of through its
generator.

## The build, once code exists

Today the gates are the whole build. F001 creates the workspaces, and from then on a full local build
is:

```sh
docker compose -f infra/compose/docker-compose.yml up -d   # postgres:18, nats:2.11 with JetStream, minio
sqlx migrate run                                            # schema
cargo build --workspace                                     # api, worker, realtime, mcp
pnpm install --frozen-lockfile && pnpm --filter web build   # apps/web/dist
cargo xtask test-all                                        # every feature harness
```

CI grows from one job to the five F001 specifies, all required checks: `validate-work` runs the
thirteen gates; `rust` starts real Postgres and NATS containers and runs `cargo fmt --check`,
`cargo clippy -- -D warnings` and `cargo test`; `web` runs lint, typecheck, tests and build;
`policy` audits commit and pull-request text; `line-limit` enforces the 500-line rule.

An image is built once and promoted through the environments unchanged — see
`docs/architecture-decisions.md` section 11 for release and rollback, and section 2.2 for how a
schema change is staged so the previous binary always runs against the current schema.

### Build order

The dependency graph is forward-only, but four features gate almost everything and are worth naming:

1. **F001** — the workspaces and CI. Nothing compiles before it.
2. **F068** — the repository contract. Write it before anything touches the database, or the first
   features will contain SQL that has to be pulled back out.
3. **F062** — tokens, theme and the component library. Build a screen before it and the screen gets
   rewritten.
4. **F002, F038, F003, F004** — tenants, authentication, authorization, runtime. Every later feature
   assumes these.

Then take milestones in order from `docs/milestones/README.md`, and within a milestone take any
feature whose dependencies are archived. Lanes run in parallel where `owned_paths` are disjoint,
which is what F043 exists to arbitrate.

## Picking up work

1. Read `docs/milestones/README.md` and take the lowest-order feature in `work/plan.md` whose
   dependencies are archived. Do not start an item with an unmet dependency or an overlapping owned
   path — the fanout gate will refuse it anyway.
2. Claim it: move the ticket to `work/inprogress/`, record `started_at`, create the branch named in
   its front matter. One ticket, one owner, one branch.
3. Write the failing tests first, in that feature's harness under `testing/features/F###/`, and
   observe them fail. The ticket names them.
4. Implement only inside the ticket's `owned_paths`. Touching another feature's paths means the
   ticket is wrong; fix the ticket first.
5. Meet every exit criterion, record `finished_at`, move the file to `work/archived/`.

## Pull requests

- **One ticket per pull request.** A PR that changes two features cannot be reviewed against either
  ticket's exit criteria.
- The description states the ticket id, what changed, the commands run with their evidence, and the
  rollback. If the ticket's behaviour changed during implementation, the ticket is updated in the
  same PR — the specification and the code land together or the specification is already wrong.
- Every gate is a required check. A red gate is never merged around; if a gate is wrong, that is its
  own PR.
- No merge without a review from someone who did not write it. On a solo change, that means it waits.

## Reviewing

Read the ticket first, then the diff against it. In order:

1. **Does it do what the ticket says**, including the failure paths and the permission negatives, or
   only the happy path?
2. **Is the test real?** A test that would pass against an empty implementation is not a test. Check
   it was written first and observed failing — the harness lane and the PR evidence should show it.
3. **The rules nothing else catches**, listed in `docs/engineering-standards.md` section 9:
   `className` used for layout only, error enums mapped once per module, tracing spans carrying
   `tenant_id`, `actor_id` and `correlation_id`, and the expand-migrate-contract phase named for any
   migration.
4. **Would this leak across tenants?** Every query through a repository, every list prefiltered by
   ACL rather than filtered afterwards, every not-found for something invisible rather than denied.
5. **What happens when it fails?** Retry, dead letter, replay, and a message a support engineer can
   act on.

Approve when it is right, not when it is close. "Fix in a follow-up" is how a backlog of known
defects starts, and this repository is built to not have one.

## Commits

- Present tense, saying what changed and why it is right, not what files moved.
- The forbidden-token policy rejects vendor attribution tokens in commit text; the hook will tell you.
- Commit when a thing is done and green, not at the end of a day.
