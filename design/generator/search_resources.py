from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
import _charts as ch

# ---------------- Search ----------------
GROUPS=[("Sheets",[("Cutover plan","Northfield Delivery / Migration","grid"),
                   ("Cutover comms tracker","Northfield Delivery / Launch","grid")]),
        ("Rows",[("Cutover runbook draft","Cutover plan · In progress · Ana Duarte","doc"),
                 ("Cutover window approval","Approvals · Waiting on you","check"),
                 ("Pre-cutover freeze","Launch plan · Done","doc")]),
        ("Documents",[("Cutover runbook","Documents · edited 2m ago by Ana Duarte","doc")]),
        ("Comments",[("…we cannot open the cutover window until the vendor table passes…","Marcus Webb · 1h ago","people")])]
MARK = '<mark style="background:color-mix(in oklch, var(--brand) 22%, transparent);color:inherit;border-radius:3px;padding:0 2px;">Cutover</mark>'
def hit(t, sub, ic, sel):
    title = t.replace("Cutover", MARK)
    bg = "background:var(--bg-selected);" if sel else ""
    return ('<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) var(--space-3);'
            'border-radius:var(--radius-md);%s">'
            '<span style="color:var(--text-tertiary);">%s</span>'
            '<div style="flex:1;min-width:0;">'
            '<div style="font-size:var(--text-sm);font-weight:500;">%s</div>'
            '<div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;">%s</div></div>'
            '<span class="mono" style="font-size:11px;color:var(--text-tertiary);">&#8629;</span></div>'
            % (bg, icon(ic,16), title, sub))

res = ""
for gi,(g,rows) in enumerate(GROUPS):
    res += ('<div style="display:flex;flex-direction:column;gap:2px;">'
            '<div style="display:flex;align-items:center;gap:8px;padding:var(--space-2) var(--space-3);">'
            '<span class="th">%s</span>'
            '<span class="mono" style="font-size:11px;color:var(--text-tertiary);">%d</span></div>' % (g, len(rows)))
    for ri,(t,sub,ic) in enumerate(rows):
        res += hit(t, sub, ic, gi==1 and ri==0)
    res += "</div>"

search = f'''<div style="flex:1;display:flex;align-items:flex-start;justify-content:center;
  background:color-mix(in oklch, var(--text-primary) 30%, transparent);padding-top:96px;">
  <div style="width:720px;background:var(--bg-raised);border:1px solid var(--border-default);
    border-radius:var(--radius-lg);box-shadow:var(--shadow-3);overflow:hidden;display:flex;flex-direction:column;">
    <div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-4);
      border-bottom:1px solid var(--border-subtle);">
      <span style="color:var(--text-tertiary);">{icon("search",20)}</span>
      <span style="flex:1;font-size:var(--text-lg);">cutover<span style="border-left:1.5px solid var(--brand);margin-left:1px;">&nbsp;</span></span>
      <span class="mono" style="font-size:11px;padding:3px 7px;border-radius:4px;background:var(--bg-sunken);
        border:1px solid var(--border-default);color:var(--text-tertiary);">esc</span></div>
    <div style="display:flex;gap:8px;padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--border-subtle);">
      {"".join(f'<span class="chip" style="height:26px;background:var(--{"accent-bg" if a else "bg-sunken"});color:var(--{"accent-fg" if a else "text-secondary"});border:1px solid var(--{"accent-border" if a else "border-subtle"});">{n}</span>' for n,a in [("All",True),("Sheets",False),("Rows",False),("Documents",False),("Files",False),("Comments",False)])}
      <span style="margin-left:auto;font-size:var(--text-xs);color:var(--text-tertiary);display:flex;align-items:center;">
        permission-filtered · 9 of 214</span></div>
    <div style="padding:var(--space-2);display:flex;flex-direction:column;gap:var(--space-2);">{res}</div>
    <div style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--border-subtle);
      background:var(--bg-sunken);display:flex;align-items:center;gap:var(--space-4);
      font-size:var(--text-xs);color:var(--text-tertiary);">
      {"".join(f'<span style="display:inline-flex;align-items:center;gap:5px;"><span class="mono" style="padding:2px 5px;border-radius:3px;background:var(--bg-surface);border:1px solid var(--border-default);">{k}</span>{l}</span>' for k,l in [("↑↓","navigate"),("↵","open"),("⌘↵","new tab"),("⌘K","toggle")])}
      <span style="margin-left:auto;">Results you cannot read are never counted</span></div>
  </div>
</div>'''
write('Search.dc.html', page(topbar("") + search, theme="light"))

# ---------------- Resources / allocations ----------------
PEOPLE=[("Priya Raman","PR",30,"Delivery lead","London","Delivery",[("Migration programme",60),("Compliance 2026",30)]),
        ("Ana Duarte","AD",210,"Engineer","Lisbon","Platform",[("Migration programme",80),("Data platform",20)]),
        ("Marcus Webb","MW",120,"Data engineer","Manchester","Platform",[("Data platform",70),("Migration programme",70)]),
        ("Sam Okafor","SO",70,"QA","Leeds","Quality",[("Migration programme",50)]),
        ("Ines Moreau","IM",160,"Designer","Paris","Design",[("Mobile launch",60),("Partner portal",30)])]
def alloc_bar(allocs):
    total=sum(p for _,p in allocs)
    col = "--danger-emphasis" if total>100 else ("--warning-emphasis" if total>90 else "--success-emphasis")
    segs="".join(f'<div style="width:{p}%;height:100%;background:{c};"></div>' for (n,p),c in zip(allocs,["var(--brand)","#0e9aa7","#e0930f"]))
    return f'''<div style="flex:1;display:flex;align-items:center;gap:var(--space-3);">
      <div style="flex:1;height:20px;border-radius:var(--radius-sm);background:var(--bg-sunken);overflow:hidden;display:flex;">{segs}</div>
      <span class="mono" style="width:48px;text-align:right;font-size:var(--text-sm);font-weight:600;color:var({col});">{total}%</span></div>'''
prows="".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3) var(--space-5);
  border-bottom:1px solid var(--border-subtle);">
  <div style="width:230px;flex:none;display:flex;align-items:center;gap:var(--space-2);">{avatar(i,h)}
    <div><div style="font-size:var(--text-sm);font-weight:600;">{n}</div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);">{r} · {loc}</div></div></div>
  <div style="width:110px;flex:none;">{chip(team,"accent")}</div>
  {alloc_bar(al)}
  <div style="width:170px;flex:none;display:flex;gap:6px;justify-content:flex-end;">
    {"".join(f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-secondary);border:1px solid var(--border-subtle);">{p[:12]}</span>' for p,_ in al[:2])}</div>
</div>''' for n,i,h,r,loc,team,al in PEOPLE)

resources = shell("Workload","Resources", chip("5 of 41 shown","accent"),
  ["People","Allocations","Capacity","Skills"],"Allocations",
  BTN("Team: All","ghost","people")+BTN("Period: Q2","ghost","calendar")+BTN("Balance","secondary","sparkle")+BTN("Allocate","primary","plus"),
  f'''<div style="flex:1;display:flex;flex-direction:column;background:var(--bg-surface);overflow:hidden;">
    <div style="display:flex;padding:var(--space-2) var(--space-5);background:var(--bg-sunken);
      border-bottom:1px solid var(--border-default);gap:var(--space-3);">
      <span class="th" style="width:230px;flex:none;">Person</span>
      <span class="th" style="width:110px;flex:none;">Team</span>
      <span class="th" style="flex:1;">Allocation across projects</span>
      <span class="th" style="width:170px;flex:none;text-align:right;">Projects</span></div>
    {prows}
    <div style="padding:var(--space-5);display:flex;gap:var(--space-4);">
      <div class="card" style="flex:1;padding:var(--space-4);">
        <span class="th">Capacity by team</span>
        <div style="margin-top:var(--space-3);">{ch.bars(420,110,[92,104,78,88,61],labels=["Delivery","Platform","Quality","Design","Data"])}</div></div>
      <div class="card" style="width:300px;padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-2);">
        <span class="th">Unstaffed demand</span>
        {"".join(f'''<div style="display:flex;align-items:center;font-size:var(--text-sm);padding:5px 0;
          border-bottom:1px solid var(--border-subtle);">
          <span style="flex:1;">{n}</span><span class="mono" style="color:var(--warning-fg);font-weight:600;">{v}</span></div>'''
          for n,v in [("Data engineer","1.4 FTE"),("QA","0.8 FTE"),("Designer","0.5 FTE")])}
      </div>
    </div>
  </div>''', crumb="Northfield Delivery")
write('Resources.dc.html', page(resources, theme="light"))
print("Search + Resources written")
