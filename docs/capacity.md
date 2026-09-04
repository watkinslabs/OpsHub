# Capacity and sequencing

What 506 points means in time, with the assumptions stated so you can disagree with the assumptions
rather than the answer. This is a model, not a plan: it has no dates because dates need a team, and
the team is your input.

Regenerate the table from the tickets with the totals in `docs/milestones/README.md`; scope and this
file cannot drift because both are derived from `target_milestone` and `estimate`.

## The work

| Milestone | Features | Points | Cumulative | Gate to the next |
|---|---|---|---|---|
| M0 Foundation and control plane | 5 | 34 | 34 | Gates run and refuse a broken fixture |
| M1 Platform and core work OS | 15 | 118 | 152 | A team runs a real tracker with history and recovery |
| M2 Planning, intake and the front door | 9 | 65 | 217 | A project is provisioned from a template; work arrives by form, email and migration |
| M3 Collaboration and automation | 9 | 63 | 280 | Intake to approval to assignment runs unattended and is diagnosable |
| M4 Reporting and dashboards | 5 | 37 | 317 | A PMO runs a weekly review without spreadsheets |
| M5 Enterprise and commercial | 10 | 72 | 389 | Security review passes; a tenant can buy, pay and administer itself |
| M6 Portfolio and resources | 4 | 37 | 426 | Governance and capacity planning across projects |
| M7 Advanced modules and AI | 14 | 80 | 506 | Every module entitled, audited, reversible; AI proposes and never acts alone |

## Assumptions

1. **A point is roughly a focused engineer-day** including its tests, its accessibility pass and its
   review — not a day of typing. That is the only calibration here, and the first milestone will tell
   you whether it is right for this team. Recalibrate after M0 rather than defending the estimate.
2. **Delivered capacity is about 60% of nominal.** A five-person team is ~15 points a week, not 25:
   review, incidents, meetings, and the third of the work that is unplanned.
3. **Milestones are sequential; features inside one are not.** The dependency graph is acyclic and
   forward-only, so within a milestone several lanes run in parallel — that is what F043's lane
   isolation exists for. The parallel width is bounded by disjoint `owned_paths`, not by headcount.
4. **M0 and M1 do not parallelise well.** The control plane and the platform floor are mostly one
   dependency chain. Adding people there mostly adds coordination.

## What that gives

At ~15 points a week (a five-person team at 60%), M0+M1 is roughly 10 weeks and the whole 506 points
is around 34 weeks of delivered capacity. Treat those as the shape of the thing, not a commitment:
the honest statement is "M1 is about a quarter for a small team", and anything more precise before
M0 has run is invented.

## Sequencing advice

- **Build the vertical slice first.** F001, F068, F002 in order, and stop to look. That slice is the
  first contact between the specification and a compiler, and it will send edits back into the
  tickets. Better to learn that at 3 features than at 30.
- **Do not start M7 modules early because they look self-contained.** Every one is entitlement-gated,
  and the entitlement, billing and packaging chain lands in M5. A module built before it has nothing
  to gate against.
- **F062 blocks every screen.** It is in M1 for that reason. Building a feature's UI before the
  design system exists produces a screen that has to be rewritten.
- **The riskiest features are not the biggest.** F008 grid editing, F046 live collaboration, F035
  formulas and F068 persistence carry the most unknowns per point. Schedule slack against those, not
  against the ones with large estimates.

## Where this model is weakest

The estimates were set by the same process that wrote the tickets, so they are internally consistent
and externally unvalidated. Nothing here has met a compiler. The first three features are the
calibration, and this file should be rewritten with real velocity once they are done — a model that
survives contact untouched was not being used.
