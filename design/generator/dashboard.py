from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
import _charts as ch

def kpi(label,value,delta,up,pts,color="var(--brand)"):
    dcol = "--success-fg" if up else "--danger-fg"
    arrow = "▲" if up else "▼"
    return f'''<div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-2);">
      <span class="th">{label}</span>
      <div style="display:flex;align-items:flex-end;gap:var(--space-2);">
        <span class="mono" style="font-size:var(--text-3xl);line-height:34px;font-weight:600;letter-spacing:-.02em;">{value}</span>
        <span class="mono" style="font-size:var(--text-xs);color:var({dcol});padding-bottom:6px;">{arrow} {delta}</span>
      </div>
      <div style="margin-top:2px;">{ch.spark(180,34,pts,color)}</div>
    </div>'''

def widget(title, subtitle, body, actions=True):
    return f'''<div class="card" style="display:flex;flex-direction:column;overflow:hidden;">
      <div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-4) var(--space-4) var(--space-2);">
        <div><div style="font-size:var(--text-base);font-weight:600;">{title}</div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;">{subtitle}</div></div>
        {'<span style="margin-left:auto;display:flex;gap:2px;color:var(--text-tertiary);">' + icon("panel",16) + icon("dots",16) + '</span>' if actions else ''}
      </div>
      <div style="padding:0 var(--space-4) var(--space-4);flex:1;">{body}</div>
    </div>'''

def legend(items):
    return '<div style="display:flex;flex-wrap:wrap;gap:var(--space-3);margin-top:var(--space-3);">' + "".join(
        f'<span style="display:inline-flex;align-items:center;gap:6px;font-size:var(--text-xs);color:var(--text-secondary);">'
        f'<span style="width:9px;height:9px;border-radius:3px;background:{c};"></span>{n}</span>' for n,c in items) + '</div>'

burn = ch.line(560,150,[120,116,109,104,98,88,83,74,66,57,51,44,36,31],"var(--brand)")
plan = ch.line(560,150,[120,111,103,94,86,77,69,60,51,43,34,26,17,9],"#8c94a1",fill=False,sw=1.6)

body = topbar("Delivery overview") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("Dashboards")}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;overflow:hidden;">
      <div style="padding:var(--space-5) var(--space-6) 0;background:var(--bg-surface);">
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">Delivery overview</h1>
          {chip("Live","success")}
          <span style="font-size:var(--text-xs);color:var(--text-tertiary);">updated 40s ago</span>
        </div>
      </div>
      {toolbar(tabs(["Overview","Portfolio","Quality","Cost"],"Overview"),
        f'<button class="btn btn-ghost">{icon("calendar",16)}Last 90 days</button>'
        f'<button class="btn btn-ghost">{icon("filter",16)}Filter</button>'
        f'<button class="btn btn-secondary">{icon("people",16)}Share</button>'
        f'<button class="btn btn-primary">{icon("plus",16)}Add widget</button>')}
      <div style="flex:1;padding:var(--space-5) var(--space-6);display:flex;flex-direction:column;
        gap:var(--space-4);overflow:hidden;">
        <div style="display:grid;grid-template-columns:repeat(4, minmax(0,1fr));gap:var(--space-4);">
          {kpi("On-time delivery","94.2%","2.1 pts",True,[86,88,87,90,91,90,93,94])}
          {kpi("Open risks","17","4",False,[9,11,10,13,14,15,16,17],ch.SER[2])}
          {kpi("Cycle time","6.4d","0.8d",True,[9,8.6,8.1,7.7,7.2,6.9,6.6,6.4],ch.SER[1])}
          {kpi("Utilization","87%","3 pts",True,[78,80,79,83,84,85,86,87],ch.SER[3])}
        </div>
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:var(--space-4);flex:1;min-height:0;">
          {widget("Burndown — Migration programme","Remaining effort vs. baseline, weeks 1–14",
            f'<div style="position:relative;">{burn}<div style="position:absolute;inset:0;">{plan}</div></div>'
            + legend([("Actual","var(--brand)"),("Baseline","#8c94a1")]))}
          {widget("Work by status","1,284 rows across 6 sheets",
            f'<div style="display:flex;align-items:center;justify-content:center;padding:var(--space-2) 0;">'
            f'{ch.donut(150,[52,23,14,11],center="1,284")}</div>'
            + legend([("Done","var(--brand)"),("In progress",ch.SER[1]),("Review",ch.SER[2]),("Blocked",ch.SER[3])]))}
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-4);height:210px;">
          {widget("Throughput by phase","Rows completed per week",
            ch.stacked(300,120,[[8,5,3],[11,6,4],[9,8,5],[14,7,6],[12,9,7]],labels=["W10","W11","W12","W13","W14"])
            + legend([("Discovery","var(--brand)"),("Build",ch.SER[1]),("Harden",ch.SER[2])]))}
          {widget("Approval SLA","Median hours to decision",
            ch.bars(300,120,[14,11,9,12,7,6],labels=["Nov","Dec","Jan","Feb","Mar","Apr"],color=ch.SER[1]))}
          {widget("Programme health","Weighted across 4 workstreams",
            f'<div style="display:flex;align-items:center;gap:var(--space-4);">{ch.gauge(150,78)}'
            f'<div style="display:flex;flex-direction:column;gap:8px;">'
            f'{chip("2 on track","success")}{chip("1 watch","warning")}{chip("1 at risk","danger")}</div></div>')}
        </div>
      </div>
    </main>
  </div>'''
write('Dashboard.dc.html', page(body, theme="dark"))
