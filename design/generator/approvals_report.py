from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
import _charts as ch

# ---------------- Approvals inbox ----------------
APPR=[("Cutover window · 28 March","Change request","Priya Raman","PR",30,"2h left","danger","Marcus Webb","MW",120),
      ("Vendor: Acme Analytics","Vendor intake","Sam Okafor","SO",70,"1d left","warning","Priya Raman","PR",30),
      ("Q2 capacity plan","Budget","Ana Duarte","AD",210,"3d left","accent","Priya Raman","PR",30),
      ("Data retention policy change","Governance","Marcus Webb","MW",120,"5d left","accent","Priya Raman","PR",30)]
items="".join(f'''<div class="card" style="padding:var(--space-4);display:flex;align-items:center;gap:var(--space-4);
  {"box-shadow:0 0 0 2px var(--brand), var(--shadow-1);" if k==0 else ""}">
  <div style="flex:1;min-width:0;">
    <div style="display:flex;align-items:center;gap:8px;">
      <span style="font-size:var(--text-base);font-weight:600;">{t}</span>{chip(kind,"accent")}</div>
    <div style="display:flex;align-items:center;gap:8px;margin-top:6px;font-size:var(--text-xs);color:var(--text-secondary);">
      {avatar(ri,rh)}requested by {req}<span>·</span>step 2 of 3<span>·</span>
      <span style="color:var(--{urg}-fg);font-weight:600;">{due}</span></div>
  </div>
  <div style="display:flex;gap:var(--space-2);">
    <button class="btn btn-secondary">Request changes</button>
    <button class="btn btn-secondary" style="color:var(--danger-fg);border-color:var(--danger-border);">Reject</button>
    <button class="btn btn-primary">{icon("check",16)}Approve</button></div>
</div>''' for k,(t,kind,req,ri,rh,due,urg,app,ai,ah) in enumerate(APPR))

appr = shell("Automation","Approvals", chip("4 waiting on you","warning"),
  ["Waiting on me","Requested by me","All","Delegations"],"Waiting on me",
  BTN("Filter","ghost","filter")+BTN("Delegate","ghost","user")+BTN("Bulk approve","secondary","check"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-3);overflow:hidden;">{items}</div>
    <aside style="width:320px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
      <span class="th">Selected · Cutover window</span>
      <div style="display:flex;flex-direction:column;gap:var(--space-3);">
        {"".join(f'''<div style="display:flex;gap:var(--space-2);align-items:flex-start;">
          <span style="width:22px;height:22px;border-radius:99px;background:var(--{c}-bg);color:var(--{c}-fg);
            display:inline-flex;align-items:center;justify-content:center;flex:none;">{icon(ic,13)}</span>
          <div><div style="font-size:var(--text-sm);font-weight:600;">{n}</div>
          <div style="font-size:var(--text-xs);color:var(--text-tertiary);">{d}</div></div></div>'''
          for n,d,c,ic in [("Ana Duarte","Approved 14:02","success","check"),
                           ("You","Waiting since 15:10","warning","clock"),
                           ("Change board","Not started","neutral" if False else "accent","people")])}
      </div>
      <div style="height:1px;background:var(--border-subtle);"></div>
      <div><span class="th">Escalation</span>
        <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:19px;margin-top:6px;">
          Escalates to Priya Raman in <span class="mono" style="color:var(--danger-fg);font-weight:600;">1h 48m</span>
          if no decision is recorded.</div></div>
      <div style="margin-top:auto;"><div style="height:72px;border:1px solid var(--border-default);
        border-radius:var(--radius-md);padding:var(--space-3);font-size:var(--text-sm);color:var(--text-tertiary);">
        Decision comment (required to reject)…</div></div>
    </aside>
  </div>''', crumb="Northfield Delivery / Automation")
write('Approvals.dc.html', page(appr, theme="light"))

# ---------------- Report builder ----------------
src="".join(f'''<div style="display:flex;align-items:center;gap:8px;height:30px;padding:0 var(--space-2);
  border-radius:var(--radius-sm);font-size:var(--text-sm);color:var(--text-secondary);
  {"background:var(--bg-selected);color:var(--accent-fg);font-weight:600;" if a else ""}">{icon("grid",14)}{n}</div>'''
  for n,a in [("Cutover plan",True),("Vendor register",True),("Risk log",False),("Capacity plan",False),("Incidents",False)])
cols="".join(f'''<div style="display:flex;align-items:center;gap:8px;padding:6px var(--space-2);
  border:1px solid var(--border-subtle);border-radius:var(--radius-sm);background:var(--bg-surface);
  font-size:var(--text-xs);">{icon("dots",13)}{n}<span class="mono" style="margin-left:auto;color:var(--text-tertiary);">{t}</span></div>'''
  for n,t in [("Task","text"),("Status","select"),("Owner","person"),("Due","date"),("Effort","number"),("Phase","select")])

report = shell("Dashboards","Delivery status report", chip("Draft","warning"),
  ["Build","Preview","Schedule","Permissions"],"Build",
  BTN("Run","ghost","clock")+BTN("Save as view","ghost","layers")+BTN("Share","secondary","people")+BTN("Publish","primary","check"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:250px;flex:none;border-right:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
      <div><span class="th">Sources</span><div style="margin-top:8px;display:flex;flex-direction:column;gap:2px;">{src}</div></div>
      <div><span class="th">Columns</span><div style="margin-top:8px;display:flex;flex-direction:column;gap:6px;">{cols}</div></div>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-canvas);">
      <div style="padding:var(--space-4) var(--space-5);display:flex;gap:var(--space-2);flex-wrap:wrap;
        border-bottom:1px solid var(--border-subtle);background:var(--bg-surface);">
        {"".join(f'<span class="chip" style="background:var(--accent-bg);color:var(--accent-fg);border:1px solid var(--accent-border);height:26px;">{t}<span style="opacity:.6;">✕</span></span>' for t in ["Status is not Done","Due before 30 Apr","Owner in Delivery team"])}
        <span class="chip" style="background:var(--bg-sunken);color:var(--text-tertiary);border:1px dashed var(--border-strong);height:26px;">+ condition</span>
      </div>
      <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
        <div style="display:flex;gap:var(--space-4);">
          {"".join(f'''<div class="card" style="flex:1;padding:var(--space-4);"><span class="th">{l}</span>
            <div class="mono" style="font-size:var(--text-2xl);font-weight:600;margin-top:4px;">{v}</div></div>''' for l,v in [("Rows","218"),("Sources","2"),("Overdue","17"),("Owners","9")])}
        </div>
        <div class="card" style="flex:1;padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
          <div style="display:flex;align-items:center;gap:8px;"><span style="font-size:var(--text-sm);font-weight:600;">Preview</span>
            <span class="mono" style="font-size:11px;color:var(--text-tertiary);">first 6 of 218 rows</span></div>
          <div style="display:flex;background:var(--bg-sunken);height:30px;border-radius:var(--radius-sm);">
            {"".join(f'<div class="th" style="flex:{f};display:flex;align-items:center;padding:0 var(--space-3);">{n}</div>' for n,f in [("Task",3),("Source",2),("Status",1),("Owner",2),("Due",1)])}
          </div>
          {"".join(f'''<div style="display:flex;height:32px;align-items:center;border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);">
            <div style="flex:3;padding:0 var(--space-3);">{t}</div>
            <div style="flex:2;padding:0 var(--space-3);color:var(--text-secondary);">{s}</div>
            <div style="flex:1;padding:0 var(--space-3);">{chip(st,k)}</div>
            <div style="flex:2;padding:0 var(--space-3);color:var(--text-secondary);">{o}</div>
            <div class="mono" style="flex:1;padding:0 var(--space-3);color:var(--text-secondary);">{d}</div></div>'''
            for t,s,st,k,o,d in [("Data migration dry run","Cutover plan","Blocked","danger","Marcus Webb","Mar 18"),
                                 ("Acme Analytics review","Vendor register","Review","warning","Sam Okafor","Mar 20"),
                                 ("Permission model sign-off","Cutover plan","Review","warning","Priya Raman","Mar 25"),
                                 ("Load test 100k rows","Cutover plan","Not started","accent","Marcus Webb","Apr 02"),
                                 ("Beacon Data review","Vendor register","In progress","accent","Sam Okafor","Apr 07"),
                                 ("Customer comms plan","Cutover plan","Review","warning","Sam Okafor","Apr 11")])}
        </div>
      </div>
    </div>
  </div>''', crumb="Northfield Delivery / Reports")
write('Report.dc.html', page(report, theme="dark"))
print("Approvals + Report written")
