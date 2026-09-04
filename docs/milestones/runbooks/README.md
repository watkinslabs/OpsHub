# Support runbooks

Spec section 8 requires a support runbook per capability before it ships. A runbook is for the person
woken at 03:00 who did not write the feature: what broke, how to confirm it, what to do, and what not
to do. It is not documentation of how the feature works.

`TEMPLATE.md` is the shape. A feature's exit criteria are not met until its runbook exists and its
first diagnostic step has been executed once against a real environment — an untested runbook is a
guess written down.

## Which features must ship one

Every feature with an async path, an external dependency, or a surface that can page someone:

| Feature | Runbook | Why it pages |
|---|---|---|
| F004 | `outbox-and-jobs.md` | Outbox lag, dead letters, worker restart |
| F008 | `grid-write-conflicts.md` | Version conflict storms under concurrent editing |
| F019 | `workflow-runs.md` | A run stuck, looping, or dead-lettered |
| F029, F030, F063 | `integration-sync.md` | Provider throttling, expired credentials, conflict backlog |
| F037 | `notification-delivery.md` | Mail not arriving; digest or quiet-hours suppression |
| F046 | `live-collaboration.md` | Session storms, reconnect loops |
| F059 | `publication-access.md` | A published link leaking, stale, or 404ing |
| F064 | `billing-webhooks.md` | Payment webhook backlog; a tenant wrongly restricted |
| F066 | `slo-burn.md` | An error budget burning; which SLI and what to shed |
| F067 | `load-gate.md` | The scale gate failing or skipping before a milestone |

## Rules

- Name the exact command, query or dashboard. "Check the logs" is not a step.
- State the blast radius before the fix: what is already broken, and what the fix may break.
- Every destructive step names its reversal, or says plainly that there is none.
- If the answer is "escalate", say to whom and with what evidence attached.
- A runbook that has never been followed is reviewed as untested code.
