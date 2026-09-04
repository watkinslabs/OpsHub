from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
from entra_billing import adminshell

# ---------------- Files & proofing ----------------
proof = shell("Documents","runbook-v3.pdf", chip("In review · 2 of 4 approved","warning"),
  ["Proof","Versions","Comments","Activity"],"Proof",
  BTN("Compare v2","ghost","layers")+BTN("Download","ghost","doc")+BTN("Request changes","secondary")+BTN("Approve","primary","check"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:120px;flex:none;background:var(--bg-surface);border-right:1px solid var(--border-subtle);
      padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-2);overflow:hidden;">
      {"".join(f'''<div style="height:110px;border-radius:var(--radius-sm);background:var(--bg-sunken);
        border:{"2px solid var(--brand)" if p==2 else "1px solid var(--border-default)"};
        display:flex;align-items:flex-end;justify-content:center;padding-bottom:4px;
        font-size:10px;color:var(--text-tertiary);position:relative;">
        {'<span style="position:absolute;top:4px;right:4px;width:16px;height:16px;border-radius:99px;background:var(--danger-emphasis);color:#fff;font-size:9px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">2</span>' if p==2 else ''}
        {p}</div>''' for p in [1,2,3,4])}
    </div>
    <div style="flex:1;background:var(--bg-canvas);display:flex;align-items:center;justify-content:center;
      padding:var(--space-6);overflow:hidden;">
      <div style="width:560px;height:100%;background:#fff;border-radius:var(--radius-sm);box-shadow:var(--shadow-2);
        padding:var(--space-7);position:relative;">
        <div style="font-size:20px;font-weight:700;color:#14171c;margin-bottom:var(--space-4);">2. Freeze window</div>
        {"".join(f'<div style="height:9px;border-radius:3px;background:#e6e9ee;margin-bottom:10px;width:{w}%;"></div>' for w in [100,96,88,100,72,0,94,100,83])}
        <div style="position:absolute;left:130px;top:196px;width:220px;height:44px;
          border:2px solid var(--danger-emphasis);border-radius:4px;
          background:color-mix(in oklch, #dc2b2b 12%, transparent);"></div>
        <div style="position:absolute;left:360px;top:186px;display:flex;align-items:center;gap:6px;">
          <span style="width:22px;height:22px;border-radius:99px;background:var(--danger-emphasis);color:#fff;
            font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">1</span></div>
        <div style="position:absolute;left:96px;top:330px;display:flex;align-items:center;gap:6px;">
          <span style="width:22px;height:22px;border-radius:99px;background:var(--warning-emphasis);color:#fff;
            font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">2</span></div>
      </div>
    </div>
    <aside style="width:340px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
      display:flex;flex-direction:column;">
      <div style="padding:var(--space-4);border-bottom:1px solid var(--border-subtle);display:flex;
        align-items:center;gap:8px;"><span style="font-size:var(--text-sm);font-weight:600;">Markups</span>
        {chip("2 open","danger")}</div>
      <div style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
        {"".join(f'''<div style="display:flex;gap:var(--space-2);">
          <span style="width:22px;height:22px;border-radius:99px;background:var(--{c}-emphasis);color:#fff;
            font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;flex:none;">{k}</span>
          <div style="flex:1;"><div style="display:flex;align-items:baseline;gap:6px;">
            <span style="font-size:var(--text-sm);font-weight:600;">{n}</span>
            <span style="font-size:11px;color:var(--text-tertiary);">p{pg} · {w}</span></div>
            <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:19px;margin-top:3px;">{t}</div>
            <div style="display:flex;gap:6px;margin-top:6px;">
              <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Reply</button>
              <button class="btn btn-ghost" style="height:var(--control-sm);font-size:var(--text-xs);">Resolve</button></div>
          </div></div>'''
          for k,c,n,pg,w,t in [(1,"danger","Priya Raman",2,"12m","This window overlaps the payroll run. Move to 02:00–05:00."),
                               (2,"warning","Marcus Webb",2,"4m","Add the rollback owner and their contact here.")])}
      </div>
      <div style="margin-top:auto;padding:var(--space-4);border-top:1px solid var(--border-subtle);">
        <div style="display:flex;flex-direction:column;gap:8px;">
          <span class="th">Approvals</span>
          {"".join(f'''<div style="display:flex;align-items:center;gap:8px;font-size:var(--text-sm);">
            {avatar(i,h)}<span style="flex:1;">{n}</span>{chip(s,c)}</div>'''
            for i,h,n,s,c in [("AD",210,"Ana Duarte","Approved","success"),("SO",70,"Sam Okafor","Approved","success"),
                              ("PR",30,"Priya Raman","Changes","danger"),("MW",120,"Marcus Webb","Waiting","warning")])}
        </div></div>
    </aside>
  </div>''', crumb="Northfield Delivery / Files")
write('Proofing.dc.html', page(proof, theme="light"))

# ---------------- Integrations admin ----------------
CONN=[("Microsoft 365","Notifications, Calendar","Active","success","Contoso Ltd","2m ago","layers"),
      ("Slack","Notifications, Thread replies","Active","success","northfield.slack.com","5m ago","people"),
      ("Google Workspace","Calendar","Needs re-auth","danger","northfield.co","3d ago","calendar"),
      ("Jira Cloud","Work sync · 2 mappings","Active","success","northfield.atlassian.net","1m ago","flow"),
      ("Salesforce","CRM sync · 1 mapping","Paused","warning","northfield.my.salesforce.com","2h ago","chart"),
      ("Box","File sync","Not connected","neutral","—","—","doc")]
def nchip(t,k): return chip(t,k) if k!="neutral" else f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-tertiary);border:1px solid var(--border-subtle);">{t}</span>'
crows="".join(f'''<div class="card" style="padding:var(--space-4);display:flex;align-items:center;gap:var(--space-4);">
  <span style="width:38px;height:38px;border-radius:var(--radius-md);background:var(--bg-sunken);
    color:var(--text-secondary);display:inline-flex;align-items:center;justify-content:center;flex:none;">{icon(ic,20)}</span>
  <div style="flex:1;min-width:0;">
    <div style="display:flex;align-items:center;gap:8px;">
      <span style="font-size:var(--text-base);font-weight:600;">{n}</span>{nchip(s,k)}</div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:3px;">{cap} · {acct}</div></div>
  <span class="mono" style="font-size:11px;color:var(--text-tertiary);width:80px;text-align:right;">{last}</span>
  <button class="btn btn-{"primary" if s=="Not connected" else "secondary"}">{"Connect" if s=="Not connected" else ("Reconnect" if k=="danger" else "Manage")}</button>
</div>''' for n,cap,s,k,acct,last,ic in CONN)

integ = adminshell("Integrations", chip("4 active · 1 needs attention","warning"),
  ["Connections","Syncs","Conflicts","Activity"],"Connections",
  BTN("Activity log","ghost","doc")+BTN("Add connection","primary","plus"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-3);overflow:hidden;">{crows}</div>
    <aside style="width:330px;flex:none;border-left:1px solid var(--border-subtle);padding:var(--space-4);
      display:flex;flex-direction:column;gap:var(--space-4);">
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--danger-bg);
        border:1px solid var(--danger-border);">
        <div style="display:flex;align-items:center;gap:8px;color:var(--danger-fg);">{icon("warn",16)}
          <span style="font-size:var(--text-sm);font-weight:600;">Google needs re-authorization</span></div>
        <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:6px;line-height:17px;">
          Refresh failed 3 times. Calendar sync is paused; nothing was lost and it resumes on reconnect.</div>
        <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);margin-top:var(--space-3);">Reconnect</button></div>
      <div><span class="th">Conflict queue</span>
        <div style="margin-top:8px;display:flex;flex-direction:column;gap:6px;">
          {"".join(f'''<div style="display:flex;align-items:center;font-size:var(--text-sm);padding:6px 0;
            border-bottom:1px solid var(--border-subtle);"><span style="flex:1;">{n}</span>
            <span class="mono" style="color:var(--warning-fg);font-weight:600;">{v}</span></div>'''
            for n,v in [("Jira · Cutover plan","4"),("Salesforce · Vendors","1")])}
        </div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;margin-top:8px;">
          Policy <span class="mono">newest_wins</span> · manual items wait for review and change nothing meanwhile.</div></div>
      <div><span class="th">Token safety</span>
        <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:18px;margin-top:6px;">
          Refresh tokens are envelope-encrypted per tenant and never returned by the API. Revoking a connection
          deletes them and pauses every sync that used it.</div></div>
    </aside>
  </div>''')
write('Integrations.dc.html', page(integ, theme="dark"))
print("Proofing + Integrations written")
