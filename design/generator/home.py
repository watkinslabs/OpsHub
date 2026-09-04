from _common import icon, chip, avatar, page, write
from _shell import topbar, rail

# F069 Home and my work. One landing surface: five sections, each capped, each
# permission-filtered by the server. Ready and empty states are both drawn here.

FX = "display:flex;align-items:center;"
COL = "display:flex;flex-direction:column;"
TT = "color:var(--text-tertiary);"
D = lambda s, inner="": f'<div style="{s}">{inner}</div>'
SP = lambda s, inner="": f'<span style="{s}">{inner}</span>'
MONO = lambda t, s="": f'<span class="mono" style="font-size:11px;{s}">{t}</span>'
TH = lambda t, s="": f'<span class="th" style="{s}">{t}</span>'


def star(on):
    fill = "var(--warning-emphasis)" if on else "none"
    color = "var(--warning-emphasis)" if on else "var(--text-tertiary)"
    return (f'<svg width="16" height="16" viewBox="0 0 24 24" fill="{fill}" stroke="{color}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'<path d="M12 3.5l2.6 5.6 6 .8-4.4 4.2 1.1 6.1-5.3-2.9-5.3 2.9 1.1-6.1L3.4 9.9l6-.8z"/></svg>')


def card(title, count, body, action="", cap=""):
    head = D(f"{FX}gap:var(--space-2);height:32px;padding:0 var(--space-4);",
             D("font-size:var(--text-sm);font-weight:700;letter-spacing:-.01em;", title)
             + (MONO(count, TT) if count else "")
             + SP("margin-left:auto;display:flex;align-items:center;gap:var(--space-3);", cap + action))
    return D("background:var(--bg-surface);border:1px solid var(--border-subtle);border-radius:var(--radius-lg);"
             "box-shadow:var(--shadow-1);padding:var(--space-3) 0 var(--space-2);"
             f"{COL}gap:var(--space-1);", head + body)


def item(lead, name, meta, right="", muted=False):
    tone = "var(--text-secondary)" if muted else "var(--text-primary)"
    return D(f"{FX}gap:var(--space-3);height:44px;padding:0 var(--space-4);",
             SP("flex:none;display:inline-flex;" + TT, lead)
             + D("flex:1;min-width:0;" + COL,
                 D(f"font-size:var(--text-sm);font-weight:500;color:{tone};white-space:nowrap;"
                   "overflow:hidden;text-overflow:ellipsis;", name)
                 + D(f"font-size:var(--text-xs);{TT}margin-top:1px;", meta))
             + SP("flex:none;display:flex;align-items:center;gap:var(--space-2);", right))


def empty(title, body):
    return D(f"{COL}align-items:center;gap:6px;padding:var(--space-6) var(--space-5) var(--space-7);text-align:center;",
             SP("color:var(--success-fg);", icon("check", 22))
             + D("font-size:var(--text-sm);font-weight:600;", title)
             + D(f"font-size:var(--text-xs);{TT}max-width:250px;line-height:17px;", body))


# ---------------- Assigned to me (cap 10, 6 shown) ----------------
ASSIGNED = [("Cutover runbook draft", "Cutover plan", "Overdue by 2 days", "danger", "Mar 12"),
            ("Vendor security review", "Vendor reviews", "Overdue by 1 day", "danger", "Mar 13"),
            ("Permission model sign-off", "Cutover plan", "Due today", "warning", "Mar 14"),
            ("Accessibility audit", "Q1 Rollout", "Due in 2 days", "accent", "Mar 16"),
            ("Load test 100k rows", "Cutover plan", "Due in 4 days", "accent", "Mar 18"),
            ("Go-live checklist", "Q1 Rollout", "Due in 6 days", "accent", "Mar 20")]
assigned = "".join(item(icon("check", 16), n, s, chip(d, k) + MONO(due, TT))
                   for n, s, d, k, due in ASSIGNED)

# ---------------- Waiting on you (cap 10, 2 shown) ----------------
APPROVALS = [("Budget increase — Q1 Rollout", "Requested by Marta Weiss", "MW", 120, "2h ago"),
             ("Vendor contract — Northfield", "Requested by Priya Raman", "PR", 30, "yesterday")]
approvals = "".join(item(icon("shield", 16), n, s, avatar(i, h) + MONO(t, TT))
                    for n, s, i, h, t in APPROVALS)

# ---------------- Mentions (cap 10, empty: all_clear) ----------------
mentions = empty("You are caught up", "New mentions on comments and update requests land here as they arrive.")

# ---------------- Favourites (cap 20, 4 shown + 1 unavailable) ----------------
FAVES = [("Cutover plan", "Sheet · Q4 Migration"), ("Launch readiness", "Dashboard · Operations"),
         ("Vendor reviews", "Sheet · Operations"), ("Rollout timeline", "View · Q1 Rollout")]
faves = "".join(item(icon("doc", 16), n, s, star(True)) for n, s in FAVES)
faves += D(f"{FX}gap:6px;height:34px;padding:0 var(--space-4);font-size:var(--text-xs);color:var(--accent-fg);"
           "border-top:1px solid var(--border-subtle);margin-top:var(--space-1);",
           icon("warn", 14) + "Show unavailable (1)")

# ---------------- Recently visited (cap 12, 7 shown) ----------------
RECENTS = [("Cutover plan", "Sheet", "12 min ago"), ("Data migration dry run", "Row", "1h ago"),
           ("Rollout timeline", "View", "3h ago"), ("Operations", "Workspace", "yesterday"),
           ("Vendor reviews", "Sheet", "yesterday"), ("Launch readiness", "Dashboard", "2 days ago"),
           ("Runbooks", "Folder", "3 days ago")]
recents = "".join(item(icon("clock", 16), n, k, MONO(t, TT)) for n, k, t in RECENTS)

VIEW_ALL = ('<span style="font-size:var(--text-xs);font-weight:600;color:var(--accent-fg);">View all</span>')
CAP = lambda n: MONO(n, TT + "letter-spacing:.02em;")

col_a = D(f"{COL}gap:var(--space-4);flex:1;min-width:0;",
          card("Assigned to me", "", assigned, VIEW_ALL, CAP("6 of 24")))
col_b = D(f"{COL}gap:var(--space-4);flex:1;min-width:0;",
          card("Waiting on you", "", approvals, VIEW_ALL, CAP("2"))
          + card("Mentions", "", mentions, "", CAP("0")))
col_c = D(f"{COL}gap:var(--space-4);flex:1;min-width:0;",
          card("Favourites", "", faves, VIEW_ALL, CAP("4 of 5"))
          + card("Recently visited", "", recents, VIEW_ALL, CAP("7 of 12")))

header = D("padding:var(--space-5) var(--space-6) var(--space-4);background:var(--bg-surface);"
           "border-bottom:1px solid var(--border-subtle);",
           D(f"{FX}gap:var(--space-3);",
             D("min-width:0;",
               '<h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;'
               'letter-spacing:-.02em;">Good morning, Priya</h1>'
               + D(f"font-size:var(--text-sm);{TT}margin-top:2px;",
                   "Two items are overdue and two approvals are waiting on you."))
             + SP("margin-left:auto;display:flex;align-items:center;gap:var(--space-2);",
                  f'<button class="btn btn-secondary">{icon("filter", 16)}Assigned to me</button>'
                  f'<button class="btn btn-primary">{icon("plus", 16)}New sheet</button>')))

body = D("flex:1;min-height:0;padding:var(--space-5) var(--space-6);background:var(--bg-canvas);"
         "display:flex;gap:var(--space-4);align-items:flex-start;overflow:hidden;",
         col_a + col_b + col_c)

home = topbar("") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("")}
    <main style="flex:1;{COL}min-width:0;background:var(--bg-canvas);">
      {header}
      {body}
    </main>
  </div>'''

write('Home.dc.html', page(home, theme="light"))
print("Home written")
