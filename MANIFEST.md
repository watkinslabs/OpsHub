# OpsHub documentation manifest

Canonical repository: `github.com/watkinslabs/OpsHub`.

`Claude.md` is the required entry point. It contains naming, branch, ticket, coding, testing, agent, security, and gate rules. Do not read every document.

## Required for implementation

| Need | Read |
|---|---|
| Product scope | `docs/product-capability-spec.md` |
| Architecture decisions | `docs/architecture-decisions.md` |
| Backlog hierarchy | `work/plan.md` |
| New feature ticket | `work/templates/ticket.md` |
| Current work | Only the target file in `work/tickets/`, `work/inprogress/`, or `work/archived/` |
| Test rules | `testing/README.md` |
| Automated gates | `automation/README.md` |
| Backlog generation | `automation/README.md` (`scaffold-plan`) |

## Optional references

Create focused detail only when needed. Link it from the ticket and add it here.

| Area | Location |
|---|---|
| Architecture | `reference/architecture/` |
| API contracts | `reference/api/` |
| Data model/migrations | `reference/data-model/` |
| UX/design system | `reference/ux/` |
| Operations | `reference/runbooks/` |
| Decisions | `reference/decisions/` |
| Milestones | `reference/milestones/` |

Do not create new top-level documentation folders. Keep every file focused and under 500 lines.

## Sources of truth

- Rules: `Claude.md`
- Product scope: `docs/product-capability-spec.md`
- Feature requirements: the ticket file under `work/`
- Test policy: `testing/`
- Automation policy: `automation/`
- History: `work/archived/`
