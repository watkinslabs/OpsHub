from _common import icon, chip, avatar, page, write
import _charts as ch

def w(title, note, body, span=1):
    return f'''<div class="card" style="grid-column:span {span};padding:var(--space-4);display:flex;
      flex-direction:column;gap:var(--space-3);">
      <div style="display:flex;align-items:baseline;gap:8px;">
        <span style="font-size:var(--text-sm);font-weight:600;">{title}</span>
        <span class="mono" style="font-size:10px;color:var(--text-tertiary);margin-left:auto;">{note}</span></div>
      <div style="flex:1;display:flex;align-items:center;justify-content:center;">{body}</div></div>'''

def lg(items):
    return ('<div style="display:flex;flex-wrap:wrap;gap:10px;">' + "".join(
      f'<span style="display:inline-flex;align-items:center;gap:5px;font-size:10px;color:var(--text-secondary);">'
      f'<span style="width:8px;height:8px;border-radius:2px;background:{c};"></span>{n}</span>' for n,c in items) + '</div>')

heat_cells = "".join(
  f'<div style="height:22px;border-radius:3px;background:color-mix(in oklch, var(--brand) {v}%, var(--bg-sunken));"></div>'
  for v in [10,25,40,80,60,30, 20,45,70,95,55,25, 35,60,85,50,30,15, 15,30,50,75,90,40])

funnel = "".join(
  f'''<div style="display:flex;align-items:center;gap:10px;">
    <span class="mono" style="width:74px;font-size:10px;color:var(--text-tertiary);">{n}</span>
    <div style="flex:1;height:20px;border-radius:4px;background:var(--bg-sunken);">
      <div style="width:{p}%;height:100%;border-radius:4px;background:{c};"></div></div>
    <span class="mono" style="width:38px;font-size:10px;text-align:right;">{p}%</span></div>'''
  for n,p,c in [("Intake",100,"var(--brand)"),("Qualified",72,"#0e9aa7"),("Approved",48,"#e0930f"),
                ("Delivered",31,"#d6558f")])

scatter_pts = "".join(
  f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" opacity=".78"/>'
  for x,y,r,c in [(40,90,7,"var(--brand)"),(78,66,10,"var(--brand)"),(120,104,6,"#0e9aa7"),(150,44,13,"#0e9aa7"),
                  (188,80,8,"#e0930f"),(216,30,9,"#e0930f"),(250,96,11,"#d6558f"),(278,58,7,"#d6558f")])

body = f'''
  <div style="padding:var(--space-7);display:flex;flex-direction:column;gap:var(--space-5);
    background:var(--bg-canvas);height:100%;overflow:hidden;">
    <div>
      <h1 style="margin:0;font-size:var(--text-3xl);font-weight:700;letter-spacing:-.025em;">Chart &amp; data widgets</h1>
      <p style="margin:8px 0 0;font-size:var(--text-sm);color:var(--text-secondary);max-width:780px;">
        Every widget type a dashboard, report or metric surface can place (F022–F024). Built on MUI X Charts with the
        OpsHub theme; the categorical series palette is fixed and colour-blind safe, and no chart uses colour as its
        only signal — each carries a label, a legend or a direct value.</p>
      <div style="margin-top:var(--space-3);">{lg([("Series 1","var(--brand)"),("Series 2","#0e9aa7"),("Series 3","#e0930f"),("Series 4","#d6558f"),("Series 5","#5aa06b")])}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4, minmax(0,1fr));gap:var(--space-4);flex:1;min-height:0;">
      {w("KPI tile","metric + delta + spark",
        f'''<div style="width:100%;display:flex;flex-direction:column;gap:6px;">
          <span class="th">On-time delivery</span>
          <div style="display:flex;align-items:flex-end;gap:8px;">
            <span class="mono" style="font-size:30px;line-height:34px;font-weight:600;">94.2%</span>
            <span class="mono" style="font-size:11px;color:var(--success-fg);padding-bottom:6px;">▲ 2.1 pts</span></div>
          {ch.spark(200,32,[86,88,87,90,91,90,93,94])}</div>''')}
      {w("Line","trend over time", ch.line(220,110,[12,18,15,24,22,31,28,36,34,42]))}
      {w("Area + baseline","actual vs. plan",
        f'<div style="position:relative;">{ch.line(220,110,[40,37,33,30,26,21,17,12])}'
        f'<div style="position:absolute;inset:0;">{ch.line(220,110,[40,35,30,25,20,15,10,5],"#8c94a1",False,1.4)}</div></div>')}
      {w("Bar","category comparison", ch.bars(220,110,[14,11,9,12,7,6],labels=["Nov","Dec","Jan","Feb","Mar","Apr"]))}
      {w("Stacked bar","composition over time",
        ch.stacked(220,110,[[8,5,3],[11,6,4],[9,8,5],[14,7,6]],labels=["W11","W12","W13","W14"]))}
      {w("Donut","share of total", ch.donut(120,[52,23,14,11],center="1,284"))}
      {w("Gauge","single measure vs. target", ch.gauge(170,78))}
      {w("Sparkline grid","dense per-row trend",
        f'''<div style="width:100%;display:flex;flex-direction:column;gap:7px;">
          {"".join(f'<div style="display:flex;align-items:center;gap:8px;"><span class="mono" style="width:52px;font-size:10px;color:var(--text-tertiary);">{n}</span>{ch.spark(120,20,v,c)}<span class="mono" style="margin-left:auto;font-size:10px;">{t}</span></div>' for n,v,c,t in [("Priya",[4,6,5,8,7,9],"var(--brand)","92%"),("Ana",[3,4,6,5,8,7],"#0e9aa7","104%"),("Marcus",[6,5,7,9,8,11],"#e0930f","140%")])}
        </div>''')}
      {w("Heatmap","resource × week utilization",
        f'<div style="width:100%;display:grid;grid-template-columns:repeat(6, minmax(0,1fr));gap:4px;">{heat_cells}</div>')}
      {w("Funnel","stage conversion", f'<div style="width:100%;display:flex;flex-direction:column;gap:8px;">{funnel}</div>')}
      {w("Scatter","effort vs. cycle time",
        f'<svg width="300" height="120" viewBox="0 0 300 120" fill="none">'
        f'<path d="M20,110 L290,110 M20,110 L20,10" stroke="var(--border-default)" stroke-width="1"/>{scatter_pts}</svg>')}
      {w("Table + bar","ranked list with inline measure",
        f'''<div style="width:100%;display:flex;flex-direction:column;gap:7px;">
          {"".join(f'<div style="display:flex;align-items:center;gap:8px;font-size:var(--text-xs);"><span style="width:76px;color:var(--text-secondary);">{n}</span><div style="flex:1;height:16px;border-radius:3px;background:var(--bg-sunken);"><div style="width:{p}%;height:100%;border-radius:3px;background:var(--brand);opacity:{o};"></div></div><span class="mono" style="width:32px;text-align:right;">{p}</span></div>' for n,p,o in [("Migration",92,1),("Platform",74,.85),("Mobile",58,.7),("Reporting",41,.55)])}
        </div>''')}
    </div>
  </div>'''
write('Charts.dc.html', page(body, theme="dark", size=(1440,1180)))
