from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN

# ---------------- Trash and recovery (F070) ----------------
# One index over every soft-deleted kind. The row says what it was, where it came from, who
# deleted it and how long is left; the state column says whether it can come back and why not.

ENTRIES = [
    ("grid", "Sheet", "Cutover plan", "Northfield Delivery / Migration", "CW", 255, "4 minutes ago",
     "30 days left", "Restorable", "success", "40 rows", True),
    ("doc", "Document", "Vendor security assessment", "Documents / Procurement", "AD", 210, "2 hours ago",
     "Legal hold", "Held", "warning", "Case 2026-14", False),
    ("grid", "Row", "Migrate identity provider", "Cutover plan / In progress", "MW", 120, "Yesterday",
     "29 days left", "Restorable", "success", "—", False),
    ("layers", "Folder", "Procurement", "Northfield Delivery", "PR", 30, "Yesterday",
     "29 days left", "Restorable", "success", "3 sheets", False),
    ("grid", "Sheet", "Vendor scorecard", "Northfield Delivery / Procurement", "PR", 30, "Yesterday",
     "29 days left", "Blocked", "danger", "Parent deleted", False),
    ("panel", "View", "At risk this week", "Cutover plan", "SO", 70, "3 days ago",
     "27 days left", "Restorable", "success", "—", False),
    ("chart", "Dashboard", "Programme status", "Northfield Delivery", "AD", 210, "6 days ago",
     "24 days left", "Restorable", "success", "6 widgets", False),
    ("doc", "File", "cutover-runbook-v4.pdf", "Cutover plan / Attachments", "MW", 120, "11 days ago",
     "19 days left", "Restorable", "success", "2.4 MB", False),
    ("chart", "Report", "Vendor spend by quarter", "Reports", "SO", 70, "28 days ago",
     "2 days left", "Expiring", "warning", "—", False),
]


def row(ic, kind, title, where, ini, hue, when, left, state, tone, detail, sel):
    mono = "font-family:'JetBrains Mono',ui-monospace,monospace;font-variant-numeric:tabular-nums;"
    blocked = state == "Blocked"
    return f'''<div style="display:flex;align-items:center;height:44px;padding:0 var(--space-4);gap:var(--space-3);
      border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);
      background:{"var(--bg-selected)" if sel else "transparent"};">
      <span style="width:16px;height:16px;border-radius:var(--radius-sm);border:1.5px solid var(--{"brand" if sel else "border-strong"});
        background:{"var(--brand)" if sel else "transparent"};display:inline-flex;align-items:center;
        justify-content:center;flex:none;">{icon("check",11,"#fff","2.4") if sel else ""}</span>
      <span style="width:20px;flex:none;color:var(--text-tertiary);">{icon(ic,17)}</span>
      <span style="width:78px;flex:none;color:var(--text-tertiary);font-size:var(--text-xs);
        font-weight:600;letter-spacing:.03em;text-transform:uppercase;">{kind}</span>
      <span style="flex:1.4;min-width:0;font-weight:600;overflow:hidden;text-overflow:ellipsis;
        white-space:nowrap;">{title}</span>
      <span style="flex:1.3;min-width:0;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;
        white-space:nowrap;">{where}</span>
      <span style="width:150px;flex:none;display:flex;align-items:center;gap:var(--space-2);">
        {avatar(ini,hue)}<span style="color:var(--text-secondary);font-size:var(--text-xs);">{when}</span></span>
      <span style="width:104px;flex:none;{mono}font-size:var(--text-xs);
        color:var(--{"warning-fg" if left in ("Legal hold","2 days left") else "text-secondary"});">{left}</span>
      <span style="width:110px;flex:none;display:flex;align-items:center;gap:6px;">
        {icon("warn",14,"var(--danger-fg)") if blocked else ""}{chip(state,tone)}</span>
      <span style="width:96px;flex:none;color:var(--text-tertiary);font-size:var(--text-xs);">{detail}</span>
      <span style="width:22px;flex:none;text-align:right;color:var(--text-tertiary);">{icon("dots",16)}</span>
    </div>'''


head = f'''<div style="display:flex;align-items:center;height:32px;padding:0 var(--space-4);gap:var(--space-3);
  background:var(--bg-sunken);border-bottom:1px solid var(--border-default);">
  <span style="width:16px;flex:none;"></span><span style="width:20px;flex:none;"></span>
  <span class="th" style="width:78px;flex:none;">Kind</span>
  <span class="th" style="flex:1.4;">Item</span>
  <span class="th" style="flex:1.3;">Where it was</span>
  <span class="th" style="width:150px;flex:none;">Deleted by</span>
  <span class="th" style="width:104px;flex:none;">Time left</span>
  <span class="th" style="width:110px;flex:none;">State</span>
  <span class="th" style="width:96px;flex:none;">Contents</span>
  <span style="width:22px;flex:none;"></span>
</div>'''

FILTERS = [("filter", "All kinds"), ("people", "Anyone"), ("calendar", "Last 30 days"), ("search", "Search trash")]
filters = "".join(f'''<div style="display:flex;align-items:center;gap:6px;height:var(--control-md);
  padding:0 var(--space-3);border:1px solid var(--border-default);border-radius:var(--radius-md);
  background:var(--bg-surface);font-size:var(--text-sm);color:var(--text-secondary);">
  {icon(ic,15)}{label}{icon("down",14)}</div>''' for ic, label in FILTERS)

stale = f'''<div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2) var(--space-4);
  background:var(--warning-bg);border-bottom:1px solid var(--warning-border);color:var(--warning-fg);
  font-size:var(--text-xs);">{icon("clock",15)}
  <span>Showing what we knew 3 minutes ago — the trash list is rebuilt from each item's own deletion,
    so it can lag. Restore and purge always check the live record.</span>
  <span style="margin-left:auto;font-weight:600;text-decoration:underline;">Refresh</span></div>'''

blocked_panel = f'''<div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
  <div style="display:flex;align-items:center;gap:8px;">{icon("warn",16,"var(--danger-fg)")}
    <span style="font-size:var(--text-base);font-weight:600;">Vendor scorecard is blocked</span></div>
  <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:20px;">
    Its folder <strong>Procurement</strong> is deleted too. Restoring the sheet on its own would leave it
    with nowhere to live, so it is refused rather than orphaned.</div>
  <button class="btn btn-secondary" style="justify-content:center;">Restore parent first</button>
</div>'''

purge_panel = f'''<div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
  <div style="display:flex;align-items:center;gap:8px;">{icon("shield",16,"var(--text-tertiary)")}
    <span style="font-size:var(--text-base);font-weight:600;">Purge now</span></div>
  <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:20px;">
    Destroys the item immediately and for good. Only a compliance administrator may run it, every purge
    is audited, and a legal hold refuses it — the hold beats the retention policy, always.</div>
  <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--warning-bg);
    border:1px solid var(--warning-border);color:var(--warning-fg);font-size:var(--text-xs);line-height:17px;">
    Vendor security assessment is held under <strong>Case 2026-14</strong>. Purge is unavailable until the
    hold is released; restore still works.</div>
  <button class="btn btn-secondary" style="justify-content:center;color:var(--text-tertiary);
    border-color:var(--border-subtle);">Purge selected</button>
</div>'''

retention_panel = f'''<div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
  <span class="th">Retention</span>
  {"".join(f'''<div style="display:flex;align-items:center;font-size:var(--text-sm);padding:5px 0;
    border-bottom:1px solid var(--border-subtle);"><span style="flex:1;">{n}</span>
    <span class="mono" style="color:var(--text-secondary);font-size:var(--text-xs);">{v}</span></div>'''
    for n, v in [("Sheets, rows, views", "30 days"), ("Documents and files", "30 days"),
                 ("Reports and dashboards", "30 days"), ("Under legal hold", "kept")])}
  <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
    At the end of the window the nightly sweep hands the item to the governance purge. Nothing here
    deletes anything on its own.</div>
</div>'''

body = f'''<div style="flex:1;display:flex;min-height:0;">
  <div style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-surface);">
    <div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-3) var(--space-4);
      border-bottom:1px solid var(--border-subtle);">{filters}
      <div style="margin-left:auto;display:flex;align-items:center;gap:var(--space-2);">
        <span style="font-size:var(--text-xs);color:var(--text-tertiary);">1 selected</span>
        {BTN("Restore","primary","check")}</div></div>
    {stale}
    {head}
    {"".join(row(*e) for e in ENTRIES)}
    <div style="padding:var(--space-3) var(--space-4);font-size:var(--text-xs);color:var(--text-tertiary);">
      9 of 142 items you can see · older items first drop off as their retention window ends</div>
  </div>
  <aside style="width:320px;flex:none;background:var(--bg-canvas);border-left:1px solid var(--border-subtle);
    padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
    {blocked_panel}{purge_panel}{retention_panel}
  </aside>
</div>'''

trash = shell("Sheets", "Trash", chip("142 items", "accent"),
              ["Everything", "Sheets & rows", "Documents & files", "Reports & dashboards"], "Everything",
              BTN("Rebuild index", "ghost", "clock") + BTN("Restore", "secondary", "check"),
              body, crumb="Northfield Delivery")
write('Trash.dc.html', page(trash, theme="light"))
print("Trash written")
