# Packaging

Which plan includes what. `tenants.plan` is `free`, `team` or `enterprise` (F002 FR-F002-02) and F048
stores an entitlement per module with `source: plan|manual`. Until now nothing said what a plan
*means*, so "upgrade to Enterprise" had no definition and F064 had nothing to project onto F048.
This file is that definition; F064 reads it and writes entitlements from it.

A `manual` entitlement always wins over a plan-derived one, so an operator can grant a module to a
tenant on any plan without this table fighting them.

## 1. Plans

| | Free | Team | Enterprise |
|---|---|---|---|
| Price | £0 | per seat, monthly or annual | per seat, annual, negotiated |
| Users | up to 5 | up to 250 | unlimited |
| Storage | 2 GB | 100 GB | 1 TB, extendable |
| Sheets per workspace | 25 | unlimited | unlimited |
| Rows per sheet | 5,000 | 100,000 | 100,000 |
| Automation runs | 100 / month | 10,000 / month | 100,000 / month |
| API requests | 1,000 / day | 50,000 / day | 500,000 / day |
| Audit retention | 30 days | 1 year | 7 years |
| Support | community | business hours | 24×7 with the F066-derived SLA |

## 2. Modules by plan

Every module here is an F048 entitlement key. `active` means the plan grants it; `trial` means a
self-serve trial grants it for its duration; `none` means it must be bought or granted manually.

| Module | Free | Team | Enterprise | Notes |
|---|---|---|---|---|
| `dynamic-views` | none | active | active | External scoped editing (F050) |
| `workapps` | none | trial | active | Composed role-based apps (F051) |
| `calendar-app` | none | active | active | Multi-source calendar (F055) |
| `pivots` | none | active | active | Pivot app (F056) |
| `data-shuttle` | none | none | active | Scheduled file flows (F052) |
| `datamesh` | none | none | active | Cross-sheet reference sync (F053) |
| `bridge` | none | none | active | Cross-system workflows (F054) |
| `assets` | none | none | active | Digital asset management (F057) |
| `ai-assist` | none | trial | active | Formula and query assistance (F039), metered |
| `ai-insights` | none | trial | active | Evidence-backed insights (F040), metered |

Capabilities **not** on this list are in every plan at every tier and are never gated: sheets, typed
columns, formulas, views, forms, comments, files, sharing, permissions, workflows, approvals,
notifications, reports, dashboards, portfolios, resources, search, import and export, publishing,
conditional formatting, update requests, mobile, SSO and SCIM, Entra, the public API, webhooks and
MCP. Security and identity are never an upsell — an enterprise buyer does not pay extra to turn on
SAML, and gating them would put a tenant's own safety behind a paywall.

## 3. Trial

A self-serve trial (F065) is 14 days at `team` limits, with `workapps`, `ai-assist` and `ai-insights`
at `state: trial`. At expiry those become `none` after the 7-day read-only grace, and the tenant
falls back to `free` limits with its data intact. Nothing is deleted by a downgrade — F064's dunning
ladder degrades entitlements before access and never blocks export.

## 4. Changing this file

A plan change here is a product decision with three consequences, and all three are part of the same
change:

1. F064's projection writes the new entitlement set on the next plan change or renewal.
2. Existing tenants are **not** silently downgraded. Removing a module from a plan grandfathers
   current holders as `source: manual` with a note, and the change applies to new subscriptions.
3. The upgrade surface in `/admin/entitlements` names what the tenant would gain, generated from
   this table rather than written twice.
