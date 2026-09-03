---
id: E004
type: epic
status: planned
owner: platform
target_milestone: M3
branch: e004-collaboration-and-automation
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 7
- Capability contract: `docs/capability-contracts.md` rows F016, F017, F036, F037, F018, F019, F020, F045, F046
- Product spec: `docs/product-capability-spec.md` sections 5.4a, 5.4b, 5.5, 8

# E004 — Collaboration and automation

## Outcome

Work that exists as rows in E002 and E003 moves between people without manual handoffs. A request that entered through a form is commented on with an attachment, routed by a published workflow, approved by a quorum with escalation, assigned, and the assignee is told through the channel they chose. Every step is attributed in the activity feed, every side effect is executed exactly once through the JetStream outbox, and external collaborators reach exactly the resources they were granted through guest identities or expiring links. Documents and live co-editing complete the collaboration surface on the same authorization and file primitives.

## Scope

- Included: threaded comments with mentions and resolution on rows, sheets, cells, files, reports, and dashboards (F016); activity feed with human and automated attribution (F016); S3-compatible file storage with ClamAV scanning, MIME/size allowlists, checksums, versions, expiring URLs, previews, and proofing decisions (F017); resource share grants with the six spec roles, guest invitations, and revocable share links capped at 30 days (F036); the notification service with in-app, email, and push channels, delivery log, preferences, quiet hours, and digests (F037); the no-code workflow builder with typed triggers, conditions, and actions (F018); the queued, idempotent, retrying workflow runtime with dead letters (F019); approval instances with quorum, due dates, reassignment, and escalation (F020); document and folder library with immutable revisions (F045); WebSocket presence and Automerge co-editing with reconnect recovery (F046).
- Excluded: cross-sheet reports and dashboards (E005); webhooks and outbound integrations that consume these events (E006 F028, F029); SSO-driven guest provisioning (F026); DAM assets and renditions (F057); offline document co-editing (spec section 10); AI-proposed comments or actions (F039, F040).

## Child features

- `F016` Comments and activity: threaded conversations, mentions, resolution, activity feed. Depends on F006, F003.
- `F017` Files and proofing: object storage, scan, versions, expiring URLs, previews, proofs. Depends on F006, F004.
- `F036` Sharing, guests, and links: share grants, guest identity, expiring share links, explicit deny. Depends on F003, F005.
- `F037` Notification service: in-app, email, push, delivery log, preferences, quiet hours, digests. Depends on F004, F002.
- `F018` Workflow builder: trigger, condition, action schema and builder UI. Depends on F007, F035.
- `F019` Workflow runtime: queued runs, idempotency, retries, dead letters, inbound webhooks. Depends on F018, F004.
- `F020` Approvals and escalation: approval state machine, quorum, notifications, escalation timers. Depends on F019, F037.
- `F045` Documents/folders: document library, revisions, search, folder access. Depends on F005, F017, F036.
- `F046` Live collaboration: presence leases, ordered operations, reconnect and conflict recovery. Depends on F045, F004.

## Exit criteria

- [ ] The spec section 8 MVP scenario runs end to end on a seeded tenant: a form submission is routed for approval by a published workflow, the approved task is assigned, the assignee receives an in-app and email notification, comments on the row with an attachment that has passed the ClamAV scan, and an administrator can see every step in the activity feed and audit log.
- [ ] Workflow runs replayed from the same event produce no duplicate comments, approvals, or notifications (idempotency verified by the F019 and F037 harnesses).
- [ ] A guest invited to one sheet and a share-link holder cannot list workspaces, read any other resource, or perform writes outside a published form; explicit deny beats every inherited grant.
- [ ] Every child feature has passed its requirement, permission-negative, audit, notification, accessibility, and performance lanes, and its flag can be turned off without breaking E002 or E003 surfaces.
- [ ] Documents can be co-edited by two sessions with presence, and a reconnecting client replays missed revisions without overwriting a newer one.
