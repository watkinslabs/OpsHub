from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs

COLS = [("",44),("Task",300),("Status",132),("Owner",150),("Due",110),("Effort",96),("Health",120),("Phase",140)]
ROWS = [
 ("Vendor security review","In progress","accent","Priya Raman","PR",30,"Mar 14","12h","On track","success","Discovery",0,False),
 ("Data migration dry run","Blocked","danger","Marcus Webb","MW",120,"Mar 18","24h","At risk","danger","Discovery",0,False),
 ("Cutover runbook draft","In progress","accent","Ana Duarte","AD",210,"Mar 21","8h","On track","success","Build",1,True),
 ("Pilot tenant provisioning","Done","success","Sam Okafor","SO",70,"Mar 08","16h","Complete","success","Build",1,False),
 ("Permission model sign-off","Review","warning","Priya Raman","PR",30,"Mar 25","6h","Watch","warning","Build",1,False),
 ("Load test 100k rows","Not started","neutral","Unassigned","–",0,"Apr 02","20h","Not started","neutral","Harden",2,False),
 ("Accessibility audit","In progress","accent","Ana Duarte","AD",210,"Apr 04","14h","On track","success","Harden",2,False),
 ("Rollback drill","Not started","neutral","Marcus Webb","MW",120,"Apr 09","10h","Not started","neutral","Harden",2,False),
 ("Customer comms plan","Review","warning","Sam Okafor","SO",70,"Apr 11","5h","Watch","warning","Launch",3,False),
 ("Go-live checklist","Not started","neutral","Priya Raman","PR",30,"Apr 15","9h","Not started","neutral","Launch",3,False),
]

def neutral(text):
    return (f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-secondary);'
            f'border:1px solid var(--border-subtle);">{text}</span>')

def status_chip(text, kind):
    return neutral(text) if kind=="neutral" else chip(text, kind)

def build():
    head = "".join(
        f'<div class="th" style="width:{w}px;flex:none;display:flex;align-items:center;gap:6px;'
        f'padding:0 var(--space-3);">{c}</div>' for c,w in COLS)
    body=[]
    for i,(task,st,stk,owner,ini,hue,due,eff,hl,hlk,phase,grp,sel) in enumerate(ROWS):
        bg = "var(--bg-selected)" if sel else ("var(--bg-surface)" if i%2==0 else "var(--bg-sunken)")
        mark = f'<span style="width:14px;height:14px;border-radius:4px;border:1.5px solid var({"--brand" if sel else "--border-strong"});background:{"var(--brand)" if sel else "transparent"};display:inline-flex;align-items:center;justify-content:center;">{icon("check",10,"#fff","3") if sel else ""}</span>'
        body.append(f'''<div style="display:flex;background:{bg};">
      <div class="cell" style="width:44px;flex:none;justify-content:center;">{mark}</div>
      <div class="cell" style="width:300px;flex:none;gap:8px;font-weight:500;">
        <span style="color:var(--text-tertiary);">{icon("doc",15)}</span>{task}</div>
      <div class="cell" style="width:132px;flex:none;">{status_chip(st,stk)}</div>
      <div class="cell" style="width:150px;flex:none;gap:8px;color:var(--text-secondary);">
        {avatar(ini,hue) if ini!="–" else '<span style="width:24px;height:24px;border-radius:99px;border:1px dashed var(--border-strong);display:inline-block;"></span>'}{owner}</div>
      <div class="cell mono" style="width:110px;flex:none;color:var(--text-secondary);">{due}</div>
      <div class="cell mono" style="width:96px;flex:none;color:var(--text-secondary);">{eff}</div>
      <div class="cell" style="width:120px;flex:none;">{status_chip(hl,hlk)}</div>
      <div class="cell" style="width:140px;flex:none;color:var(--text-secondary);">{phase}</div>
    </div>''')
    inspector = f'''
    <aside style="width:320px;flex:none;background:var(--bg-surface);border-left:1px solid var(--border-subtle);
      display:flex;flex-direction:column;">
      <div style="padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--border-subtle);
        display:flex;align-items:flex-start;gap:var(--space-3);">
        <div style="flex:1;">
          <div style="font-size:var(--text-lg);font-weight:600;line-height:24px;">Cutover runbook draft</div>
          <div class="mono" style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:4px;">ROW-2471 · v12</div>
        </div>
        <span style="color:var(--text-tertiary);">{icon("dots",18)}</span>
      </div>
      <div style="padding:var(--space-4) var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);">
        {"".join(f'''<div style="display:flex;flex-direction:column;gap:6px;">
          <span class="th">{k}</span><div style="font-size:var(--text-sm);">{v}</div></div>''' for k,v in
          [("Status", chip("In progress","accent")),
           ("Owner", f'<span style="display:inline-flex;align-items:center;gap:8px;">{avatar("AD",210)}Ana Duarte</span>'),
           ("Due", '<span class="mono">Mar 21, 2026</span>'),
           ("Predecessors", '<span style="color:var(--accent-fg);">2 tasks</span> · finish-to-start')])}
      </div>
      <div style="padding:0 var(--space-5);"><div style="height:1px;background:var(--border-subtle);"></div></div>
      <div style="padding:var(--space-4) var(--space-5);display:flex;flex-direction:column;gap:var(--space-3);">
        <span class="th">Activity</span>
        {"".join(f'''<div style="display:flex;gap:var(--space-2);">{avatar(i,h)}
          <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:18px;">
            <span style="color:var(--text-primary);font-weight:600;">{n}</span> {t}
            <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;">{w}</div></div></div>'''
          for i,h,n,t,w in [("PR",30,"Priya","set health to On track","2h ago"),
                            ("AD",210,"Ana","attached runbook-v3.pdf","yesterday")])}
      </div>
      <div style="margin-top:auto;padding:var(--space-4) var(--space-5);border-top:1px solid var(--border-subtle);
        display:flex;gap:var(--space-2);">
        <button class="btn btn-primary" style="flex:1;justify-content:center;">Save</button>
        <button class="btn btn-secondary">{icon("people",16)}Share</button>
      </div>
    </aside>'''
    left = (tabs(["Grid","Board","Timeline","Calendar","Cards"],"Grid"))
    right = (f'<button class="btn btn-ghost">{icon("filter",16)}Filter <span class="chip" style="background:var(--accent-bg);color:var(--accent-fg);">2</span></button>'
             f'<button class="btn btn-ghost">{icon("sort",16)}Sort</button>'
             f'<button class="btn btn-secondary">{icon("people",16)}Share</button>'
             f'<button class="btn btn-primary">{icon("plus",16)}New row</button>')
    body_html = f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("Sheets")}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-canvas);">
      <div style="padding:var(--space-5) var(--space-5) 0;background:var(--bg-surface);">
        <div style="display:flex;align-items:center;gap:var(--space-2);font-size:var(--text-xs);
          color:var(--text-tertiary);margin-bottom:6px;">
          Northfield Delivery <span>/</span> Migration <span>/</span>
          <span style="color:var(--text-secondary);">Cutover plan</span></div>
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">Cutover plan</h1>
          {chip("Shared with 6","accent")}
          <span style="display:flex;margin-left:4px;">{avatar("PR",30)}{avatar("AD",210)}{avatar("MW",120)}</span>
        </div>
      </div>
      {toolbar(left, right)}
      <div style="flex:1;overflow:hidden;display:flex;flex-direction:column;background:var(--bg-surface);">
        <div style="display:flex;background:var(--bg-sunken);border-bottom:1px solid var(--border-default);height:36px;">{head}</div>
        {"".join(body)}
        <div style="display:flex;align-items:center;gap:8px;height:var(--row-h);padding:0 var(--space-3);
          color:var(--text-tertiary);font-size:var(--text-sm);">{icon("plus",15)}Add row</div>
      </div>
      <div style="height:40px;flex:none;display:flex;align-items:center;gap:var(--space-4);padding:0 var(--space-5);
        border-top:1px solid var(--border-subtle);background:var(--bg-surface);font-size:var(--text-xs);
        color:var(--text-tertiary);">
        <span class="mono">10 of 1,284 rows</span><span>·</span><span>2 filters</span>
        <span style="margin-left:auto;display:inline-flex;align-items:center;gap:6px;">
          <span style="width:7px;height:7px;border-radius:99px;background:var(--success-emphasis);"></span>
          3 collaborators editing</span>
      </div>
    </main>
    {inspector}
  </div>'''
    return topbar("Cutover plan") + body_html

write('Main.dc.html', page(build(), theme="light"))
