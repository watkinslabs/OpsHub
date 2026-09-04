# Authorization model

The single vocabulary every feature authorizes against. `docs/capability-contracts.md` names a role
in each row's Roles column; this file defines what that role is and what it may do. Nothing else may
invent a role or a permission — `cargo xtask check-roles` fails on a role a ticket or catalog row
uses that is not defined here.

Evaluation itself is F003: tenant suspended → denied; an explicit `deny` on the resource or any
ancestor wins; otherwise the nearest `allow`; with no applicable entry the result is deny.

## 1. Permission catalogue

A permission is `<resource>:<action>`. Resources are the aggregates in the contract catalog; actions
are drawn from this closed set. A role is a named set of these strings and nothing more.

| Action | Means |
|---|---|
| `read` | See the resource and its content the caller is otherwise entitled to |
| `create` | Bring a new instance into existence under a parent the caller may `read` |
| `update` | Change an existing instance under an expected version |
| `delete` | Soft-delete; `purge` is separate and privileged |
| `purge` | Irreversibly remove, only through the audited governance job |
| `share` | Grant, change or revoke another principal's access |
| `export` | Take content out of the product as a file or feed |
| `run` | Execute something with effects — a workflow, a sync, a job, a scan |
| `approve` | Record a decision that gates another action |
| `administer` | Change configuration that governs other people's access or cost |

Resource keys: `tenant`, `user`, `group`, `role`, `workspace`, `folder`, `sheet`, `column`, `row`,
`cell`, `view`, `form`, `comment`, `file`, `document`, `workflow`, `workflow-run`, `approval`,
`report`, `metric`, `dashboard`, `chart`, `export`, `portfolio`, `project`, `resource-profile`,
`allocation`, `time-entry`, `template`, `baseline`, `share`, `notification`, `integration`, `sync`,
`api-application`, `webhook`, `identity-connection`, `entitlement`, `feature-flag`, `subscription`,
`credit`, `signup`, `audit`, `compliance-policy`, `publication`, `asset`, `calendar`, `pivot`,
`workapp`, `dynamic-view`, `ai-request`, `ai-insight`, `mcp-server`, `formatting-rule`,
`update-request`, `document-folder`, `data-flow`, `mapping`, `bridge-flow`, `mobile-device`.

`*:read` and the other wildcards expand at seed time to every resource key above; they are shorthand
in this document only, never a stored value. A stored permission row is always one explicit
`<resource>:<action>` pair, so revoking a resource key from a role is a row deletion rather than a
re-interpretation.

## 2. Principal kinds

These appear in the catalog's Roles column but are not roles. They describe *who is calling*, and
they constrain what any role can grant.

| Kind | Meaning |
|---|---|
| `self` | The authenticated user acting on their own record — their preferences, their sessions, their notification settings, their time entries. Carries no role and cannot be granted to anyone else. |
| `public` | No session at all. Reaches only the unauthenticated routes (`/public/**`, `/embed/**`) and only through a token that carries its own scope. |
| `scoped-actor` | A token-bound context — an API token, an MCP token, a share link, an update-request link. Its authority is the intersection of the minting user's permissions and the token's stored scope, and it can never exceed either. |
| `platform-operator` | Runs the deployment, not a tenant. Creates tenants, kills feature flags, mints credit codes. Never has tenant data access by virtue of this kind. |
| `maintainer` | Repository and tooling role for the delivery control plane. No product surface. |
| `operator` | Runs the service: health, backups, restore drills, SLOs. No product surface. |
| `release-manager` | May record a release signature (F044). No product surface. |

## 3. Role catalogue

Every role is tenant-scoped and attaches at a scope kind. `Inherits` is literal: the role's
permission set is the named role's set plus the additions listed.

### 3.1 Base resource roles

Seeded per tenant by F003. These are the roles a resource ACL grants.

| Role | Scope kinds | Permission set |
|---|---|---|
| `viewer` | any resource | `*:read` |
| `commenter` | any resource | viewer + `comment:create`, `comment:update` (own only) |
| `editor` | any resource | commenter + `*:create`, `*:update`, `*:delete` on the resource and its children |
| `admin` | workspace, folder | editor + `share`, `*:administer` within the scope |
| `owner` | any resource | admin + transfer of ownership; exactly one per resource |
| `tenant-admin` | tenant | every permission in the catalogue except `purge`, which additionally requires the compliance path |
| `form-submitter` | form | `form:read`, `row:create` through that published form only |

`resource-owner`, `resource-editor`, `resource-commenter`, `resource-viewer` and `resource-admin` in
the catalog are these same roles named against a generic resource; they are not separate roles and
are normalized to `owner`, `editor`, `commenter`, `viewer` and `admin` at seed time.

### 3.2 Capability roles

Granted at tenant or workspace scope for a capability that is not one resource's ACL. Each inherits
the base role named, so a capability role is always a superset of ordinary access, never a bypass.

| Role | Scope | Inherits | Adds | Used by |
|---|---|---|---|---|
| `workspace-admin` | workspace | admin | `workspace:administer`, `folder:*` | F005 |
| `sheet-viewer` | sheet | viewer | — | F013 |
| `sheet-editor` | sheet | editor | `column:*`, `row:*`, `cell:*`, `view:create` | F006–F011, F035, F046, F060 |
| `project-editor` | sheet | sheet-editor | `project:update`, dependency and baseline edits | F012 |
| `view-owner` | view | owner | `dynamic-view:administer` | F050 |
| `form-admin` | sheet | sheet-editor | `form:*` | F014 |
| `document-editor` | document | editor | `document:*` | F045, F046 |
| `resource-exporter` | workspace | viewer | `export:create`, `export:read` | F025 |
| `workflow-viewer` | workspace | viewer | `workflow:read`, `workflow-run:read` | F019 |
| `workflow-editor` | workspace | editor | `workflow:*`, `workflow-run:run` | F018–F020, F040, F054 |
| `approver` | approval | — | `approval:approve`, `approval:read` on approvals routed to them | F020 |
| `report-viewer` | workspace | viewer | `report:read`, `chart:read` | F021, F024 |
| `report-editor` | workspace | editor | `report:*`, `metric:*`, `chart:*`, `pivot:*` | F021, F022, F024, F056 |
| `dashboard-editor` | workspace | editor | `dashboard:*` | F023 |
| `publisher` | workspace | editor | `publication:*` | F059 |
| `portfolio-viewer` | portfolio | viewer | `portfolio:read`, `project:read` | F031 |
| `portfolio-admin` | portfolio | admin | `portfolio:*`, `template:*`, `baseline:*`, stage gates | F015, F031, F032 |
| `resource-admin` | tenant | admin | `resource-profile:*`, `allocation:*` | F033 |
| `asset-editor` | workspace | editor | `asset:*` | F057 |
| `calendar-editor` | workspace | editor | `calendar:*` | F055 |
| `app-admin` | workspace | admin | `workapp:*` | F051 |
| `data-admin` | tenant | admin | `data-flow:*`, `mapping:*`, `bridge-flow:*` | F052, F053, F054 |
| `integration-admin` | tenant | admin | `integration:*`, `sync:*` | F029, F030 |
| `identity-admin` | tenant | admin | `identity-connection:*` | F026, F063 |
| `compliance-admin` | tenant | admin | `compliance-policy:*`, `audit:read`, `*:purge` | F027 |
| `billing-admin` | tenant | admin | `subscription:*`, `credit:read`, `credit:update` | F064 |
| `requester` | update-request | — | `update-request:create`, `update-request:read` on their own | F061 |

### 3.3 Rules that hold for every role

- A role grants; it never widens a scoped token. A `scoped-actor` holding a role still cannot exceed
  the token's stored scope.
- No role grants `purge`. Purge runs only through the F027 governance job under `compliance-admin`,
  and a legal hold refuses it.
- No capability role grants `share` unless it inherits `admin` or `owner`.
- `tenant-admin` is not a superuser over data it has no ACL entry for: it may grant itself access,
  and that grant is audited, which is the point.
- Adding a resource key to the catalogue requires adding it to section 1 and re-seeding wildcards;
  adding a role requires a row in section 3 and a ticket that uses it.
