from _common import icon, chip, avatar, page, write
from _shell import topbar, rail
from board_timeline import shell, BTN

# ---------------- Announcements and in-app help (F073) ----------------
# Two surfaces over one frame: the what's-new panel hangs off the bell, the help drawer docks
# right against the screen the person is already on. The panel shows a targeted item, a plain
# product change and a dismissed item that keeps its date and has lost its dismiss control,
# because dismissal is permanent and the UI must not offer an undo that does not exist.

ITEMS = [
    ("Approval escalation", "action_required", "Action required", "danger",
     "Approvals now escalate to the workspace admin after 48 hours. Existing approval steps keep "
     "their current behaviour until you edit them.", "Enterprise · Admins", "2 hours ago",
     "Set an escalation target", False),
    ("Digital asset management", "change", "New", "accent",
     "Assets are now a module in your plan. Upload, tag and proof creative files against the same "
     "permissions as sheets.", "Enterprise · assets", "Yesterday",
     "What assets can hold", False),
    ("Faster grid scrolling", "info", "Improved", "success",
     "Grids over 20,000 rows now render on a virtualized surface. Nothing to turn on.", "Everyone",
     "3 days ago", "", False),
    ("Column formulas in views", "change", "New", "accent",
     "A saved view can carry its own computed column without changing the sheet beneath it.",
     "Team, Enterprise", "Dismissed 4 Mar", "Working with formulas", True),
]


def item(title, sev, label, tone, body, audience, when, link, dismissed):
    muted = "var(--text-tertiary)" if dismissed else "var(--text-primary)"
    ico = {"action_required": "warn", "change": "sparkle", "info": "check"}[sev]
    return f'''<div style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--border-subtle);
      display:flex;flex-direction:column;gap:6px;opacity:{".62" if dismissed else "1"};
      background:{"var(--bg-sunken)" if dismissed else "transparent"};">
      <div style="display:flex;align-items:center;gap:var(--space-2);">
        <span style="color:var(--{tone}-fg);display:inline-flex;">{icon(ico,15)}</span>
        {chip(label,tone)}
        <span class="mono" style="margin-left:auto;font-size:11px;color:var(--text-tertiary);">{when}</span>
        {'' if dismissed else f'<span style="color:var(--text-tertiary);display:inline-flex;">{icon("dots",15)}</span>'}
      </div>
      <div style="font-size:var(--text-sm);font-weight:600;color:{muted};line-height:19px;">{title}</div>
      <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:17px;
        display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{body}</div>
      <div style="display:flex;align-items:center;gap:var(--space-2);margin-top:2px;">
        <span style="display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--text-tertiary);">
          {icon("people",13)}{audience}</span>
        {f'<a href="#" style="margin-left:auto;font-size:var(--text-xs);font-weight:600;">{link}</a>' if link else ''}
      </div>
    </div>'''


panel = f'''<div class="card" style="position:absolute;top:52px;right:var(--space-5);width:380px;
  box-shadow:var(--shadow-3);overflow:hidden;z-index:4;display:flex;flex-direction:column;">
  <div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-3) var(--space-4);
    border-bottom:1px solid var(--border-default);">
    <span style="font-size:var(--text-sm);font-weight:700;">What&#39;s new</span>
    <span class="chip" style="background:var(--accent-bg);color:var(--accent-fg);
      border:1px solid var(--accent-border);">3 new</span>
    <span style="margin-left:auto;display:inline-flex;align-items:center;gap:6px;
      font-size:var(--text-xs);color:var(--text-secondary);">
      <span style="width:28px;height:16px;border-radius:var(--radius-full);background:var(--brand);
        position:relative;display:inline-block;">
        <span style="position:absolute;top:2px;left:14px;width:12px;height:12px;border-radius:var(--radius-full);
          background:var(--bg-surface);"></span></span>Show dismissed</span>
  </div>
  <div style="display:flex;flex-direction:column;max-height:452px;overflow:hidden;">
    {"".join(item(*i) for i in ITEMS)}
  </div>
  <div style="padding:var(--space-3) var(--space-4);display:flex;align-items:center;gap:var(--space-2);
    background:var(--bg-sunken);border-top:1px solid var(--border-subtle);">
    <span style="color:var(--text-tertiary);display:inline-flex;">{icon("shield",14)}</span>
    <span style="font-size:11px;color:var(--text-tertiary);">Nothing you read here is recorded.</span>
    <a href="#" style="margin-left:auto;font-size:var(--text-xs);font-weight:600;">Help centre</a>
  </div>
</div>'''

RELATED = [("Freezing and hiding columns", "Sheets"), ("Column types and validation", "Sheets"),
           ("Formulas across sheets", "Formulas"), ("Sharing a saved view", "Views")]

body_para = lambda t: f'<p style="margin:0 0 var(--space-3);font-size:var(--text-sm);line-height:21px;color:var(--text-secondary);">{t}</p>'

drawer = f'''<aside style="width:420px;flex:none;background:var(--bg-surface);
  border-left:1px solid var(--border-default);display:flex;flex-direction:column;
  box-shadow:var(--shadow-2);z-index:3;">
  <div style="display:flex;align-items:center;gap:var(--space-2);height:52px;flex:none;
    padding:0 var(--space-4);border-bottom:1px solid var(--border-subtle);">
    <span style="color:var(--accent-fg);display:inline-flex;">{icon("doc",17)}</span>
    <span style="font-size:var(--text-sm);font-weight:700;">Help</span>
    {chip("Sheet grid","accent")}
    <span class="mono" style="margin-left:auto;font-size:11px;padding:2px 6px;border-radius:var(--radius-sm);
      background:var(--bg-sunken);border:1px solid var(--border-default);color:var(--text-tertiary);">Esc</span>
  </div>
  <div style="flex:1;overflow:hidden;padding:var(--space-5) var(--space-4);">
    <h2 style="margin:0 0 6px;font-size:var(--text-lg);font-weight:700;letter-spacing:-.01em;">Working with columns</h2>
    <div style="display:flex;align-items:center;gap:var(--space-2);margin-bottom:var(--space-4);">
      <span class="mono" style="font-size:11px;color:var(--text-tertiary);">Updated 27 Feb · v4</span>
      {chip("Shown in English","warning")}
    </div>
    {body_para("A column carries one type for every row in the sheet. Changing the type rewrites the "
               "stored values, so OpsHub asks you to confirm and records the change in the sheet history.")}
    {body_para("Drag a column header to reorder it. The first column is the primary column and cannot "
               "be moved or hidden; it is what every reference, form and report uses to name a row.")}
    <div style="border-left:3px solid var(--accent-border);background:var(--accent-bg);
      padding:var(--space-3);border-radius:0 var(--radius-md) var(--radius-md) 0;margin-bottom:var(--space-5);">
      <span style="font-size:var(--text-xs);color:var(--accent-fg);line-height:18px;">
        Freezing is per person. Freezing a column does not change what anyone else sees.</span>
    </div>
    <div class="th" style="margin-bottom:var(--space-2);">More for this screen</div>
    {"".join(f'''<a href="#" style="display:flex;align-items:center;gap:var(--space-2);height:34px;
      border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);color:var(--text-primary);">
      {icon("doc",14,"var(--text-tertiary)")}{t}
      <span style="margin-left:auto;font-size:11px;color:var(--text-tertiary);">{s}</span>
      <span style="color:var(--text-tertiary);display:inline-flex;">{icon("chev",13)}</span></a>''' for t, s in RELATED)}
  </div>
  <div style="flex:none;padding:var(--space-3) var(--space-4);border-top:1px solid var(--border-subtle);
    display:flex;align-items:center;gap:var(--space-2);background:var(--bg-sunken);">
    {icon("search",15,"var(--text-tertiary)")}
    <span style="font-size:var(--text-xs);color:var(--text-tertiary);">Search all help articles</span>
    <span class="mono" style="margin-left:auto;font-size:11px;padding:2px 6px;border-radius:var(--radius-sm);
      background:var(--bg-surface);border:1px solid var(--border-default);color:var(--text-tertiary);">F1</span>
  </div>
</aside>'''

COLS = ["Task", "Owner", "Status", "Due"]
ROWS = [("Freeze the primary column", "PR", 30, "In progress", "accent", "12 Mar"),
        ("Add a validated status column", "AD", 210, "Review", "warning", "14 Mar"),
        ("Hide legacy estimate column", "MW", 120, "Blocked", "danger", "18 Mar"),
        ("Reorder delivery columns", "SO", 70, "Done", "success", "09 Mar"),
        ("Document the column types", "CW", 255, "Not started", "neutral", "22 Mar"),
        ("Backfill the owner column", "PR", 30, "In progress", "accent", "25 Mar"),
        ("Split the notes column", "AD", 210, "Not started", "neutral", "27 Mar"),
        ("Retire the duplicate due column", "MW", 120, "Review", "warning", "02 Apr")]

head = f'''<div style="display:flex;height:32px;background:var(--bg-sunken);
  border-bottom:1px solid var(--border-default);">
  <div class="th" style="width:44px;flex:none;"></div>
  <div class="th" style="flex:2;display:flex;align-items:center;padding:0 var(--space-3);">Task</div>
  <div class="th" style="width:130px;flex:none;display:flex;align-items:center;">Owner</div>
  <div class="th" style="width:130px;flex:none;display:flex;align-items:center;">Status</div>
  <div class="th" style="width:100px;flex:none;display:flex;align-items:center;">Due</div>
</div>'''

grid = head + "".join(f'''<div style="display:flex;height:var(--row-h);border-bottom:1px solid var(--border-subtle);
  font-size:var(--text-sm);background:{"var(--bg-selected)" if n == 1 else "transparent"};">
  <div class="mono" style="width:44px;flex:none;display:flex;align-items:center;justify-content:center;
    font-size:11px;color:var(--text-tertiary);border-right:1px solid var(--border-subtle);">{n}</div>
  <div style="flex:2;display:flex;align-items:center;padding:0 var(--space-3);font-weight:500;">{t}</div>
  <div style="width:130px;flex:none;display:flex;align-items:center;gap:6px;">{avatar(i,h)}
    <span style="color:var(--text-secondary);font-size:var(--text-xs);">{i}</span></div>
  <div style="width:130px;flex:none;display:flex;align-items:center;">{chip(st,tone)}</div>
  <div class="mono" style="width:100px;flex:none;display:flex;align-items:center;font-size:var(--text-xs);
    color:var(--text-secondary);">{due}</div>
</div>''' for n, (t, i, h, st, tone, due) in enumerate(ROWS, start=1))

content = f'''<div style="flex:1;display:flex;min-width:0;position:relative;">
  <div style="flex:1;min-width:0;display:flex;flex-direction:column;background:var(--bg-surface);
    overflow:hidden;">{grid}</div>
  {drawer}
  {panel}
</div>'''

board = shell("Sheets", "Cutover plan", chip("Grid view", "accent"),
              ["Grid", "Board", "Timeline", "Calendar", "Cards"], "Grid",
              BTN("Filter", "ghost", "filter") + BTN("Sort", "ghost", "sort")
              + BTN("Help", "secondary", "doc") + BTN("New row", "primary", "plus"),
              content)

write('Announcements.dc.html', page(board, theme="light"))
print("Announcements written")
