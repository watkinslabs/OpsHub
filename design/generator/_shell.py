from _common import icon, chip, avatar

NAV = [("grid","Sheets"),("chart","Dashboards"),("flow","Automation"),("people","Workload"),
       ("calendar","Calendar"),("doc","Documents"),("shield","Admin")]

def topbar(title, crumb=""):
    """Masthead: identity, workspace context, search and account. Navigation is the icon rail."""
    return f'''
  <header style="height:var(--topbar-h);flex:none;display:flex;align-items:center;gap:var(--space-4);
    padding:0 var(--space-4);background:var(--bg-surface);border-bottom:1px solid var(--border-subtle);
    box-shadow:var(--shadow-1);position:relative;z-index:2;">
    <div style="display:flex;align-items:center;gap:var(--space-2);flex:none;">
      <span style="width:28px;height:28px;border-radius:8px;background:var(--brand);display:inline-flex;
        align-items:center;justify-content:center;">{icon("layers",17,"#fff","2")}</span>
      <span style="font-size:var(--text-lg);font-weight:700;letter-spacing:-.02em;">OpsHub</span>
    </div>
    <div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-md);flex:none;
      padding:0 var(--space-2) 0 var(--space-2);border:1px solid var(--border-default);
      border-radius:var(--radius-md);background:var(--bg-surface);">
      <span style="width:20px;height:20px;border-radius:5px;background:var(--accent-bg);color:var(--accent-fg);
        font-size:10px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">NF</span>
      <span style="font-size:var(--text-sm);font-weight:600;">Northfield Delivery</span>
      <span style="color:var(--text-tertiary);">{icon("down",15)}</span>
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
    """Icon rail: 72px. One product area per icon, label under it, active marked by an edge bar.
    Section navigation belongs to the page, never to a second sidebar beside this one."""
    items = []
    for ic, label in NAV:
        on = label == active
        items.append(f'''<div style="position:relative;display:flex;flex-direction:column;align-items:center;
          justify-content:center;gap:3px;height:56px;border-radius:var(--radius-md);
          color:var(--{"accent-fg" if on else "text-secondary"});
          background:{"var(--bg-selected)" if on else "transparent"};">
          {'<span style="position:absolute;left:-8px;top:14px;width:3px;height:28px;border-radius:0 3px 3px 0;background:var(--brand);"></span>' if on else ''}
          {icon(ic,20)}
          <span style="font-size:10px;font-weight:{600 if on else 500};line-height:1;">{label}</span>
        </div>''')
    return f'''
  <nav style="width:var(--rail-w);flex:none;background:var(--bg-surface);
    border-right:1px solid var(--border-subtle);display:flex;flex-direction:column;
    padding:var(--space-2) var(--space-2);gap:var(--space-1);">
    {''.join(items)}
    <div style="margin-top:auto;display:flex;flex-direction:column;align-items:center;gap:3px;height:56px;
      justify-content:center;color:var(--text-secondary);border-radius:var(--radius-md);">
      {icon("cog",20)}<span style="font-size:10px;font-weight:500;line-height:1;">Settings</span></div>
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

def section_nav(title, items):
    """The page's own navigation — the only wide sidebar a screen may have."""
    rows=[]
    for ic,label,on in items:
        rows.append(f'''<div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-md);
          padding:0 var(--space-3);border-radius:var(--radius-md);font-size:var(--text-sm);
          font-weight:{600 if on else 500};color:var(--{"accent-fg" if on else "text-secondary"});
          background:{"var(--bg-selected)" if on else "transparent"};">{icon(ic,16)}{label}</div>''')
    return f'''<div style="width:var(--section-w);flex:none;background:var(--bg-canvas);
      border-right:1px solid var(--border-subtle);padding:var(--space-4) var(--space-3);
      display:flex;flex-direction:column;gap:2px;">
      <span class="th" style="padding:0 var(--space-3) var(--space-2);">{title}</span>{''.join(rows)}</div>'''
