from _common import icon, chip, avatar, page

def topbar(title, crumb=""):
    return f'''
  <header style="height:var(--topbar-h);flex:none;display:flex;align-items:center;gap:var(--space-4);
    padding:0 var(--space-4);background:var(--bg-surface);border-bottom:1px solid var(--border-subtle);
    box-shadow:var(--shadow-1);position:relative;z-index:2;">
    <div style="display:flex;align-items:center;gap:var(--space-2);width:calc(var(--rail-w) - 16px);flex:none;">
      <span style="width:28px;height:28px;border-radius:8px;background:var(--brand);display:inline-flex;
        align-items:center;justify-content:center;">{icon("layers",17,"#fff","2")}</span>
      <span style="font-size:var(--text-lg);font-weight:700;letter-spacing:-.02em;">OpsHub</span>
    </div>
    <div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-md);flex:1;max-width:520px;
      padding:0 var(--space-3);border-radius:var(--radius-md);background:var(--bg-sunken);
      border:1px solid var(--border-subtle);color:var(--text-tertiary);">
      {icon("search",16)}<span style="font-size:var(--text-sm);">Search sheets, rows, people</span>
      <span class="mono" style="margin-left:auto;font-size:11px;padding:2px 6px;border-radius:4px;
        background:var(--bg-surface);border:1px solid var(--border-default);">⌘K</span>
    </div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:var(--space-2);">
      <button class="btn btn-ghost" style="gap:6px;">{icon("sparkle",18)}<span>Ask</span></button>
      <span style="position:relative;display:inline-flex;padding:6px;color:var(--text-secondary);">{icon("bell",19)}
        <span style="position:absolute;top:4px;right:4px;width:7px;height:7px;border-radius:99px;
          background:var(--danger-emphasis);border:2px solid var(--bg-surface);"></span></span>
      {avatar("CW",255)}
    </div>
  </header>'''

def rail(active):
    items = [("grid","Sheets"),("chart","Dashboards"),("flow","Automation"),("people","Workload"),
             ("calendar","Calendar"),("doc","Documents"),("shield","Admin")]
    out = []
    for ic, label in items:
        on = " on" if label == active else ""
        out.append(f'<div class="rail-item{on}">{icon(ic,18)}<span>{label}</span></div>')
    return f'''
  <nav style="width:var(--rail-w);flex:none;background:var(--bg-surface);border-right:1px solid var(--border-subtle);
    display:flex;flex-direction:column;padding:var(--space-3);gap:var(--space-1);">
    <div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-lg);padding:0 var(--space-2);
      border:1px solid var(--border-default);border-radius:var(--radius-md);margin-bottom:var(--space-3);
      background:var(--bg-surface);box-shadow:var(--shadow-1);">
      <span style="width:22px;height:22px;border-radius:6px;background:var(--accent-bg);color:var(--accent-fg);
        font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">NF</span>
      <span style="font-size:var(--text-sm);font-weight:600;">Northfield Delivery</span>
      <span style="margin-left:auto;color:var(--text-tertiary);">{icon("down",16)}</span>
    </div>
    {''.join(out)}
    <div style="margin-top:auto;display:flex;flex-direction:column;gap:var(--space-1);">
      <div style="height:1px;background:var(--border-subtle);margin:var(--space-2) 0;"></div>
      <div class="rail-item">{icon("cog",18)}<span>Settings</span></div>
      <div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2);
        border-radius:var(--radius-md);background:var(--bg-sunken);">
        <span style="font-size:var(--text-xs);color:var(--text-secondary);">Storage</span>
        <span class="mono" style="margin-left:auto;font-size:11px;color:var(--text-tertiary);">62%</span>
      </div>
    </div>
  </nav>'''

def toolbar(left, right=""):
    return f'''<div style="height:52px;flex:none;display:flex;align-items:center;gap:var(--space-2);
      padding:0 var(--space-5);border-bottom:1px solid var(--border-subtle);background:var(--bg-surface);">
      {left}<div style="margin-left:auto;display:flex;align-items:center;gap:var(--space-2);">{right}</div></div>'''

def tabs(names, active):
    out=[]
    for n in names:
        on = n==active
        out.append(f'''<div style="height:38px;display:flex;align-items:center;padding:0 var(--space-1);
          font-size:var(--text-sm);font-weight:{600 if on else 500};
          color:var({'--accent-fg' if on else '--text-secondary'});
          border-bottom:2px solid {'var(--brand)' if on else 'transparent'};">{n}</div>''')
    return f'<div style="display:flex;gap:var(--space-5);">{"".join(out)}</div>'
