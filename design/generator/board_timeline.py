from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
import _charts as ch

def shell(active, title, sub, tabnames, tabactive, right, body, crumb="Northfield Delivery / Migration"):
    return topbar("") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail(active)}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-canvas);">
      <div style="padding:var(--space-5) var(--space-5) 0;background:var(--bg-surface);">
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-bottom:6px;">{crumb}</div>
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">{title}</h1>
          {sub}
        </div>
      </div>
      {toolbar(tabs(tabnames, tabactive), right)}
      {body}
    </main>
  </div>'''

BTN = lambda t,k="secondary",i=None: f'<button class="btn btn-{k}">{icon(i,16) if i else ""}{t}</button>'

# ---------------- Board / Kanban ----------------
LANES=[("Backlog","--text-tertiary",[("Load test 100k rows","MW",120,"Apr 02","neutral","Not started"),
        ("Rollback drill","MW",120,"Apr 09","neutral","Not started"),("Go-live checklist","PR",30,"Apr 15","neutral","Not started")]),
       ("In progress","--accent-fg",[("Vendor security review","PR",30,"Mar 14","accent","In progress"),
        ("Cutover runbook draft","AD",210,"Mar 21","accent","In progress"),("Accessibility audit","AD",210,"Apr 04","accent","In progress")]),
       ("Review","--warning-fg",[("Permission model sign-off","PR",30,"Mar 25","warning","Review"),
        ("Customer comms plan","SO",70,"Apr 11","warning","Review")]),
       ("Blocked","--danger-fg",[("Data migration dry run","MW",120,"Mar 18","danger","Blocked")]),
       ("Done","--success-fg",[("Pilot tenant provisioning","SO",70,"Mar 08","success","Done")])]

def card(t,i,h,due,k,st):
    return f'''<div class="card" style="padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-2);
      box-shadow:var(--shadow-1);cursor:grab;">
      <div style="font-size:var(--text-sm);font-weight:600;line-height:19px;">{t}</div>
      <div style="display:flex;align-items:center;gap:8px;">{chip(st,k)}
        <span class="mono" style="margin-left:auto;font-size:11px;color:var(--text-tertiary);">{due}</span>{avatar(i,h)}</div>
    </div>'''

lanes="".join(f'''<div style="width:272px;flex:none;display:flex;flex-direction:column;gap:var(--space-3);">
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="width:8px;height:8px;border-radius:99px;background:var({c});"></span>
    <span style="font-size:var(--text-sm);font-weight:600;">{n}</span>
    <span class="mono" style="font-size:11px;color:var(--text-tertiary);">{len(cs)}</span>
    <span style="margin-left:auto;color:var(--text-tertiary);">{icon("plus",15)}</span></div>
  {"".join(card(*c) for c in cs)}
</div>''' for n,c,cs in LANES)

board = shell("Sheets","Cutover plan", chip("Board view","accent"),
  ["Grid","Board","Timeline","Calendar","Cards"],"Board",
  BTN("Group: Status","ghost","layers")+BTN("Filter","ghost","filter")+BTN("Share","secondary","people")+BTN("New row","primary","plus"),
  f'''<div style="flex:1;overflow:hidden;padding:var(--space-5);display:flex;gap:var(--space-4);
    background:var(--bg-canvas);">{lanes}</div>''')
write('Board.dc.html', page(board, theme="light"))

# ---------------- Timeline / Gantt ----------------
BARS=[("Discovery",0,140,"var(--brand)",1,"PR",30),("Vendor security review",10,90,ch.SER[1],2,"PR",30),
      ("Data migration dry run",60,120,ch.SER[3],2,"MW",120),("Build",150,220,"var(--brand)",1,"AD",210),
      ("Cutover runbook draft",165,120,ch.SER[1],2,"AD",210),("Pilot provisioning",160,80,ch.SER[4],2,"SO",70),
      ("Harden",380,180,"var(--brand)",1,"MW",120),("Load test",390,110,ch.SER[2],2,"MW",120),
      ("Launch",570,120,"var(--brand)",1,"PR",30)]
weeks=["Mar 02","Mar 09","Mar 16","Mar 23","Mar 30","Apr 06","Apr 13","Apr 20"]
rows="".join(f'''<div style="display:flex;align-items:center;height:38px;border-bottom:1px solid var(--border-subtle);">
  <div style="width:250px;flex:none;padding-left:{12 if lvl==1 else 30}px;display:flex;align-items:center;gap:8px;
    font-size:var(--text-sm);font-weight:{600 if lvl==1 else 400};color:var(--text-{'primary' if lvl==1 else 'secondary'});">
    {icon("chev",13) if lvl==1 else ""}{n}</div>
  <div style="flex:1;position:relative;height:100%;">
    <div style="position:absolute;left:{x}px;top:9px;width:{w}px;height:20px;border-radius:5px;background:{c};
      opacity:{1 if lvl==1 else .85};display:flex;align-items:center;padding:0 6px;gap:4px;">
      {avatar(i,h) if lvl==2 else ""}</div>
  </div></div>''' for n,x,w,c,lvl,i,h in BARS)

timeline = shell("Sheets","Cutover plan", chip("Timeline view","accent"),
  ["Grid","Board","Timeline","Calendar","Cards"],"Timeline",
  BTN("Zoom: Week","ghost","search")+BTN("Baseline","ghost","layers")+BTN("Critical path","ghost","warn")+BTN("Share","secondary","people"),
  f'''<div style="flex:1;display:flex;flex-direction:column;background:var(--bg-surface);overflow:hidden;">
    <div style="display:flex;height:34px;background:var(--bg-sunken);border-bottom:1px solid var(--border-default);">
      <div class="th" style="width:250px;flex:none;display:flex;align-items:center;padding:0 var(--space-3);">Task</div>
      <div style="flex:1;display:flex;">{"".join(f'<div class="th" style="flex:1;display:flex;align-items:center;justify-content:center;border-left:1px solid var(--border-subtle);">{w}</div>' for w in weeks)}</div>
    </div>
    {rows}
    <div style="padding:var(--space-4) var(--space-5);display:flex;gap:var(--space-4);">
      {"".join(f'<span style="display:inline-flex;align-items:center;gap:6px;font-size:var(--text-xs);color:var(--text-secondary);"><span style="width:14px;height:8px;border-radius:3px;background:{c};"></span>{n}</span>' for n,c in [("Phase","var(--brand)"),("On track",ch.SER[1]),("At risk",ch.SER[2]),("Blocked",ch.SER[3]),("Complete",ch.SER[4])])}
    </div>
  </div>''')
write('Timeline.dc.html', page(timeline, theme="dark"))
print("Board + Timeline written")
