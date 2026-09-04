from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
import _charts as ch

def field(label, value, hint="", w="100%"):
    return f'''<div style="display:flex;flex-direction:column;gap:6px;width:{w};">
      <span class="th">{label}</span>
      <div style="height:var(--control-md);display:flex;align-items:center;padding:0 var(--space-3);
        border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--bg-surface);
        font-size:var(--text-sm);color:var(--text-primary);">{value}
        <span style="margin-left:auto;color:var(--text-tertiary);">{icon("down",15)}</span></div>
      {f'<span style="font-size:var(--text-xs);color:var(--text-tertiary);">{hint}</span>' if hint else ''}</div>'''

# ---------------- Workflow builder ----------------
def node(x,y,kind,title,sub,ic,tone,selected=False):
    ring = "box-shadow:0 0 0 2px var(--brand), var(--shadow-2);" if selected else "box-shadow:var(--shadow-1);"
    return f'''<div style="position:absolute;left:{x}px;top:{y}px;width:236px;background:var(--bg-surface);
      border:1px solid var(--border-default);border-radius:var(--radius-lg);{ring}overflow:hidden;">
      <div style="display:flex;align-items:center;gap:8px;padding:8px var(--space-3);
        background:var(--{tone}-bg);border-bottom:1px solid var(--{tone}-border);color:var(--{tone}-fg);">
        {icon(ic,15)}<span style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;">{kind}</span>
      </div>
      <div style="padding:var(--space-3);">
        <div style="font-size:var(--text-sm);font-weight:600;">{title}</div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:3px;line-height:16px;">{sub}</div>
      </div></div>'''

def connector(x,y,w=0,h=40,label=""):
    arrow = ('<path d="M-3,%d L1,%d L5,%d" stroke="var(--border-strong)" stroke-width="1.5" '
             'stroke-linecap="round" stroke-linejoin="round"/>' % (h-9, h-3, h-9)) if not w else ""
    lbl = ('<div style="position:absolute;left:%dpx;top:%dpx;font-size:11px;font-weight:600;'
           'color:var(--text-tertiary);background:var(--bg-canvas);padding:0 6px;">%s</div>'
           % (x+8, y+h/2-9, label)) if label else ""
    return ('<svg style="position:absolute;left:%dpx;top:%dpx;" width="%d" height="%d" fill="none">'
            '<path d="M1,0 L1,%d" stroke="var(--border-strong)" stroke-width="1.5" stroke-linecap="round"/>'
            '%s</svg>%s' % (x, y, max(w,2)+2, h+2, h-8, arrow, lbl))

palette = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-md);
  padding:0 var(--space-2);border-radius:var(--radius-md);border:1px solid var(--border-subtle);
  background:var(--bg-surface);font-size:var(--text-sm);color:var(--text-secondary);">{icon(i,15)}{n}</div>'''
  for i,n in [("bell","Send notification"),("user","Assign owner"),("check","Set cell value"),
              ("shield","Request approval"),("doc","Create row"),("flow","Call webhook"),("clock","Wait")])

wf_canvas = f'''<div style="position:relative;flex:1;background:var(--bg-canvas);
  background-image:radial-gradient(var(--border-default) 1px, transparent 1px);background-size:22px 22px;
  overflow:hidden;">
  {node(300,40,"Trigger","Row status changes","Sheet · Cutover plan","flow","accent")}
  {connector(418,148)}
  {node(300,190,"Condition","Status is Blocked","and Health is At risk","warn","warning",True)}
  {connector(418,298)}
  {node(180,340,"Action","Notify programme lead","Slack · #northfield-delivery","bell","success")}
  {node(560,340,"Action","Request approval","Approver: Priya Raman · 24h SLA","shield","success")}
  <svg style="position:absolute;left:298px;top:298px;" width="384" height="44" fill="none">
    <path d="M120,0 L120,20 Q120,28 112,28 L8,28 Q0,28 0,36 L0,42" stroke="var(--border-strong)" stroke-width="1.5"/>
    <path d="M120,0 L120,20 Q120,28 128,28 L372,28 Q380,28 380,36 L380,42" stroke="var(--border-strong)" stroke-width="1.5"/>
  </svg>
  <div style="position:absolute;left:340px;top:318px;font-size:11px;font-weight:600;color:var(--text-tertiary);
    background:var(--bg-canvas);padding:0 6px;">true</div>
  <div style="position:absolute;left:640px;top:318px;font-size:11px;font-weight:600;color:var(--text-tertiary);
    background:var(--bg-canvas);padding:0 6px;">also</div>
  <div style="position:absolute;right:var(--space-5);bottom:var(--space-5);display:flex;gap:6px;
    background:var(--bg-surface);border:1px solid var(--border-default);border-radius:var(--radius-md);
    padding:4px;box-shadow:var(--shadow-1);">
    <span style="padding:4px 8px;color:var(--text-secondary);">−</span>
    <span class="mono" style="padding:4px 4px;font-size:var(--text-xs);color:var(--text-secondary);">100%</span>
    <span style="padding:4px 8px;color:var(--text-secondary);">+</span></div>
</div>'''

wf = topbar("") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("Automation")}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;">
      <div style="padding:var(--space-5) var(--space-5) 0;background:var(--bg-surface);">
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">Escalate blocked work</h1>
          {chip("Draft","warning")}<span class="mono" style="font-size:var(--text-xs);color:var(--text-tertiary);">v4 · edited 12m ago</span>
        </div>
      </div>
      {toolbar(tabs(["Builder","Runs","Versions","Settings"],"Builder"),
        f'<button class="btn btn-ghost">{icon("clock",16)}Test run</button>'
        f'<button class="btn btn-secondary">Save draft</button>'
        f'<button class="btn btn-primary">{icon("check",16)}Publish</button>')}
      <div style="flex:1;display:flex;min-height:0;">
        <div style="width:232px;flex:none;border-right:1px solid var(--border-subtle);background:var(--bg-surface);
          padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-2);">
          <span class="th">Steps</span>{palette}
        </div>
        {wf_canvas}
        <aside style="width:300px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
          padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="color:var(--warning-fg);">{icon("warn",17)}</span>
            <span style="font-size:var(--text-base);font-weight:600;">Condition</span></div>
          {field("Column","Status")}
          {field("Operator","is any of")}
          {field("Value","Blocked, At risk")}
          {field("Combine","AND","All conditions must match")}
          <div style="margin-top:auto;padding:var(--space-3);border-radius:var(--radius-md);
            background:var(--accent-bg);border:1px solid var(--accent-border);font-size:var(--text-xs);
            color:var(--accent-fg);line-height:17px;">Runs are idempotent per row version. A retry after failure
            resumes at the failed step.</div>
        </aside>
      </div>
    </main>
  </div>'''
write('Workflow.dc.html', page(wf, theme="light"))

# ---------------- Workload ----------------
PEOPLE=[("Priya Raman","PR",30,"Delivery lead",[92,104,118,96,88,74]),
        ("Ana Duarte","AD",210,"Engineer",[80,86,92,110,124,96]),
        ("Marcus Webb","MW",120,"Data engineer",[64,72,88,132,140,120]),
        ("Sam Okafor","SO",70,"QA",[48,56,72,80,68,60]),
        ("Ines Moreau","IM",160,"Designer",[88,84,80,76,92,88]),
        ("Tom Alderly","TA",300,"Analyst",[36,44,52,48,40,32])]
WEEKS=["Mar 09","Mar 16","Mar 23","Mar 30","Apr 06","Apr 13"]

def heat(pct):
    if pct>115: tone,fg="--danger-bg","--danger-fg"
    elif pct>100: tone,fg="--warning-bg","--warning-fg"
    elif pct>=60: tone,fg="--success-bg","--success-fg"
    else: tone,fg="--bg-sunken","--text-tertiary"
    return f'''<div style="flex:1;height:44px;border-radius:var(--radius-sm);background:var({tone});
      border:1px solid var({fg});display:flex;align-items:center;justify-content:center;">
      <span class="mono" style="font-size:var(--text-xs);font-weight:600;color:var({fg});">{pct}%</span></div>'''

rows="".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) var(--space-5);
  border-bottom:1px solid var(--border-subtle);">
  <div style="width:210px;flex:none;display:flex;align-items:center;gap:var(--space-2);">
    {avatar(i,h)}<div><div style="font-size:var(--text-sm);font-weight:600;">{n}</div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);">{r}</div></div></div>
  <div style="flex:1;display:flex;gap:var(--space-2);">{"".join(heat(p) for p in ws)}</div>
  <div style="width:110px;flex:none;text-align:right;">{ch.spark(90,26,ws)}</div>
</div>''' for n,i,h,r,ws in PEOPLE)

wl = topbar("") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("Workload")}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;">
      <div style="padding:var(--space-5) var(--space-5) 0;background:var(--bg-surface);">
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">Workload</h1>
          {chip("3 conflicts","danger")}
        </div>
      </div>
      {toolbar(tabs(["Heatmap","Allocations","Time entries","Reconcile"],"Heatmap"),
        f'<button class="btn btn-ghost">{icon("calendar",16)}6 weeks</button>'
        f'<button class="btn btn-ghost">{icon("filter",16)}Skill</button>'
        f'<button class="btn btn-secondary">{icon("doc",16)}Export</button>'
        f'<button class="btn btn-primary">{icon("sparkle",16)}Suggest balance</button>')}
      <div style="flex:1;display:flex;min-height:0;">
        <div style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-surface);">
          <div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) var(--space-5);
            background:var(--bg-sunken);border-bottom:1px solid var(--border-default);">
            <span class="th" style="width:210px;flex:none;">Resource</span>
            <div style="flex:1;display:flex;gap:var(--space-2);">
              {"".join(f'<span class="th" style="flex:1;text-align:center;">{w}</span>' for w in WEEKS)}</div>
            <span class="th" style="width:110px;flex:none;text-align:right;">Trend</span>
          </div>
          {rows}
          <div style="padding:var(--space-4) var(--space-5);display:flex;gap:var(--space-4);">
            {"".join(f'<span style="display:inline-flex;align-items:center;gap:6px;font-size:var(--text-xs);color:var(--text-secondary);"><span style="width:12px;height:12px;border-radius:3px;background:var({b});border:1px solid var({f});"></span>{l}</span>' for l,b,f in [("Under 60%","--bg-sunken","--text-tertiary"),("Healthy","--success-bg","--success-fg"),("Over 100%","--warning-bg","--warning-fg"),("Over 115%","--danger-bg","--danger-fg")])}
          </div>
        </div>
        <aside style="width:320px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
          padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
          <span class="th">Conflicts</span>
          {"".join(f'''<div style="border:1px solid var(--{t}-border);background:var(--{t}-bg);
            border-radius:var(--radius-md);padding:var(--space-3);">
            <div style="display:flex;align-items:center;gap:8px;color:var(--{t}-fg);">{icon("warn",15)}
              <span style="font-size:var(--text-sm);font-weight:600;">{n}</span></div>
            <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:6px;line-height:17px;">{d}</div>
            <div style="display:flex;gap:6px;margin-top:var(--space-3);">
              <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Shift 1 week</button>
              <button class="btn btn-ghost" style="height:var(--control-sm);font-size:var(--text-xs);">Reassign</button></div>
          </div>''' for n,d,t in [
            ("Marcus Webb · Mar 30","140% for 2 weeks. Load test and rollback drill overlap.","danger"),
            ("Ana Duarte · Apr 06","124% for 1 week. Accessibility audit overlaps cutover.","warning"),
            ("Tom Alderly · Mar 09","36% for 3 weeks. Capacity available for reassignment.","warning")])}
        </aside>
      </div>
    </main>
  </div>'''
write('Workload.dc.html', page(wl, theme="dark"))
print("Workflow + Workload written")
