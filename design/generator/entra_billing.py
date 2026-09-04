from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs, section_nav
from board_timeline import shell, BTN
import _charts as ch

def adminshell(title, sub, tabnames, tabactive, right, body, active_nav="Admin"):
    """Admin pages: icon rail plus the section's own navigation. Never two wide sidebars."""
    pages=[("people","Users & groups"),("shield","Roles & permissions"),("user","SSO & SCIM"),
           ("layers","Microsoft Entra"),("layers","Integrations"),("chart","Billing"),
           ("flow","API & webhooks"),("doc","Audit log"),("cog","Entitlements"),("sparkle","MCP access")]
    head = title.split(" \u2014")[0].strip()
    items = [(i, n, n.startswith(head) or head.startswith(n)) for i, n in pages]
    return topbar("") + f"""
  <div style="flex:1;display:flex;min-height:0;">
    {rail(active_nav)}
    {section_nav("Administration", items)}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-surface);">
      <div style="padding:var(--space-5) var(--space-5) 0;">
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">{title}</h1>
          {sub}</div></div>
      {toolbar(tabs(tabnames,tabactive), right)}
      {body}
    </main>
  </div>"""

def field(label, value, hint="", state="default", w="100%"):
    b={"default":"var(--border-default)","ok":"var(--success-emphasis)","err":"var(--danger-emphasis)"}[state]
    return f'''<div style="display:flex;flex-direction:column;gap:5px;width:{w};">
      <span class="th">{label}</span>
      <div style="height:var(--control-md);border:1px solid {b};border-radius:var(--radius-md);
        background:var(--bg-surface);display:flex;align-items:center;padding:0 var(--space-3);
        font-size:var(--text-sm);">{value}</div>
      {f'<span style="font-size:11px;color:var(--text-tertiary);">{hint}</span>' if hint else ''}</div>'''

def toggle(on,label,sub=""):
    return f'''<div style="display:flex;align-items:flex-start;gap:var(--space-3);">
      <span style="width:36px;height:20px;border-radius:99px;flex:none;margin-top:1px;
        background:{'var(--brand)' if on else 'var(--border-strong)'};display:inline-flex;align-items:center;
        padding:2px;justify-content:{'flex-end' if on else 'flex-start'};">
        <span style="width:16px;height:16px;border-radius:99px;background:#fff;"></span></span>
      <div><div style="font-size:var(--text-sm);font-weight:500;">{label}</div>
      {f'<div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;line-height:16px;">{sub}</div>' if sub else ''}</div></div>'''

# ---------------- Entra admin ----------------
GROUPS=[("Delivery Team","Delivery","group",24,2),("Security Reviewers","security-reviewer","role",8,0),
        ("Data Platform","Data Platform","group",16,1),("All Staff","Members","group",412,0)]
gmap="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-3) 0;
  border-bottom:1px solid var(--border-subtle);gap:var(--space-3);font-size:var(--text-sm);">
  <span style="flex:1;display:flex;align-items:center;gap:8px;">{icon("people",15)}{d}</span>
  <span style="color:var(--text-tertiary);">→</span>
  <span style="flex:1;display:flex;align-items:center;gap:6px;">{chip(k,"accent" if k=="group" else "warning")}{o}</span>
  <span class="mono" style="width:110px;text-align:right;color:var(--text-secondary);">{m} members</span>
  <span class="mono" style="width:80px;text-align:right;color:var(--{"success" if r==0 else "warning"}-fg);">+{m//8} / -{r}</span>
  <span style="color:var(--text-tertiary);width:24px;text-align:right;">{icon("dots",16)}</span></div>'''
  for d,o,k,m,r in GROUPS)

entra = adminshell("Microsoft Entra", chip("Connected · Contoso Ltd","success"),
  ["Connection","Sign-in","Groups","Mail"],"Groups",
  BTN("Test connection","ghost","refresh" if False else "clock")+BTN("Sync now","secondary","people")+BTN("Disconnect","ghost"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-5);overflow:hidden;">
      <div style="display:flex;gap:var(--space-4);">
        {field("Directory tenant ID","72f988bf-86f1-41af-91ab-2d7cd011db47","","ok","40%")}
        {field("Client ID","a1b2c3d4-5e6f-7890-abcd-ef1234567890","","ok","40%")}
        {field("Cloud","Global","", "default","20%")}
      </div>
      <div style="display:flex;gap:var(--space-7);">
        {toggle(True,"Sign in with Microsoft","Users press one button; password and SAML stay available")}
        {toggle(True,"Directory group sync","Nightly, delta tokens")}
        {toggle(True,"Graph mail delivery","Sends as ops@northfield.co")}
      </div>
      <div style="display:flex;flex-direction:column;gap:var(--space-2);">
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="th">Group mappings</span>
          <button class="btn btn-secondary" style="margin-left:auto;height:var(--control-sm);font-size:var(--text-xs);">
            {icon("plus",14)}Add mapping</button></div>
        <div style="display:flex;gap:var(--space-3);padding-bottom:6px;border-bottom:1px solid var(--border-default);">
          <span class="th" style="flex:1;">Directory group</span><span class="th" style="width:16px;"></span>
          <span class="th" style="flex:1;">OpsHub target</span>
          <span class="th" style="width:110px;text-align:right;">Size</span>
          <span class="th" style="width:80px;text-align:right;">Last sync</span><span style="width:24px;"></span></div>
        {gmap}
      </div>
    </div>
    <aside style="width:320px;flex:none;border-left:1px solid var(--border-subtle);padding:var(--space-4);
      display:flex;flex-direction:column;gap:var(--space-4);">
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--success-bg);
        border:1px solid var(--success-border);">
        <div style="display:flex;align-items:center;gap:8px;color:var(--success-fg);">{icon("check",16)}
          <span style="font-size:var(--text-sm);font-weight:600;">All scopes granted</span></div>
        <div class="mono" style="font-size:11px;color:var(--text-secondary);margin-top:6px;line-height:16px;">
          User.Read.All · GroupMember.Read.All<br>Mail.Send</div></div>
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--warning-bg);
        border:1px solid var(--warning-border);">
        <div style="display:flex;align-items:center;gap:8px;color:var(--warning-fg);">{icon("warn",16)}
          <span style="font-size:var(--text-sm);font-weight:600;">Sync halted for review</span></div>
        <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:6px;line-height:17px;">
          Last run would have removed 31% of <b>All Staff</b>. Nothing was changed.</div>
        <div style="display:flex;gap:6px;margin-top:var(--space-3);">
          <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Review diff</button>
          <button class="btn btn-ghost" style="height:var(--control-sm);font-size:var(--text-xs);">Approve</button></div></div>
      <div><span class="th">Redirect URI</span>
        <div class="mono" style="margin-top:6px;padding:var(--space-2);background:var(--bg-sunken);
          border-radius:var(--radius-sm);font-size:11px;color:var(--text-secondary);word-break:break-all;">
          https://app.opshub.io/auth/entra/callback</div></div>
    </aside>
  </div>''')
write('Entra.dc.html', page(entra, theme="light"))

# ---------------- Billing ----------------
INV=[("INV-2026-0412","1 Mar 2026","Team · 41 seats","$1,845.00","Paid","success"),
     ("INV-2026-0311","1 Feb 2026","Team · 38 seats","$1,710.00","Paid","success"),
     ("INV-2026-0208","1 Jan 2026","Team · 35 seats","$1,575.00","Paid","success"),
     ("INV-2025-1207","1 Dec 2025","Team · 35 seats","$1,575.00","Refunded","warning")]
invrows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-3) 0;
  border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);">
  <span class="mono" style="width:150px;">{n}</span>
  <span class="mono" style="width:120px;color:var(--text-secondary);">{d}</span>
  <span style="flex:1;color:var(--text-secondary);">{p}</span>
  <span class="mono" style="width:110px;text-align:right;font-weight:600;">{a}</span>
  <span style="width:100px;display:flex;justify-content:flex-end;">{chip(s,k)}</span>
  <span style="width:40px;text-align:right;color:var(--text-tertiary);">{icon("doc",15)}</span></div>''' for n,d,p,a,s,k in INV)

billing = adminshell("Billing", chip("Team plan · active","success"),
  ["Overview","Usage","Invoices","Payment method"],"Overview",
  BTN("Redeem code","secondary","sparkle")+BTN("Change plan","primary","chart"),
  f'''<div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-5);overflow:hidden;">
    <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:var(--space-4);">
      {"".join(f'''<div class="card" style="padding:var(--space-4);"><span class="th">{l}</span>
        <div style="display:flex;align-items:flex-end;gap:8px;margin-top:4px;">
          <span class="mono" style="font-size:var(--text-2xl);font-weight:600;">{v}</span>
          <span style="font-size:11px;color:var(--text-tertiary);padding-bottom:6px;">{s}</span></div></div>'''
        for l,v,s in [("Next invoice","$1,845","1 Apr"),("Seats","41 / 50","in use"),
                      ("Storage","62 GB","of 100 GB"),("Credit balance","$250.00","expires 1 Jun")])}
    </div>
    <div style="display:grid;grid-template-columns:2fr 1fr;gap:var(--space-4);flex:1;min-height:0;">
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:var(--text-base);font-weight:600;">Invoices</span>
          <span class="mono" style="margin-left:auto;font-size:11px;color:var(--text-tertiary);">last 4</span></div>
        <div style="display:flex;padding-bottom:6px;border-bottom:1px solid var(--border-default);">
          <span class="th" style="width:150px;">Invoice</span><span class="th" style="width:120px;">Issued</span>
          <span class="th" style="flex:1;">Plan</span><span class="th" style="width:110px;text-align:right;">Amount</span>
          <span class="th" style="width:100px;text-align:right;">Status</span><span style="width:40px;"></span></div>
        {invrows}
      </div>
      <div style="display:flex;flex-direction:column;gap:var(--space-4);">
        <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
          <span class="th">Redeem a credit code</span>
          <div style="display:flex;gap:8px;">
            <div class="mono" style="flex:1;height:var(--control-md);border:1px solid var(--border-default);
              border-radius:var(--radius-md);display:flex;align-items:center;padding:0 var(--space-3);
              font-size:var(--text-sm);letter-spacing:.08em;color:var(--text-tertiary);">XXXX-XXXX-XXXX-XXXX</div>
            <button class="btn btn-primary">Redeem</button></div>
          <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
            One-time use. Credit applies to your next invoice before any charge.</div>
        </div>
        <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-2);">
          <span class="th">Credit ledger</span>
          {"".join(f'''<div style="display:flex;align-items:center;font-size:var(--text-sm);padding:4px 0;">
            <span style="flex:1;color:var(--text-secondary);">{n}</span>
            <span class="mono" style="color:var(--{c}-fg);font-weight:600;">{v}</span></div>'''
            for n,v,c in [("Redemption · LAUNCH25","+$300.00","success"),("Applied · INV-2026-0412","−$50.00","danger"),
                          ("Balance","$250.00","accent")])}
        </div>
      </div>
    </div>
  </div>''')
write('Billing.dc.html', page(billing, theme="dark"))
print("Entra + Billing written")
