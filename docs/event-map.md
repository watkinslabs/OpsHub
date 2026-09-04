# Event map

Every domain event, who publishes it, and who reacts to it inside the product. Generated from the
events column of `docs/capability-contracts.md` and from the tickets that name each event, so it
cannot drift from the catalog.

## How to read the consumers column

An event with no named consumer is **not** an orphan. Four consumers are generic and subscribe by
pattern rather than by name, so they do not appear per row:

- **F028 webhooks** delivers any event a customer subscribes to, which is the main reason an event
  exists at all — most of these are published for people outside this repository.
- **F003 audit** records the actor, diff and correlation id for every mutation alongside its event.
- **F010 search** reindexes from create, update and delete events across every indexed aggregate.
- **F037 notifications** routes the subset that has a notification category.

A row with a named consumer means one feature reacts to another's event in a way that the reacting
feature's specification depends on. Those are the couplings worth knowing about before changing a
payload: **breaking one of these breaks another feature**, whereas breaking a generic consumer
breaks a customer's webhook, which is a versioning problem instead.

250 events across 64 features. 48 have a named in-repo consumer.

## Cross-feature couplings

| Event | Produced by | Consumed by |
|---|---|---|
| `approval.decided.v1` | F020 | F019, F032, F040, F054, F057 |
| `approval.escalated.v1` | F020 | F037 |
| `approval.requested.v1` | F020 | F037 |
| `baseline.captured.v1` | F015 | F032 |
| `capacity.computed.v1` | F033 | F034 |
| `cell.updated.v1` | F008 | F009, F010, F012, F016, F035, F053, F058, F060, F061 |
| `cells.bulk-updated.v1` | F008 | F009, F010, F035, F053, F060 |
| `column.deleted.v1` | F007 | F060 |
| `comment.created.v1` | F016 | F010 |
| `dashboard.deleted.v1` | F023 | F070 |
| `document.deleted.v1` | F045 | F070 |
| `document.restored.v1` | F045 | F070 |
| `document.revision-added.v1` | F045 | F047 |
| `document.updated.v1` | F045 | F047 |
| `file.deleted.v1` | F017 | F016, F070 |
| `file.uploaded.v1` | F017 | F010, F016 |
| `folder.updated.v1` | F005 | F070 |
| `form.submitted.v1` | F014 | F019, F058 |
| `formula.recalculated.v1` | F035 | F060 |
| `guest.invited.v1` | F036 | F037 |
| `link.updated.v1` | F009 | F035 |
| `mention.created.v1` | F016 | F037 |
| `metric.computed.v1` | F022 | F024 |
| `project.provisioned.v1` | F015 | F032 |
| `proof.decided.v1` | F017 | F037 |
| `report.deleted.v1` | F021 | F070 |
| `rollup.recomputed.v1` | F009 | F035 |
| `row.created.v1` | F006 | F010, F019, F060 |
| `row.deleted.v1` | F006 | F009, F010, F016, F053, F060, F070 |
| `row.reparented.v1` | F009 | F012, F035 |
| `row.restored.v1` | F006 | F009, F010, F070 |
| `row.updated.v1` | F006 | F009, F010, F012, F016, F019, F028, F032, F053 |
| `rows.bulk-updated.v1` | F008 | F009, F035, F060 |
| `session.revoked.v1` | F038 | F058 |
| `share.granted.v1` | F036 | F037 |
| `sheet.created.v1` | F006 | F010 |
| `sheet.deleted.v1` | F006 | F010, F016, F070 |
| `sheet.restored.v1` | F006 | F010, F070 |
| `sheet.updated.v1` | F006 | F010 |
| `subscription.updated.v1` | F064 | F065 |
| `tenant.created.v1` | F002 | F004 |
| `update-request.reminded.v1` | F061 | F037 |
| `update-request.sent.v1` | F061 | F037 |
| `user.deactivated.v1` | F002 | F037 |
| `view.deleted.v1` | F013 | F070 |
| `workflow-run.completed.v1` | F019 | F016 |
| `workflow-run.failed.v1` | F019 | F037 |
| `workload-conflict.detected.v1` | F034 | F032 |

## All events by producer

**F002 — Tenant, users, and groups**  
  `group.updated.v1`, `tenant.created.v1`, `tenant.suspended.v1`, `tenant.updated.v1`, `user.created.v1`, `user.deactivated.v1`, `user.updated.v1`

**F003 — Authorization and audit**  
  `acl.updated.v1`, `audit.recorded.v1`, `role.updated.v1`

**F004 — Runtime operations**  
  `outbox.published.v1`

**F005 — Workspace navigation**  
  `folder.moved.v1`, `folder.updated.v1`, `workspace-member.updated.v1`, `workspace.created.v1`, `workspace.deleted.v1`, `workspace.restored.v1`, `workspace.updated.v1`

**F006 — Sheets/boards/items**  
  `row.created.v1`, `row.deleted.v1`, `row.moved.v1`, `row.restored.v1`, `row.updated.v1`, `sheet.created.v1`, `sheet.deleted.v1`, `sheet.restored.v1`, `sheet.updated.v1`

**F007 — Typed columns**  
  `column.created.v1`, `column.deleted.v1`, `column.reordered.v1`, `column.updated.v1`

**F008 — Grid editing**  
  `cell.updated.v1`, `cells.bulk-updated.v1`, `edit.undone.v1`, `rows.bulk-updated.v1`

**F009 — Hierarchy and links**  
  `link.created.v1`, `link.deleted.v1`, `link.updated.v1`, `rollup.recomputed.v1`, `row.reparented.v1`

**F010 — Search/import/export**  
  `export.completed.v1`, `import.completed.v1`, `import.failed.v1`, `import.started.v1`, `search.indexed.v1`

**F011 — Dates and schedules**  
  `row.rescheduled.v1`, `schedule-settings.updated.v1`, `working-calendar.updated.v1`

**F012 — Dependencies and Gantt**  
  `dependency.created.v1`, `dependency.deleted.v1`, `dependency.updated.v1`, `schedule.shifted.v1`

**F013 — Views**  
  `view.created.v1`, `view.deleted.v1`, `view.shared.v1`, `view.updated.v1`

**F014 — Forms**  
  `form.published.v1`, `form.submission-rejected.v1`, `form.submitted.v1`, `form.updated.v1`

**F015 — Templates and baselines**  
  `baseline.captured.v1`, `project.provisioned.v1`, `provisioning.failed.v1`, `template.published.v1`

**F016 — Comments and activity**  
  `comment.created.v1`, `comment.deleted.v1`, `comment.resolved.v1`, `comment.updated.v1`, `mention.created.v1`

**F017 — Files and proofing**  
  `file.deleted.v1`, `file.quarantined.v1`, `file.scanned.v1`, `file.uploaded.v1`, `file.version-added.v1`, `proof.decided.v1`

**F018 — Workflow builder**  
  `workflow.disabled.v1`, `workflow.published.v1`, `workflow.updated.v1`

**F019 — Workflow runtime**  
  `workflow-run.completed.v1`, `workflow-run.dead-lettered.v1`, `workflow-run.failed.v1`, `workflow-run.queued.v1`, `workflow-run.started.v1`

**F020 — Approvals and escalation**  
  `approval.cancelled.v1`, `approval.decided.v1`, `approval.escalated.v1`, `approval.requested.v1`

**F021 — Cross-source reports**  
  `report.created.v1`, `report.deleted.v1`, `report.refreshed.v1`, `report.updated.v1`

**F022 — Metrics and summaries**  
  `metric.computed.v1`, `metric.updated.v1`

**F023 — Dashboard builder**  
  `dashboard.created.v1`, `dashboard.deleted.v1`, `dashboard.refreshed.v1`, `dashboard.updated.v1`

**F024 — Charts and insights**  
  `chart.updated.v1`, `time-series.projected.v1`

**F025 — Export/drill-through**  
  `drill-through.opened.v1`, `report-export.completed.v1`, `report-export.failed.v1`, `report-export.requested.v1`

**F026 — SSO/SCIM**  
  `identity-connection.updated.v1`, `saml.login.v1`, `scim.group-synced.v1`, `scim.user-synced.v1`

**F027 — Governance/compliance**  
  `access-review.generated.v1`, `legal-hold.applied.v1`, `purge.confirmed.v1`, `retention-policy.updated.v1`, `tenant-export.completed.v1`

**F028 — API/webhooks**  
  `application.updated.v1`, `webhook.delivered.v1`, `webhook.disabled.v1`, `webhook.failed.v1`, `webhook.updated.v1`

**F029 — Microsoft/Google/Slack**  
  `integration.connected.v1`, `integration.notified.v1`, `integration.refresh-failed.v1`, `integration.revoked.v1`

**F030 — Jira/Salesforce/files**  
  `sync-conflict.detected.v1`, `sync-conflict.resolved.v1`, `sync-run.completed.v1`, `sync-run.failed.v1`, `sync-run.started.v1`, `sync.updated.v1`

**F031 — Portfolio rollups**  
  `portfolio.rollup-refreshed.v1`, `portfolio.updated.v1`

**F032 — Project health/governance**  
  `health-override.set.v1`, `project-health.computed.v1`, `project-intake.submitted.v1`, `stage-gate.decided.v1`, `stage-gate.submitted.v1`

**F033 — Resources/capacity**  
  `allocation.created.v1`, `allocation.deleted.v1`, `allocation.updated.v1`, `capacity.computed.v1`, `resource.updated.v1`

**F034 — Workload/actuals**  
  `time-entry.reconciled.v1`, `time-entry.recorded.v1`, `workload-conflict.detected.v1`

**F035 — Formula engine**  
  `formula.failed.v1`, `formula.recalculated.v1`, `formula.updated.v1`

**F036 — Sharing, guests, and links**  
  `guest.accepted.v1`, `guest.invited.v1`, `share-link.created.v1`, `share-link.revoked.v1`, `share.granted.v1`, `share.revoked.v1`, `share.updated.v1`

**F037 — Notification service**  
  `digest.sent.v1`, `notification.created.v1`, `notification.delivered.v1`, `notification.failed.v1`

**F038 — Authentication and MFA**  
  `api-token.created.v1`, `api-token.revoked.v1`, `mfa.enrolled.v1`, `mfa.removed.v1`, `session.created.v1`, `session.revoked.v1`

**F039 — AI formulas/queries**  
  `ai-proposal.applied.v1`, `ai-proposal.created.v1`, `ai-proposal.rejected.v1`, `ai-query.executed.v1`

**F040 — AI insights/automation**  
  `ai-action.confirmed.v1`, `ai-action.proposed.v1`, `ai-action.rejected.v1`, `ai-insight.dismissed.v1`, `ai-insight.generated.v1`

**F045 — Documents/folders**  
  `document.created.v1`, `document.deleted.v1`, `document.moved.v1`, `document.restored.v1`, `document.revision-added.v1`, `document.updated.v1`

**F046 — Live collaboration**  
  `document.change-applied.v1`, `presence.joined.v1`, `presence.left.v1`, `sheet.patch-applied.v1`

**F047 — MCP access server**  
  `mcp.mutation-confirmed.v1`, `mcp.mutation-proposed.v1`, `mcp.resource-read.v1`, `mcp.tool-called.v1`

**F048 — Entitlements and feature flags**  
  `entitlement.updated.v1`, `feature-flag.updated.v1`

**F049 — Localization**  
  `locale.updated.v1`

**F050 — Dynamic View**  
  `dynamic-view.row-edited.v1`, `dynamic-view.updated.v1`

**F051 — WorkApps**  
  `workapp.published.v1`, `workapp.updated.v1`

**F052 — Data Shuttle**  
  `shuttle-run.completed.v1`, `shuttle-run.failed.v1`, `shuttle-run.started.v1`

**F053 — DataMesh**  
  `mapping-conflict.detected.v1`, `mapping.synced.v1`, `mapping.updated.v1`

**F054 — Bridge**  
  `bridge-run.completed.v1`, `bridge-run.failed.v1`, `bridge-run.started.v1`, `bridge-run.step-completed.v1`

**F055 — Calendar App**  
  `calendar.published.v1`, `calendar.updated.v1`

**F056 — Pivot App**  
  `pivot.computed.v1`, `pivot.updated.v1`

**F057 — DAM assets**  
  `asset.archived.v1`, `asset.created.v1`, `asset.rendition-ready.v1`, `asset.rights-updated.v1`, `asset.updated.v1`

**F058 — Mobile clients**  
  `mobile-device.registered.v1`, `mobile-sync.applied.v1`, `mobile-sync.rejected.v1`

**F059 — Publishing/embedding**  
  `publication.created.v1`, `publication.revoked.v1`, `publication.updated.v1`, `publication.viewed.v1`

**F060 — Conditional formatting**  
  `formatting-rule.deleted.v1`, `formatting-rule.updated.v1`

**F061 — Update requests**  
  `update-request.cancelled.v1`, `update-request.reminded.v1`, `update-request.responded.v1`, `update-request.sent.v1`

**F063 — Microsoft Entra integration**  
  `entra.connected.v1`, `entra.group-synced.v1`, `entra.mail-sent.v1`, `entra.revoked.v1`

**F064 — Billing and subscriptions**  
  `credit-code.issued.v1`, `credit.redeemed.v1`, `invoice.issued.v1`, `invoice.payment-failed.v1`, `subscription.updated.v1`, `usage.recorded.v1`

**F065 — Self-serve signup and trials**  
  `signup.abandoned.v1`, `signup.started.v1`, `signup.verified.v1`, `tenant.provisioned.v1`

**F069 — Home and my work**  
  `favorite.added.v1`, `favorite.removed.v1`

**F070 — Trash and recovery**  
  `item.purged.v1`, `item.restored.v1`

**F071 — Migration import**  
  `migration.completed.v1`, `migration.failed.v1`, `migration.started.v1`

**F072 — Inbound email**  
  `inbound-message.applied.v1`, `inbound-message.received.v1`, `inbound-message.rejected.v1`

**F073 — Announcements and in-app help**  
  `announcement.dismissed.v1`, `announcement.published.v1`

