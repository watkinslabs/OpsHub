from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
import _charts as ch

# ---------------- AI insights + proposal diff ----------------
INS=[("Migration programme will miss 30 April","risk","danger",
      "Three tasks on the critical path slipped this week and the remaining float is 2 days.",
      ["Data migration dry run · Blocked since Mar 12","Cutover runbook draft · +4d","Load test 100k rows · unassigned"]),
     ("Marcus Webb is over capacity for 3 weeks","risk","warning",
      "Allocations total 140% from 30 March while two tasks overlap.",["Load test 100k rows","Rollback drill"]),
     ("Approval time improved 38% this quarter","trend","success",
      "Median decision time fell from 14h to 6h after the escalation rule shipped.",["Approvals · 214 decisions"])]
cards="".join(f'''<div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);
  {"box-shadow:0 0 0 2px var(--brand), var(--shadow-1);" if k==0 else ""}">
  <div style="display:flex;align-items:flex-start;gap:var(--space-3);">
    <span style="width:26px;height:26px;border-radius:var(--radius-md);background:var(--{c}-bg);color:var(--{c}-fg);
      display:inline-flex;align-items:center;justify-content:center;flex:none;">{icon("warn" if c!="success" else "chart",15)}</span>
    <div style="flex:1;"><div style="font-size:var(--text-base);font-weight:600;line-height:21px;">{t}</div>
      <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:19px;margin-top:4px;">{d}</div></div>
    {chip(kind,c)}</div>
  <div style="padding:var(--space-3);background:var(--bg-sunken);border-radius:var(--radius-md);
    display:flex;flex-direction:column;gap:5px;">
    <span class="th">Evidence · {len(ev)} records</span>
    {"".join(f'<div style="font-size:var(--text-xs);color:var(--text-secondary);display:flex;align-items:center;gap:6px;">{icon("doc",13)}<a href="#">{e}</a></div>' for e in ev)}
  </div>
  <div style="display:flex;gap:8px;">
    <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Dismiss</button>
    <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Explain</button>
    <button class="btn btn-primary" style="height:var(--control-sm);font-size:var(--text-xs);">Review action</button></div>
</div>''' for k,(t,kind,c,d,ev) in enumerate(INS))

diff = f'''<aside style="width:360px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
  display:flex;flex-direction:column;">
  <div style="padding:var(--space-4);border-bottom:1px solid var(--border-subtle);">
    <div style="font-size:var(--text-base);font-weight:600;">Proposed action</div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:3px;">
      Nothing changes until you approve</div></div>
  <div style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
    <span class="th">Reschedule 2 tasks · Cutover plan</span>
    {"".join(f'''<div style="border:1px solid var(--border-subtle);border-radius:var(--radius-md);overflow:hidden;">
      <div style="padding:8px var(--space-3);background:var(--bg-sunken);font-size:var(--text-xs);font-weight:600;">{r}</div>
      <div style="display:flex;font-size:var(--text-sm);">
        <div style="flex:1;padding:8px var(--space-3);background:var(--danger-bg);color:var(--danger-fg);">
          <div class="mono" style="font-size:11px;">− {a}</div></div>
        <div style="flex:1;padding:8px var(--space-3);background:var(--success-bg);color:var(--success-fg);">
          <div class="mono" style="font-size:11px;">+ {b}</div></div></div></div>'''
      for r,a,b in [("Load test 100k rows · Due","Apr 02","Apr 09"),("Rollback drill · Due","Apr 09","Apr 16")])}
    <div style="padding:var(--space-3);background:var(--accent-bg);border:1px solid var(--accent-border);
      border-radius:var(--radius-md);font-size:var(--text-xs);color:var(--accent-fg);line-height:17px;">
      Reads used only records you can access. This proposal touches 2 rows in 1 sheet and emits 2 audit events.</div>
  </div>
  <div style="margin-top:auto;padding:var(--space-4);border-top:1px solid var(--border-subtle);display:flex;gap:8px;">
    <button class="btn btn-secondary" style="flex:1;justify-content:center;">Reject</button>
    <button class="btn btn-primary" style="flex:1;justify-content:center;">{icon("check",16)}Apply</button></div>
</aside>'''

ai = shell("Dashboards","Insights", chip("6 new","accent"),
  ["Risks","Trends","Actions","Settings"],"Risks",
  BTN("Scope: Programme","ghost","layers")+BTN("Rescan","ghost","clock")+BTN("AI settings","secondary","cog"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-3);overflow:hidden;">{cards}</div>
    {diff}
  </div>''', crumb="Northfield Delivery")
write('Insights.dc.html', page(ai, theme="light"))

# ---------------- Mobile ----------------
def phone(title, body, dark=False):
    return f'''<div style="width:390px;height:780px;border-radius:32px;border:1px solid var(--border-strong);
      background:var(--bg-canvas);box-shadow:var(--shadow-3);overflow:hidden;display:flex;flex-direction:column;">
      <div style="height:52px;flex:none;display:flex;align-items:center;gap:var(--space-3);padding:0 var(--space-4);
        background:var(--bg-surface);border-bottom:1px solid var(--border-subtle);">
        <span style="width:26px;height:26px;border-radius:8px;background:var(--brand);display:inline-flex;
          align-items:center;justify-content:center;">{icon("layers",16,"#fff","2")}</span>
        <span style="font-size:var(--text-base);font-weight:700;">{title}</span>
        <span style="margin-left:auto;color:var(--text-secondary);">{icon("bell",19)}</span>{avatar("CW",255)}</div>
      {body}
      <div style="height:60px;flex:none;display:flex;border-top:1px solid var(--border-subtle);
        background:var(--bg-surface);">
        {"".join(f'''<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;
          color:var(--{"accent-fg" if a else "text-tertiary"});">{icon(i,20)}
          <span style="font-size:10px;font-weight:{600 if a else 500};">{n}</span></div>'''
          for i,n,a in [("grid","Work",True),("bell","Inbox",False),("plus","Add",False),("chart","Reports",False),("user","Me",False)])}
      </div></div>'''

mobile_body = f'''<div style="flex:1;overflow:hidden;padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
  <div style="display:flex;gap:8px;">
    {"".join(f'<span class="chip" style="height:30px;background:var(--{"accent-bg" if a else "bg-sunken"});color:var(--{"accent-fg" if a else "text-secondary"});border:1px solid var(--{"accent-border" if a else "border-subtle"});">{n}</span>' for n,a in [("My work",True),("Due soon",False),("Approvals",False)])}
  </div>
  {"".join(f'''<div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-2);">
    <div style="font-size:var(--text-base);font-weight:600;line-height:21px;">{t}</div>
    <div style="display:flex;align-items:center;gap:8px;">{chip(s,k)}
      <span class="mono" style="margin-left:auto;font-size:var(--text-xs);color:var(--{u}-fg);">{d}</span></div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);">{sheet}</div>
  </div>''' for t,s,k,d,u,sheet in [
    ("Data migration dry run","Blocked","danger","Overdue 2d","danger","Cutover plan"),
    ("Cutover runbook draft","In progress","accent","Due Mar 21","warning","Cutover plan"),
    ("Permission model sign-off","Review","warning","Due Mar 25","text-secondary" if False else "accent","Cutover plan"),
    ("Accessibility audit","In progress","accent","Due Apr 04","accent","Cutover plan")])}
  <div style="margin-top:auto;display:flex;align-items:center;justify-content:center;gap:8px;
    padding:var(--space-3);font-size:var(--text-xs);color:var(--text-tertiary);">
    {icon("check",14)}Offline submissions queue and sync when you reconnect</div>
</div>'''

mob = f'''<div style="flex:1;display:flex;align-items:center;justify-content:center;gap:var(--space-9);
  background:var(--bg-canvas);padding:var(--space-7);">
  {phone("My work", mobile_body)}
  <div style="max-width:360px;display:flex;flex-direction:column;gap:var(--space-4);">
    <h1 style="margin:0;font-size:var(--text-2xl);font-weight:700;letter-spacing:-.02em;">Mobile</h1>
    <p style="margin:0;font-size:var(--text-sm);color:var(--text-secondary);line-height:22px;">
      The same permissions, the same rows. Mobile is a submission and review surface, not a second product:
      read your work, act on approvals, capture a form or a photo, and let queued submissions sync when the
      connection returns.</p>
    {"".join(f'''<div style="display:flex;gap:var(--space-3);align-items:flex-start;">
      <span style="width:26px;height:26px;border-radius:var(--radius-md);background:var(--accent-bg);
        color:var(--accent-fg);display:inline-flex;align-items:center;justify-content:center;flex:none;">{icon(i,15)}</span>
      <div><div style="font-size:var(--text-sm);font-weight:600;">{t}</div>
      <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:17px;margin-top:2px;">{d}</div></div></div>'''
      for i,t,d in [("check","44px hit targets","Every control meets the touch minimum from F062"),
                    ("bell","Push and deep links","A notification opens the exact row, not the home screen"),
                    ("shield","No offline co-editing","Deliberate: queued submissions only, so there is no merge to explain")])}
  </div>
</div>'''
write('Mobile.dc.html', page(mob, theme="light"))
print("Insights + Mobile written")
