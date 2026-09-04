from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
from entra_billing import adminshell
import _charts as ch

# ---------------- Entitlements ----------------
MODS=[("Dynamic View","dynamic-views","Active","success","included in Team",""),
      ("WorkApps","workapps","Trial","warning","11 days left","2026-04-14"),
      ("Data Shuttle","data-shuttle","Not enabled","neutral","Enterprise plan",""),
      ("DataMesh","datamesh","Not enabled","neutral","Enterprise plan",""),
      ("Bridge","bridge","Not enabled","neutral","Enterprise plan",""),
      ("Calendar App","calendar-app","Active","success","included in Team",""),
      ("Pivot App","pivots","Active","success","included in Team",""),
      ("DAM assets","assets","Not enabled","neutral","Add-on",""),
      ("AI assist","ai-assist","Active","success","metered · 12k tokens/day",""),
      ("AI insights","ai-insights","Trial","warning","4 days left","2026-04-07")]
def st(t,k): return chip(t,k) if k!="neutral" else f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-tertiary);border:1px solid var(--border-subtle);">{t}</span>'
mrows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-3) 0;gap:var(--space-3);
  border-bottom:1px solid var(--border-subtle);">
  <div style="width:200px;flex:none;"><div style="font-size:var(--text-sm);font-weight:600;">{n}</div>
    <div class="mono" style="font-size:11px;color:var(--text-tertiary);margin-top:2px;">{slug}</div></div>
  <div style="width:130px;flex:none;">{st(s,k)}</div>
  <div style="flex:1;font-size:var(--text-sm);color:var(--text-secondary);">{note}</div>
  <div class="mono" style="width:110px;flex:none;text-align:right;font-size:var(--text-xs);color:var(--text-tertiary);">{exp}</div>
  <button class="btn btn-{"secondary" if s!="Not enabled" else "primary"}" style="height:var(--control-sm);font-size:var(--text-xs);">
    {"Manage" if s!="Not enabled" else "Enable"}</button>
</div>''' for n,slug,s,k,note,exp in MODS)

ent = adminshell("Entitlements", chip("Team plan","accent"),
  ["Modules","Feature flags","Limits","History"],"Modules",
  BTN("Compare plans","ghost","chart")+BTN("Upgrade plan","primary","sparkle"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-2);overflow:hidden;">
      <div style="display:flex;padding-bottom:6px;border-bottom:1px solid var(--border-default);gap:var(--space-3);">
        <span class="th" style="width:200px;flex:none;">Module</span>
        <span class="th" style="width:130px;flex:none;">State</span>
        <span class="th" style="flex:1;">Source</span>
        <span class="th" style="width:110px;flex:none;text-align:right;">Ends</span>
        <span style="width:74px;"></span></div>
      {mrows}
    </div>
    <aside style="width:320px;flex:none;border-left:1px solid var(--border-subtle);padding:var(--space-4);
      display:flex;flex-direction:column;gap:var(--space-4);">
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--warning-bg);
        border:1px solid var(--warning-border);">
        <div style="display:flex;align-items:center;gap:8px;color:var(--warning-fg);">{icon("clock",16)}
          <span style="font-size:var(--text-sm);font-weight:600;">2 trials ending</span></div>
        <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:6px;line-height:17px;">
          At expiry these modules become read-only for 7 days before turning off. Nothing you created is
          deleted, and re-enabling restores it.</div></div>
      <div><span class="th">Where state comes from</span>
        <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:18px;margin-top:6px;">
          A plan change writes entitlements with <span class="mono">source: plan</span>. Anything an operator
          set by hand carries <span class="mono">source: manual</span> and is never overwritten by billing.</div></div>
      <div><span class="th">Denied requests · 7d</span>
        <div style="margin-top:8px;">{ch.bars(280,90,[12,4,0,7,2,0,1],labels=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],color="#e0930f")}</div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:6px;line-height:17px;">
          Mostly <span class="mono">data-shuttle</span> — a signal that someone needs it, not an error.</div></div>
    </aside>
  </div>''')
write('Entitlements.dc.html', page(ent, theme="light"))

# ---------------- MCP admin ----------------
TOOLS=[("search_records","read","records:read","1,284","—"),("get_record","read","records:read","3,902","—"),
       ("list_children","read","records:read","644","—"),("get_report","read","records:read","208","—"),
       ("get_workflow_runs","read","workflows:run","91","—"),
       ("create_record","write","records:write","24","18 approved"),("update_record","write","records:write","61","44 approved"),
       ("add_comment","write","records:write","12","12 approved"),("assign_record","write","records:write","8","6 approved"),
       ("run_workflow","write","workflows:run","3","2 approved")]
trows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-2) 0;gap:var(--space-3);
  border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);">
  <span class="mono" style="width:190px;flex:none;">{n}</span>
  <span style="width:80px;flex:none;">{chip(k,"accent" if k=="read" else "warning")}</span>
  <span class="mono" style="width:160px;flex:none;color:var(--text-secondary);font-size:var(--text-xs);">{sc}</span>
  <span class="mono" style="width:80px;flex:none;text-align:right;">{c}</span>
  <span style="flex:1;text-align:right;color:var(--text-tertiary);font-size:var(--text-xs);">{a}</span>
</div>''' for n,k,sc,c,a in TOOLS)

mcp = adminshell("MCP access", chip("2 tokens active","success"),
  ["Tools","Resources","Confirmations","Audit"],"Tools",
  BTN("Rotate token","ghost")+BTN("Audit log","ghost","doc")+BTN("New token","primary","plus"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      <div style="display:flex;gap:var(--space-4);">
        {"".join(f'''<div class="card" style="flex:1;padding:var(--space-4);"><span class="th">{l}</span>
          <div class="mono" style="font-size:var(--text-2xl);font-weight:600;margin-top:4px;">{v}</div>
          <div style="font-size:11px;color:var(--text-tertiary);margin-top:2px;">{s}</div></div>'''
          for l,v,s in [("Calls · 7d","6,237","across 2 clients"),("Mutations","108","82 approved, 26 expired"),
                        ("Denied","417","permission-filtered, not errors"),("p95","88ms","reads")])}
      </div>
      <div style="display:flex;flex-direction:column;gap:var(--space-2);">
        <span class="th">Tools exposed to this token</span>
        <div style="display:flex;padding-bottom:6px;border-bottom:1px solid var(--border-default);gap:var(--space-3);">
          <span class="th" style="width:190px;flex:none;">Tool</span><span class="th" style="width:80px;flex:none;">Kind</span>
          <span class="th" style="width:160px;flex:none;">Required scope</span>
          <span class="th" style="width:80px;flex:none;text-align:right;">Calls</span>
          <span class="th" style="flex:1;text-align:right;">Confirmations</span></div>
        {trows}
      </div>
    </div>
    <aside style="width:330px;flex:none;border-left:1px solid var(--border-subtle);padding:var(--space-4);
      display:flex;flex-direction:column;gap:var(--space-4);">
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--accent-bg);
        border:1px solid var(--accent-border);">
        <div style="display:flex;align-items:center;gap:8px;color:var(--accent-fg);">{icon("shield",16)}
          <span style="font-size:var(--text-sm);font-weight:600;">Writes stop at a human</span></div>
        <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:6px;line-height:17px;">
          A mutating tool never writes on first call. It returns a diff and a confirmation id that expires in
          15 minutes; changing the arguments invalidates the approval.</div></div>
      <div><span class="th">Pending confirmations</span>
        <div style="display:flex;flex-direction:column;gap:8px;margin-top:8px;">
          {"".join(f'''<div style="padding:var(--space-3);border:1px solid var(--border-subtle);
            border-radius:var(--radius-md);">
            <div class="mono" style="font-size:11px;color:var(--text-tertiary);">{t}</div>
            <div style="font-size:var(--text-sm);font-weight:600;margin-top:3px;">{n}</div>
            <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:3px;">{d}</div>
            <div style="display:flex;gap:6px;margin-top:8px;">
              <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">View diff</button>
              <button class="btn btn-primary" style="height:var(--control-sm);font-size:var(--text-xs);">Approve</button></div></div>'''
            for t,n,d in [("expires in 11m","update_record","Status: Blocked → In progress on ROW-2471"),
                          ("expires in 3m","add_comment","New comment on ROW-2455")])}
        </div></div>
    </aside>
  </div>''')
write('Mcp.dc.html', page(mcp, theme="dark"))
print("Entitlements + Mcp written")
