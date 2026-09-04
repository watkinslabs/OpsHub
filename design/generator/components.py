from _common import icon, chip, avatar, page, write
import _charts as ch

def grp(title, note, body, span=1):
    return f'''<section style="grid-column:span {span};display:flex;flex-direction:column;gap:var(--space-3);">
      <div style="display:flex;align-items:baseline;gap:var(--space-2);">
        <h3 style="margin:0;font-size:var(--text-sm);font-weight:700;letter-spacing:.02em;text-transform:uppercase;
          color:var(--text-secondary);">{title}</h3>
        <span class="mono" style="font-size:10px;color:var(--text-tertiary);">{note}</span></div>
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);flex:1;">{body}</div>
    </section>'''

def row(*items, gap=8, align="center"):
    return f'<div style="display:flex;align-items:{align};gap:{gap}px;flex-wrap:wrap;">{"".join(items)}</div>'

def btn(label, kind="primary", size="md", ic=None, disabled=False):
    style = {"primary":"background:var(--brand);color:#fff;box-shadow:var(--shadow-1);",
             "secondary":"background:var(--bg-surface);color:var(--text-primary);border-color:var(--border-default);box-shadow:var(--shadow-1);",
             "ghost":"background:transparent;color:var(--text-secondary);",
             "danger":"background:var(--danger-emphasis);color:#fff;"}[kind]
    if disabled: style="background:var(--bg-active);color:var(--text-tertiary);"
    return (f'<button class="btn" style="{style}height:var(--control-{size});">'
            f'{icon(ic,16) if ic else ""}{label}</button>')

def textfield(label, value, state="default"):
    border = {"default":"var(--border-default)","focus":"var(--brand)","error":"var(--danger-emphasis)"}[state]
    ring = "box-shadow:0 0 0 3px color-mix(in oklch, var(--brand) 25%, transparent);" if state=="focus" else ""
    return f'''<div style="display:flex;flex-direction:column;gap:5px;flex:1;min-width:150px;">
      <span class="th">{label}</span>
      <div style="height:var(--control-md);display:flex;align-items:center;padding:0 var(--space-3);
        border:1px solid {border};border-radius:var(--radius-md);background:var(--bg-surface);
        font-size:var(--text-sm);{ring}">{value}</div>
      {f'<span style="font-size:11px;color:var(--danger-fg);">Required field</span>' if state=="error" else ''}</div>'''

def check(on, label, kind="box"):
    if kind=="box":
        mark = f'<span style="width:16px;height:16px;border-radius:4px;border:1.5px solid var({"--brand" if on else "--border-strong"});background:{"var(--brand)" if on else "transparent"};display:inline-flex;align-items:center;justify-content:center;flex:none;">{icon("check",11,"#fff","3") if on else ""}</span>'
    elif kind=="radio":
        mark = f'<span style="width:16px;height:16px;border-radius:99px;border:1.5px solid var({"--brand" if on else "--border-strong"});display:inline-flex;align-items:center;justify-content:center;flex:none;">{"<span style=\'width:8px;height:8px;border-radius:99px;background:var(--brand);\'></span>" if on else ""}</span>'
    else:
        mark = f'<span style="width:34px;height:19px;border-radius:99px;flex:none;background:{"var(--brand)" if on else "var(--border-strong)"};display:inline-flex;align-items:center;padding:2px;justify-content:{"flex-end" if on else "flex-start"};"><span style="width:15px;height:15px;border-radius:99px;background:#fff;"></span></span>'
    return f'<span style="display:inline-flex;align-items:center;gap:8px;font-size:var(--text-sm);">{mark}{label}</span>'

def alert(kind, title, msg):
    return f'''<div style="display:flex;gap:var(--space-3);padding:var(--space-3);border-radius:var(--radius-md);
      background:var(--{kind}-bg);border:1px solid var(--{kind}-border);">
      <span style="color:var(--{kind}-fg);flex:none;">{icon("warn" if kind in ("warning","danger") else "check",17)}</span>
      <div><div style="font-size:var(--text-sm);font-weight:600;color:var(--{kind}-fg);">{title}</div>
      <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:2px;line-height:16px;">{msg}</div></div></div>'''

def state_block(ic, title, msg, action):
    return f'''<div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:var(--space-4);
      text-align:center;border:1px dashed var(--border-default);border-radius:var(--radius-md);flex:1;">
      <span style="color:var(--text-tertiary);">{icon(ic,24)}</span>
      <div style="font-size:var(--text-sm);font-weight:600;">{title}</div>
      <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:16px;max-width:190px;">{msg}</div>
      {action}</div>'''

dialog = f'''<div style="width:100%;background:var(--bg-raised);border:1px solid var(--border-default);
  border-radius:var(--radius-lg);box-shadow:var(--shadow-3);overflow:hidden;">
  <div style="padding:var(--space-4) var(--space-4) var(--space-2);font-size:var(--text-lg);font-weight:600;">
    Delete 3 rows?</div>
  <div style="padding:0 var(--space-4);font-size:var(--text-sm);color:var(--text-secondary);line-height:19px;">
    Deleted rows move to the trash for 30 days. Linked rows in 2 other sheets keep their reference.</div>
  <div style="display:flex;justify-content:flex-end;gap:8px;padding:var(--space-4);">
    {btn("Cancel","secondary")}{btn("Delete","danger")}</div></div>'''

menu = f'''<div style="width:210px;background:var(--bg-raised);border:1px solid var(--border-default);
  border-radius:var(--radius-md);box-shadow:var(--shadow-2);padding:4px;">
  {"".join(f'<div style="display:flex;align-items:center;gap:10px;height:32px;padding:0 10px;border-radius:var(--radius-sm);font-size:var(--text-sm);{"background:var(--bg-hover);" if h else ""}color:var(--text-{"primary" if not d else "tertiary"});">{icon(i,16)}{n}</div>' for i,n,h,d in [("doc","Open in new tab",False,False),("people","Share",True,False),("check","Duplicate",False,False),("chart","Move to…",False,True)])}
  <div style="height:1px;background:var(--border-subtle);margin:4px 0;"></div>
  <div style="display:flex;align-items:center;gap:10px;height:32px;padding:0 10px;border-radius:var(--radius-sm);
    font-size:var(--text-sm);color:var(--danger-fg);">{icon("warn",16)}Delete</div></div>'''

toast = f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3) var(--space-4);
  border-radius:var(--radius-md);background:var(--bg-raised);border:1px solid var(--border-default);
  box-shadow:var(--shadow-3);">
  <span style="color:var(--success-fg);">{icon("check",18)}</span>
  <div style="font-size:var(--text-sm);">Workflow published</div>
  <span style="margin-left:auto;font-size:var(--text-sm);font-weight:600;color:var(--accent-fg);">Undo</span></div>'''

tabs_demo = f'''<div style="display:flex;gap:var(--space-5);border-bottom:1px solid var(--border-subtle);">
  {"".join(f'<div style="height:36px;display:flex;align-items:center;font-size:var(--text-sm);font-weight:{600 if o else 500};color:var({"--accent-fg" if o else "--text-secondary"});border-bottom:2px solid {"var(--brand)" if o else "transparent"};">{n}</div>' for n,o in [("Grid",True),("Board",False),("Timeline",False)])}</div>'''

body = f'''
  <div style="padding:var(--space-7);display:flex;flex-direction:column;gap:var(--space-5);
    background:var(--bg-canvas);height:100%;overflow:hidden;">
    <div>
      <h1 style="margin:0;font-size:var(--text-3xl);font-weight:700;letter-spacing:-.025em;">Component library</h1>
      <p style="margin:8px 0 0;font-size:var(--text-sm);color:var(--text-secondary);max-width:760px;">
        MUI v7 components under a custom OpsHub theme — the theme maps every token on the left sheet onto MUI's
        palette, typography, shape and spacing, so these are configured, not rebuilt. MUI X supplies Data Grid,
        Charts and Date Pickers. Only OpsHub-specific composites are hand-built.</p>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4, minmax(0,1fr));gap:var(--space-5);flex:1;min-height:0;">
      {grp("Buttons","MuiButton · 3 sizes",
        row(btn("Primary"),btn("Secondary","secondary"),btn("Ghost","ghost")) +
        row(btn("New row","primary","md","plus"),btn("Filter","secondary","md","filter"),btn("Delete","danger")) +
        row(btn("Small","secondary","sm"),btn("Large","secondary","lg"),btn("Disabled","primary",disabled=True)))}
      {grp("Inputs","MuiTextField · MuiSelect",
        row(textfield("Sheet name","Cutover plan")) +
        row(textfield("Owner","Ana Duarte","focus")) +
        row(textfield("Due date","","error")))}
      {grp("Selection","checkbox · radio · switch",
        row(check(True,"Include archived"),check(False,"Notify watchers")) +
        row(check(True,"Newest wins","radio"),check(False,"Manual","radio")) +
        row(check(True,"Compact density","switch")) +
        row(f'<div style="flex:1;height:6px;border-radius:99px;background:var(--bg-sunken);"><div style="width:62%;height:100%;border-radius:99px;background:var(--brand);"></div></div>'))}
      {grp("Status","MuiChip · badge",
        row(chip("In progress","accent"),chip("Done","success"),chip("At risk","warning"),chip("Blocked","danger")) +
        row(avatar("PR",30),avatar("AD",210),avatar("MW",120),
            f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-secondary);border:1px solid var(--border-subtle);">+4</span>') +
        row(f'<span class="mono" style="font-size:var(--text-xs);color:var(--text-tertiary);">v12 · ROW-2471</span>'))}
      {grp("Navigation","tabs · breadcrumb · menu", tabs_demo +
        f'<div style="display:flex;align-items:center;gap:6px;font-size:var(--text-xs);color:var(--text-tertiary);">Northfield <span>/</span> Migration <span>/</span> <span style="color:var(--text-secondary);">Cutover</span></div>' + menu)}
      {grp("Overlays","dialog · menu · toast", dialog + toast)}
      {grp("Feedback","MuiAlert · skeleton",
        alert("danger","Sync failed","Jira connector returned 429. Retrying in 4 minutes.") +
        alert("warning","Version conflict","This row changed while you were editing.") +
        alert("success","Approved","Priya Raman approved the cutover window.") +
        f'<div style="display:flex;flex-direction:column;gap:6px;">{"".join(f"<div style=\'height:10px;width:{w}%;border-radius:4px;background:var(--bg-active);\'></div>" for w in [92,74,84])}</div>')}
      {grp("States","every screen ships all five",
        f'<div style="display:flex;gap:var(--space-2);">' +
        state_block("doc","No rows yet","Create the first row or import a CSV.",btn("New row","primary","sm","plus")) +
        state_block("shield","No access","You need Viewer on this sheet.",btn("Request access","secondary","sm")) +
        '</div>' +
        f'''<div style="display:flex;gap:var(--space-3);padding:var(--space-3);border:1px solid var(--danger-border);
          background:var(--danger-bg);border-radius:var(--radius-md);align-items:center;">
          <span style="color:var(--danger-fg);">{icon("warn",18)}</span>
          <div style="flex:1;"><div style="font-size:var(--text-sm);font-weight:600;color:var(--danger-fg);">Could not load rows</div>
          <div class="mono" style="font-size:10px;color:var(--text-tertiary);margin-top:2px;">correlation_id 7c1a…9f2</div></div>
          {btn("Retry","secondary","sm")}</div>''')}
    </div>
  </div>'''
write('Components.dc.html', page(body, theme="light", size=(1440,1180)))
