from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
from entra_billing import adminshell
import _charts as ch

# ---------------- Governance / compliance ----------------
POL=[("Work records","7 years","Legal hold: 2 sheets","Active","success"),
     ("Comments & activity","3 years","—","Active","success"),
     ("Files & attachments","5 years","Legal hold: 1 case","Active","success"),
     ("Audit events","7 years","Immutable","Active","success"),
     ("Signup requests","30 days","Pre-tenant data","Active","success"),
     ("Integration call logs","90 days","—","Active","success")]
prows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-3) 0;gap:var(--space-3);
  border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);">
  <span style="flex:1;font-weight:500;">{n}</span>
  <span class="mono" style="width:100px;">{r}</span>
  <span style="flex:1;color:var(--text-secondary);font-size:var(--text-xs);">{h}</span>
  <span style="width:90px;">{chip(s,k)}</span>
  <span style="width:24px;text-align:right;color:var(--text-tertiary);">{icon("cog",15)}</span>
</div>''' for n,r,h,s,k in POL)

gov = adminshell("Governance & compliance", chip("2 legal holds","warning"),
  ["Retention","Legal holds","Access reviews","Export & purge"],"Retention",
  BTN("Access review","ghost","people")+BTN("Tenant export","secondary","doc")+BTN("New policy","primary","plus"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-5);overflow:hidden;">
      <div>
        <div style="display:flex;padding-bottom:6px;border-bottom:1px solid var(--border-default);gap:var(--space-3);">
          <span class="th" style="flex:1;">Data class</span><span class="th" style="width:100px;">Retention</span>
          <span class="th" style="flex:1;">Hold</span><span class="th" style="width:90px;">Status</span>
          <span style="width:24px;"></span></div>
        {prows}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);">
        <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
          <span class="th">Purge queue</span>
          {"".join(f'''<div style="display:flex;align-items:center;font-size:var(--text-sm);padding:5px 0;
            border-bottom:1px solid var(--border-subtle);"><span style="flex:1;">{n}</span>
            <span class="mono" style="color:var(--text-secondary);">{v}</span></div>'''
            for n,v in [("Comments older than 3 years","14,802 rows"),("Signup requests · unverified","318 rows"),
                        ("Integration logs · 90d","96,140 rows")])}
          <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
            A purge runs as a privileged, audited job and refuses anything under legal hold — the hold wins
            over the policy, always.</div></div>
        <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
          <span class="th">Access review · Q2</span>
          <div style="display:flex;align-items:center;gap:var(--space-4);">
            {ch.donut(110,[28,9,4],center="41")}
            <div style="display:flex;flex-direction:column;gap:6px;">
              {"".join(f'<span style="display:inline-flex;align-items:center;gap:6px;font-size:var(--text-xs);color:var(--text-secondary);"><span style="width:9px;height:9px;border-radius:3px;background:{c};"></span>{n}</span>' for n,c in [("Confirmed 28","var(--brand)"),("Pending 9","#e0930f"),("Revoked 4","#d6558f")])}
            </div></div>
          <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
            Reviewers have 5 days left. Unreviewed access is reported, never revoked automatically.</div></div>
      </div>
    </div>
  </div>''')
write('Governance.dc.html', page(gov, theme="light"))

# ---------------- Templates gallery ----------------
TPL=[("Delivery programme","Sheets, timeline, dashboard, 2 workflows","Programme","layers",True),
     ("Vendor review","Intake form, review sheet, 3-step approval","Procurement","shield",False),
     ("Sprint board","Board view, burndown, standup digest","Engineering","grid",False),
     ("Incident log","Sheet, severity rules, escalation workflow","Operations","warn",False),
     ("Client onboarding","WorkApp, checklist, update requests","Services","people",False),
     ("Quarterly planning","Portfolio rollup, capacity, scoring","Portfolio","chart",False)]
cards="".join(f'''<div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);
  {"box-shadow:0 0 0 2px var(--brand), var(--shadow-1);" if sel else ""}">
  <div style="height:96px;border-radius:var(--radius-md);background:var(--bg-sunken);
    border:1px solid var(--border-subtle);display:flex;align-items:center;justify-content:center;
    color:var(--text-tertiary);">{icon(ic,28)}</div>
  <div><div style="font-size:var(--text-base);font-weight:600;">{n}</div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:3px;line-height:17px;">{d}</div></div>
  <div style="display:flex;align-items:center;gap:8px;">{chip(cat,"accent")}
    <button class="btn btn-{"primary" if sel else "secondary"}" style="margin-left:auto;height:var(--control-sm);
      font-size:var(--text-xs);">Use template</button></div>
</div>''' for n,d,cat,ic,sel in TPL)

tpl = shell("Sheets","Templates", chip("6 available","accent"),
  ["Gallery","Your templates","Provisioning runs","Baselines"],"Gallery",
  BTN("Category: All","ghost","filter")+BTN("Create from sheet","secondary","plus"),
  f'''<div style="flex:1;padding:var(--space-5);display:flex;gap:var(--space-5);min-height:0;">
    <div style="flex:1;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--space-4);
      align-content:start;overflow:hidden;">{cards}</div>
    <aside style="width:320px;flex:none;display:flex;flex-direction:column;gap:var(--space-4);">
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span class="th">Delivery programme</span>
        <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:20px;">
          Creates 4 sheets, 1 dashboard, 2 workflows and a report, wired together with the right column
          types and permissions.</div>
        <div style="display:flex;flex-direction:column;gap:6px;">
          {"".join(f'''<div style="display:flex;align-items:center;gap:8px;font-size:var(--text-sm);">
            <span style="color:var(--text-tertiary);">{icon(i,15)}</span>{n}
            <span class="mono" style="margin-left:auto;font-size:11px;color:var(--text-tertiary);">{c}</span></div>'''
            for i,n,c in [("grid","Sheets","4"),("chart","Dashboards","1"),("flow","Workflows","2"),("doc","Reports","1")])}
        </div>
        <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--accent-bg);
          border:1px solid var(--accent-border);font-size:var(--text-xs);color:var(--accent-fg);line-height:17px;">
          Provisioning runs as a job you can watch, and rolls back as one unit if any step fails.</div>
        <button class="btn btn-primary" style="justify-content:center;">Use this template</button>
      </div>
    </aside>
  </div>''', crumb="Northfield Delivery")
write('Templates.dc.html', page(tpl, theme="dark"))
print("Governance + Templates written")
