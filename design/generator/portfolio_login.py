from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
import _charts as ch

# ---------------- Portfolio rollup ----------------
PROJ=[("Migration programme","PR",30,78,"On track","success",92,"Apr 30","1.2M","890k"),
      ("Mobile launch","AD",210,54,"At risk","danger",61,"May 22","640k","520k"),
      ("Data platform","MW",120,66,"Watch","warning",74,"Jun 10","980k","610k"),
      ("Compliance 2026","SO",70,91,"On track","success",96,"Apr 12","320k","300k"),
      ("Partner portal","IM",160,33,"On track","success",48,"Aug 01","450k","150k")]
rows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-3) var(--space-5);
  border-bottom:1px solid var(--border-subtle);gap:var(--space-3);">
  <div style="width:230px;flex:none;display:flex;align-items:center;gap:8px;">
    <span style="color:var(--text-tertiary);">{icon("chev",13)}</span>
    <span style="font-size:var(--text-sm);font-weight:600;">{n}</span></div>
  <div style="width:120px;flex:none;">{chip(h,hk)}</div>
  <div style="width:150px;flex:none;display:flex;align-items:center;gap:8px;">
    <div style="flex:1;height:6px;border-radius:99px;background:var(--bg-sunken);">
      <div style="width:{p}%;height:100%;border-radius:99px;background:var(--brand);"></div></div>
    <span class="mono" style="font-size:11px;color:var(--text-secondary);">{p}%</span></div>
  <div style="width:110px;flex:none;display:flex;align-items:center;gap:8px;">{avatar(i,ah)}
    <span style="font-size:var(--text-xs);color:var(--text-secondary);">{i}</span></div>
  <div class="mono" style="width:100px;flex:none;font-size:var(--text-sm);color:var(--text-secondary);">{due}</div>
  <div class="mono" style="width:110px;flex:none;font-size:var(--text-sm);">{spent} / {budget}</div>
  <div style="flex:1;display:flex;justify-content:flex-end;">{ch.spark(90,24,[c*0.7,c*0.8,c*0.85,c*0.95,c])}</div>
</div>''' for n,i,ah,p,h,hk,c,due,budget,spent in PROJ)

port = shell("Dashboards","Portfolio", chip("5 programmes","accent"),
  ["Rollup","Health","Financials","Dependencies"],"Rollup",
  BTN("Group: Programme","ghost","layers")+BTN("Period: Q2","ghost","calendar")+BTN("Export","secondary","doc"),
  f'''<div style="flex:1;display:flex;flex-direction:column;background:var(--bg-surface);overflow:hidden;">
    <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:var(--space-4);padding:var(--space-5);">
      {"".join(f'''<div class="card" style="padding:var(--space-4);"><span class="th">{l}</span>
        <div style="display:flex;align-items:flex-end;gap:8px;margin-top:4px;">
        <span class="mono" style="font-size:var(--text-2xl);font-weight:600;">{v}</span>
        <span class="mono" style="font-size:11px;color:var(--{c}-fg);padding-bottom:5px;">{d}</span></div></div>'''
        for l,v,d,c in [("Programmes","5","1 at risk","danger"),("Budget used","64%","+6 pts","warning"),
                        ("Milestones hit","31/38","82%","success"),("Open risks","17","+4","danger")])}
    </div>
    <div style="display:flex;padding:var(--space-2) var(--space-5);background:var(--bg-sunken);
      border-top:1px solid var(--border-default);border-bottom:1px solid var(--border-default);gap:var(--space-3);">
      {"".join(f'<span class="th" style="width:{w}px;flex:none;">{n}</span>' for n,w in [("Programme",230),("Health",120),("Progress",150),("Owner",110),("Target",100),("Spend / budget",110)])}
      <span class="th" style="flex:1;text-align:right;">Trend</span>
    </div>
    {rows}
  </div>''', crumb="Northfield Delivery")
write('Portfolio.dc.html', page(port, theme="light"))

# ---------------- Login ----------------
login = f'''
  <div style="flex:1;display:flex;">
    <div style="flex:1;display:flex;align-items:center;justify-content:center;background:var(--bg-canvas);">
      <div style="width:400px;display:flex;flex-direction:column;gap:var(--space-5);">
        <div style="display:flex;align-items:center;gap:var(--space-2);">
          <span style="width:32px;height:32px;border-radius:9px;background:var(--brand);display:inline-flex;
            align-items:center;justify-content:center;">{icon("layers",19,"#fff","2")}</span>
          <span style="font-size:var(--text-xl);font-weight:700;letter-spacing:-.02em;">OpsHub</span></div>
        <div><h1 style="margin:0;font-size:var(--text-2xl);font-weight:700;letter-spacing:-.02em;">Sign in</h1>
          <p style="margin:6px 0 0;font-size:var(--text-sm);color:var(--text-secondary);">
            to <span style="font-weight:600;color:var(--text-primary);">Northfield Delivery</span></p></div>
        <div style="display:flex;flex-direction:column;gap:var(--space-2);">
          {"".join(f'''<button class="btn btn-secondary" style="height:var(--control-lg);justify-content:center;gap:10px;">
            {icon(i,17)}{n}</button>''' for i,n in [("shield","Sign in with Microsoft"),("user","Sign in with SSO (SAML)")])}
        </div>
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <div style="flex:1;height:1px;background:var(--border-subtle);"></div>
          <span style="font-size:var(--text-xs);color:var(--text-tertiary);">or</span>
          <div style="flex:1;height:1px;background:var(--border-subtle);"></div></div>
        <div style="display:flex;flex-direction:column;gap:var(--space-3);">
          {"".join(f'''<div style="display:flex;flex-direction:column;gap:5px;"><span class="th">{l}</span>
            <div style="height:var(--control-lg);border:1px solid var(--border-{b});border-radius:var(--radius-md);
              background:var(--bg-surface);display:flex;align-items:center;padding:0 var(--space-3);
              font-size:var(--text-sm);color:var(--text-{c});{r}">{v}</div></div>'''
            for l,v,b,c,r in [("Work email","priya@northfield.co","default","primary",""),
                              ("Password","••••••••••••","default","primary","")])}
          <div style="display:flex;align-items:center;gap:8px;font-size:var(--text-sm);">
            <span style="width:16px;height:16px;border-radius:4px;border:1.5px solid var(--brand);background:var(--brand);
              display:inline-flex;align-items:center;justify-content:center;">{icon("check",11,"#fff","3")}</span>
            Keep me signed in
            <a href="#" style="margin-left:auto;font-size:var(--text-sm);">Forgot password?</a></div>
          <button class="btn btn-primary" style="height:var(--control-lg);justify-content:center;">Continue</button>
        </div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);text-align:center;line-height:18px;">
          Protected by rate limiting and MFA. New here?
          <a href="#">Start a free trial</a></div>
      </div>
    </div>
    <div style="width:520px;flex:none;background:linear-gradient(160deg,
      color-mix(in oklch, var(--brand) 22%, var(--bg-canvas)), var(--bg-canvas));
      display:flex;align-items:center;justify-content:center;padding:var(--space-9);
      border-left:1px solid var(--border-subtle);">
      <div style="max-width:340px;">
        <div style="font-size:var(--text-2xl);font-weight:700;line-height:32px;letter-spacing:-.02em;">
          One record set. Every view your team needs.</div>
        <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:22px;margin-top:var(--space-3);">
          Sheets, timelines, dashboards, approvals and automation over the same rows — with permissions that
          hold at every layer.</div>
      </div>
    </div>
  </div>'''
write('Login.dc.html', page(login, theme="light"))
print("Portfolio + Login written")
