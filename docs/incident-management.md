# Incident management

Runbooks say how to fix one thing. This says how the team behaves when something is broken, who
decides, and what happens afterwards. It exists because the expensive part of an incident is rarely
the fix — it is the twenty minutes nobody was sure who was running it.

## Severity

Severity is set by impact on customers, not by how alarming the graph looks. The first responder
sets it and can raise it; only the incident lead lowers it.

| | Meaning | Response | Comms |
|---|---|---|---|
| **Sev 1** | Data loss or corruption, a cross-tenant exposure, or the product unusable for most tenants | Page immediately, 24×7, incident lead assigned within 5 minutes | Status page within 15 minutes, updates every 30 |
| **Sev 2** | A core capability broken for many, or any tenant fully blocked with no workaround | Page during business hours, best effort out of hours | Status page within 60 minutes, updates hourly |
| **Sev 3** | Degraded or slow, a workaround exists, or one tenant affected | Next business day | Direct to affected tenants |
| **Sev 4** | Cosmetic or latent, no customer impact | Ticket | None |

**A suspected cross-tenant data exposure is Sev 1 from the first report**, before it is confirmed.
It is the one failure this product cannot recover trust from, so it is treated as real until proven
otherwise, and confirming it is not a prerequisite for responding.

## Roles

One person holds each; on a small team one person may hold several, but they say which they are.

- **Incident lead** — runs the incident, holds the decisions, does not fix things themselves. Their
  job is to keep the response coherent and to decide when to escalate or stand down.
- **Operator** — the one making changes. Everyone else proposes; the operator applies, one change at
  a time, saying what they are about to do before doing it.
- **Scribe** — timestamps what happened, what was tried and what it did. Without this the postmortem
  is reconstructed from memory, which is how wrong conclusions are reached.
- **Comms** — owns the status page and customer contact so the lead is not writing updates.

## During

- **Stop the bleeding before finding the cause.** Roll back, disable the flag, shed the load. The
  cause can be found from evidence afterwards; the customer cannot get the hour back.
- **One change at a time, announced.** Two simultaneous fixes make the outcome unattributable.
- **Capture before you clear.** Take the logs, the query plan, the queue depth, the correlation ids
  before restarting the thing that holds them. A restart that fixes it and erases the evidence buys
  a repeat next week.
- Use the feature's runbook. If it is wrong or missing, that is a finding, and fixing it is part of
  the follow-up rather than an afterthought.

## Afterwards

A postmortem is written for every Sev 1 and Sev 2, within five working days, and is **blameless** in
the specific sense that it names systems, defaults and missing guardrails rather than people. If the
conclusion is that someone should have been more careful, the analysis is not finished — careful is
not a control.

It carries: what customers experienced and for how long; the timeline from first signal to
resolution; how it was detected, and whether an alert or a customer found it; what was actually
wrong; what made it worse or slower than it needed to be; and the actions.

Each action is a ticket with an owner and a date, and at least one must be a **control** — a test, a
gate, an alert, a constraint — not just a fix. A postmortem whose actions are all "be careful when
editing X" has not produced a control.

Detection is scored honestly: if a customer told us first, that is recorded as such and generating
the missing alert is one of the actions.

## Links

- Feature runbooks: `docs/milestones/runbooks/`
- Error budgets and burn alerts: F066, `docs/milestones/README.md`
- Threats and their mitigations: `docs/threat-model.md`
- Recovery targets, rollback and release: `docs/architecture-decisions.md` section 11
