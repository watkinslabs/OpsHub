from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
import _charts as ch

# ---------------- Publishing / embed ----------------
PUBS=[("Delivery overview","Dashboard","link","Active","success","1,204","30 Apr",True),
      ("Vendor status","Report","tenant","Active","success","86","15 May",False),
      ("Q1 retrospective","Dashboard","link","Expired","warning","2,331","1 Mar",False)]
prows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-3) 0;gap:var(--space-3);
  border-bottom:1px solid var(--border-subtle);{"background:var(--bg-selected);" if sel else ""}">
  <div style="flex:1;display:flex;align-items:center;gap:10px;">
    <span style="color:var(--text-tertiary);">{icon("chart" if k=="Dashboard" else "doc",16)}</span>
    <div><div style="font-size:var(--text-sm);font-weight:600;">{n}</div>
      <div style="font-size:var(--text-xs);color:var(--text-tertiary);">{k}</div></div></div>
  <div style="width:110px;flex:none;">{chip("Anyone with link" if a=="link" else "Tenant only","accent" if a=="link" else "warning")}</div>
  <div style="width:90px;flex:none;">{chip(s,sk)}</div>
  <div class="mono" style="width:80px;flex:none;text-align:right;font-size:var(--text-sm);">{v}</div>
  <div class="mono" style="width:90px;flex:none;text-align:right;font-size:var(--text-sm);color:var(--text-secondary);">{e}</div>
  <span style="width:24px;text-align:right;color:var(--text-tertiary);">{icon("dots",16)}</span>
</div>''' for n,k,a,s,sk,v,e,sel in PUBS)

pub = shell("Dashboards","Publishing", chip("2 active","success"),
  ["Publications","Embeds","Access log","Settings"],"Publications",
  BTN("Access log","ghost","doc")+BTN("Revoke all","ghost")+BTN("Publish","primary","people"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      <div>
        <div style="display:flex;padding-bottom:6px;border-bottom:1px solid var(--border-default);gap:var(--space-3);">
          <span class="th" style="flex:1;">Target</span>
          <span class="th" style="width:110px;flex:none;">Access</span>
          <span class="th" style="width:90px;flex:none;">Status</span>
          <span class="th" style="width:80px;flex:none;text-align:right;">Views 7d</span>
          <span class="th" style="width:90px;flex:none;text-align:right;">Expires</span><span style="width:24px;"></span></div>
        {prows}
      </div>
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span class="th">Views · Delivery overview</span>
        {ch.line(760,120,[40,62,58,91,120,104,146,171,158,204,231,212,266,289])}
        <div style="display:flex;gap:var(--space-5);font-size:var(--text-xs);color:var(--text-tertiary);">
          <span>Renders as the publisher's permissions at request time</span>
          <span class="mono" style="margin-left:auto;">refresh every 300s · snapshot age 41s</span></div>
      </div>
    </div>
    <aside style="width:340px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
      <span class="th">Delivery overview</span>
      <div style="display:flex;align-items:center;gap:8px;padding:var(--space-3);background:var(--bg-sunken);
        border:1px solid var(--border-subtle);border-radius:var(--radius-md);">
        <span class="mono" style="flex:1;font-size:11px;color:var(--text-secondary);overflow:hidden;
          text-overflow:ellipsis;white-space:nowrap;">opshub.io/public/publications/8fJ2q…</span>
        <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Copy</button></div>
      <div style="padding:var(--space-3);background:var(--bg-sunken);border:1px solid var(--border-subtle);
        border-radius:var(--radius-md);">
        <div class="th" style="margin-bottom:6px;">Embed snippet</div>
        <div class="mono" style="font-size:11px;color:var(--text-secondary);line-height:16px;">
          &lt;iframe src="opshub.io/embed/8fJ2q…"<br>&nbsp;&nbsp;width="960" height="600"<br>&nbsp;&nbsp;frameborder="0"&gt;&lt;/iframe&gt;</div></div>
      <div><span class="th">Allowed origins</span>
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:8px;">
          {"".join(f'<div class="mono" style="font-size:11px;padding:6px var(--space-2);border-radius:var(--radius-sm);background:var(--bg-sunken);border:1px solid var(--border-subtle);color:var(--text-secondary);">{o}</div>' for o in ["https://northfield.co","https://intranet.northfield.co"])}
        </div></div>
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--warning-bg);
        border:1px solid var(--warning-border);font-size:var(--text-xs);color:var(--warning-fg);line-height:17px;">
        A publication never widens access. If the publisher loses read access the page shows an error state and
        no data, and revoking takes effect within 5 seconds.</div>
    </aside>
  </div>''', crumb="Northfield Delivery")
write('Publishing.dc.html', page(pub, theme="light"))

# ---------------- Intake / request form ----------------
intake = shell("Sheets","Project intake", chip("Step 2 of 4","accent"),
  ["Request","Scoring","Approvals","Pipeline"],"Request",
  BTN("Save draft","ghost")+BTN("Submit","primary","check"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;display:flex;justify-content:center;padding:var(--space-7) var(--space-5);
      background:var(--bg-canvas);overflow:hidden;">
      <div style="width:640px;display:flex;flex-direction:column;gap:var(--space-5);">
        <div><h2 style="margin:0;font-size:var(--text-xl);font-weight:700;letter-spacing:-.01em;">Business case</h2>
          <p style="margin:6px 0 0;font-size:var(--text-sm);color:var(--text-secondary);line-height:20px;">
            Scored automatically against the portfolio model. A score above 70 routes to the change board.</p></div>
        {"".join(f'''<div style="display:flex;flex-direction:column;gap:6px;">
          <span class="th">{l}{' <span style="color:var(--danger-fg);">*</span>' if req else ''}</span>
          <div style="min-height:{h}px;border:1px solid var(--border-{b});border-radius:var(--radius-md);
            background:var(--bg-surface);padding:var(--space-3);font-size:var(--text-sm);
            color:var(--text-{c});line-height:20px;">{v}</div>
          {f'<span style="font-size:11px;color:var(--text-tertiary);">{hint}</span>' if hint else ''}</div>'''
          for l,v,h,b,c,req,hint in [
            ("Request title","Partner portal phase 2",32,"default","primary",True,""),
            ("Problem statement","Partners raise 400+ support tickets a month for status they could self-serve. Support cost is £18k/month and partner NPS fell 11 points.",84,"default","primary",True,"120–2,000 characters"),
            ("Expected benefit","Deflect 60% of status tickets; £11k/month saving from Q4.",56,"default","primary",True,""),
            ("Requested by","Sam Okafor · Partner Operations",32,"default","secondary",False,"")])}
        <div style="display:flex;gap:var(--space-4);">
          {"".join(f'''<div style="flex:1;display:flex;flex-direction:column;gap:6px;"><span class="th">{l}</span>
            <div style="height:var(--control-md);border:1px solid var(--border-default);border-radius:var(--radius-md);
              background:var(--bg-surface);display:flex;align-items:center;padding:0 var(--space-3);
              font-size:var(--text-sm);">{v}<span style="margin-left:auto;color:var(--text-tertiary);">{icon("down",15)}</span></div></div>'''
            for l,v in [("Value band","£100k–£250k"),("Target quarter","Q4 2026"),("Sponsor","Priya Raman")])}
        </div>
      </div>
    </div>
    <aside style="width:320px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
      <span class="th">Live score</span>
      <div style="display:flex;align-items:center;justify-content:center;">{ch.gauge(180,74)}</div>
      {"".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);font-size:var(--text-sm);">
        <span style="flex:1;color:var(--text-secondary);">{n}</span>
        <div style="width:70px;height:6px;border-radius:99px;background:var(--bg-sunken);">
          <div style="width:{p}%;height:100%;border-radius:99px;background:var(--brand);"></div></div>
        <span class="mono" style="width:28px;text-align:right;font-size:var(--text-xs);">{p}</span></div>'''
        for n,p in [("Strategic fit",85),("Value",70),("Confidence",60),("Risk",80)])}
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--accent-bg);
        border:1px solid var(--accent-border);font-size:var(--text-xs);color:var(--accent-fg);line-height:17px;">
        At 74 this routes to the change board. Submitting creates the request row, notifies the sponsor and
        opens approval step 1.</div>
    </aside>
  </div>''', crumb="Northfield Delivery / Intake")
write('Intake.dc.html', page(intake, theme="light"))
print("Publishing + Intake written")
