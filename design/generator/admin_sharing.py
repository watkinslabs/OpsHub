from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs, section_nav

USERS=[("Priya Raman","PR",30,"priya@northfield.co","Admin","SSO · Okta","Active","success","2m ago"),
 ("Ana Duarte","AD",210,"ana@northfield.co","Editor","SSO · Okta","Active","success","18m ago"),
 ("Marcus Webb","MW",120,"marcus@northfield.co","Editor","SSO · Okta","Active","success","1h ago"),
 ("Sam Okafor","SO",70,"sam@northfield.co","Commenter","Password + TOTP","Active","success","yesterday"),
 ("Ines Moreau","IM",160,"ines@studio-mo.fr","Guest","Link invite","Expires in 4d","warning","3d ago"),
 ("Tom Alderly","TA",300,"tom@northfield.co","Viewer","SSO · Okta","Suspended","danger","21d ago")]

subnav=[("people","Users & groups",True),("shield","Roles & permissions",False),("user","SSO & SCIM",False),
        ("layers","Integrations",False),("flow","API & webhooks",False),("doc","Audit log",False),
        ("cog","Entitlements",False),("sparkle","AI settings",False)]

side="".join(f'''<div class="rail-item{' on' if on else ''}" style="height:var(--control-md);">
  {icon(i,17)}<span style="font-size:var(--text-sm);">{n}</span></div>''' for i,n,on in subnav)

rows="".join(f'''<div style="display:flex;align-items:center;border-bottom:1px solid var(--border-subtle);
  background:{'var(--bg-surface)' if k%2==0 else 'var(--bg-sunken)'};">
  <div class="cell" style="width:44px;flex:none;justify-content:center;">
    <span style="width:14px;height:14px;border-radius:4px;border:1.5px solid var(--border-strong);"></span></div>
  <div class="cell" style="width:280px;flex:none;gap:10px;">{avatar(ini,h)}
    <div style="min-width:0;"><div style="font-weight:600;">{n}</div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);">{e}</div></div></div>
  <div class="cell" style="width:150px;flex:none;">{chip(role,"accent")}</div>
  <div class="cell" style="width:200px;flex:none;color:var(--text-secondary);">{auth}</div>
  <div class="cell" style="width:170px;flex:none;">{chip(st,stk)}</div>
  <div class="cell mono" style="width:150px;flex:none;color:var(--text-secondary);font-size:var(--text-xs);">{seen}</div>
  <div class="cell" style="flex:1;justify-content:flex-end;color:var(--text-tertiary);">{icon("dots",17)}</div>
</div>''' for k,(n,ini,h,e,role,auth,st,stk,seen) in enumerate(USERS))

admin = topbar("") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("Admin")}
    {section_nav("Administration", [(i, n, n == "Users & groups") for i, n in [("people","Users & groups"),("shield","Roles & permissions"),("user","SSO & SCIM"),("layers","Microsoft Entra"),("layers","Integrations"),("chart","Billing"),("flow","API & webhooks"),("doc","Audit log"),("cog","Entitlements"),("sparkle","MCP access")]])}

    <main style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-surface);">
      <div style="padding:var(--space-5) var(--space-5) 0;">
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">Users &amp; groups</h1>
          <span class="mono" style="font-size:var(--text-sm);color:var(--text-tertiary);">248 seats · 41 used</span>
        </div>
      </div>
      {toolbar(tabs(["Users","Groups","Invitations","Access reviews"],"Users"),
        f'<button class="btn btn-ghost">{icon("filter",16)}Role</button>'
        f'<button class="btn btn-secondary">{icon("doc",16)}Export CSV</button>'
        f'<button class="btn btn-primary">{icon("plus",16)}Invite people</button>')}
      <div style="padding:var(--space-3) var(--space-5);display:flex;gap:var(--space-2);">
        <div style="display:flex;align-items:center;gap:8px;height:var(--control-md);flex:1;max-width:340px;
          padding:0 var(--space-3);border:1px solid var(--border-default);border-radius:var(--radius-md);
          color:var(--text-tertiary);">{icon("search",16)}<span style="font-size:var(--text-sm);">Filter users</span></div>
        {chip("Guest · 1","warning")}{chip("Suspended · 1","danger")}
      </div>
      <div style="display:flex;background:var(--bg-sunken);border-top:1px solid var(--border-default);
        border-bottom:1px solid var(--border-default);height:36px;">
        {"".join(f'<div class="th" style="width:{w}px;flex:none;display:flex;align-items:center;padding:0 var(--space-3);">{c}</div>' for c,w in [("",44),("Person",280),("Role",150),("Authentication",200),("Status",170),("Last seen",150)])}
      </div>
      {rows}
      <div style="margin-top:auto;padding:var(--space-4) var(--space-5);border-top:1px solid var(--border-subtle);
        display:flex;align-items:center;gap:var(--space-3);">
        <span class="mono" style="font-size:var(--text-xs);color:var(--text-tertiary);">6 of 41</span>
        <div style="margin-left:auto;display:flex;gap:6px;">
          <button class="btn btn-secondary" style="height:var(--control-sm);">Previous</button>
          <button class="btn btn-secondary" style="height:var(--control-sm);">Next</button></div>
      </div>
    </main>
  </div>'''
write('Admin.dc.html', page(admin, theme="light"))

# ---------------- Sharing widgets sheet ----------------
def panel(title, sub, body, w="100%"):
    return f'''<div class="card" style="width:{w};padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);">
      <div><div style="font-size:var(--text-lg);font-weight:600;letter-spacing:-.01em;">{title}</div>
      <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:3px;">{sub}</div></div>{body}</div>'''

def input_row(ph, btn):
    return f'''<div style="display:flex;gap:var(--space-2);">
      <div style="flex:1;height:var(--control-md);display:flex;align-items:center;padding:0 var(--space-3);
        border:1px solid var(--border-default);border-radius:var(--radius-md);color:var(--text-tertiary);
        font-size:var(--text-sm);">{ph}</div>
      <button class="btn btn-primary">{btn}</button></div>'''

def person_row(n,i,h,role,note=""):
    return f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) 0;">
      {avatar(i,h)}<div style="flex:1;min-width:0;"><div style="font-size:var(--text-sm);font-weight:500;">{n}</div>
      {f'<div style="font-size:var(--text-xs);color:var(--text-tertiary);">{note}</div>' if note else ''}</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:var(--text-sm);color:var(--text-secondary);">
        {role}{icon("down",15)}</div></div>'''

def toggle(on, label, sub=""):
    return f'''<div style="display:flex;align-items:flex-start;gap:var(--space-3);">
      <span style="width:36px;height:20px;border-radius:99px;flex:none;margin-top:1px;
        background:{'var(--brand)' if on else 'var(--border-strong)'};display:inline-flex;align-items:center;
        padding:2px;justify-content:{'flex-end' if on else 'flex-start'};">
        <span style="width:16px;height:16px;border-radius:99px;background:#fff;box-shadow:var(--shadow-1);"></span></span>
      <div><div style="font-size:var(--text-sm);font-weight:500;">{label}</div>
      {f'<div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;line-height:16px;">{sub}</div>' if sub else ''}</div></div>'''

link_box = f'''<div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-3);
  background:var(--bg-sunken);border:1px solid var(--border-subtle);border-radius:var(--radius-md);">
  <span class="mono" style="font-size:var(--text-xs);color:var(--text-secondary);flex:1;overflow:hidden;
    text-overflow:ellipsis;white-space:nowrap;">opshub.io/public/share/8fJ2q…7Kd</span>
  <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Copy</button></div>'''

share = f'''
  <div style="padding:var(--space-7);display:flex;flex-direction:column;gap:var(--space-6);
    background:var(--bg-canvas);height:100%;overflow:hidden;">
    <div>
      <h1 style="margin:0;font-size:var(--text-2xl);font-weight:700;letter-spacing:-.02em;">Sharing &amp; distribution</h1>
      <p style="margin:6px 0 0;font-size:var(--text-sm);color:var(--text-secondary);max-width:680px;">
        One share system across sheets, views, reports, dashboards and documents (F036). Publishing and embedding
        are F059; update requests are F061. Every surface below is permission-scoped and token-revocable.</p>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3, minmax(0,1fr));gap:var(--space-5);flex:1;min-height:0;">
      {panel("Share","Sheet · Cutover plan", input_row("Add people, groups or emails","Invite") +
        f'''<div>{person_row("Priya Raman","PR",30,"Owner")}{person_row("Ana Duarte","AD",210,"Editor")}
        {person_row("Ines Moreau","IM",160,"Viewer","Guest · expires Apr 12")}
        {person_row("Delivery team","DT",255,"Commenter","14 members")}</div>''' +
        f'<div style="height:1px;background:var(--border-subtle);"></div>' +
        toggle(True,"Anyone with the link can view","Read-only, expires in 30 days, revocable at any time") +
        link_box)}
      {panel("Publish","Dashboard · Delivery overview",
        toggle(True,"Published","Renders as the publisher's permissions at request time") +
        link_box +
        toggle(True,"Allow embedding","Restricted to 2 allowed origins") +
        f'''<div style="padding:var(--space-3);background:var(--bg-sunken);border-radius:var(--radius-md);
          border:1px solid var(--border-subtle);"><div class="th" style="margin-bottom:6px;">Embed snippet</div>
          <div class="mono" style="font-size:11px;color:var(--text-secondary);line-height:16px;">
          &lt;iframe src="opshub.io/embed/8fJ2q…"<br>&nbsp;&nbsp;width="960" height="600"&gt;&lt;/iframe&gt;</div></div>''' +
        f'''<div style="display:flex;gap:var(--space-4);font-size:var(--text-xs);color:var(--text-tertiary);">
          <span class="mono">1,204 views · 7d</span><span class="mono">Expires Apr 30</span></div>''')}
      {panel("Request an update","Row · Vendor security review",
        f'''<div style="display:flex;flex-direction:column;gap:var(--space-3);">
          {person_row("supplier@vendorco.com","VC",95,"Recipient","No OpsHub account needed")}
          <div><span class="th">Fields they can edit</span>
          <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;">
            {chip("Status","accent")}{chip("Due date","accent")}{chip("Attachment","accent")}
            <span class="chip" style="background:var(--bg-sunken);color:var(--text-tertiary);
              border:1px dashed var(--border-strong);">+ add field</span></div></div>
        </div>''' +
        toggle(True,"Send reminders","Every 3 days until answered, max 3") +
        toggle(False,"Allow partial submission","Recipient can save and return later") +
        f'''<div style="margin-top:auto;display:flex;gap:var(--space-2);">
          <button class="btn btn-primary" style="flex:1;justify-content:center;">Send request</button>
          <button class="btn btn-secondary">Preview</button></div>''')}
    </div>
    <div style="display:grid;grid-template-columns:repeat(3, minmax(0,1fr));gap:var(--space-5);height:150px;">
      {panel("Guest access","External collaborator",
        f'<div style="display:flex;align-items:center;gap:var(--space-3);">{avatar("IM",160)}'
        f'<div style="flex:1;"><div style="font-size:var(--text-sm);font-weight:600;">Ines Moreau</div>'
        f'<div style="font-size:var(--text-xs);color:var(--text-tertiary);">Scoped to 1 sheet · no tenant discovery</div></div>'
        f'{chip("Expires in 4d","warning")}</div>')}
      {panel("Revocation","Active tokens",
        f'''<div style="display:flex;align-items:center;gap:var(--space-3);">
          <span class="mono" style="font-size:var(--text-2xl);font-weight:600;">7</span>
          <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:16px;">
            live share links across 4 resources</div>
          <button class="btn btn-secondary" style="margin-left:auto;height:var(--control-sm);
            color:var(--danger-fg);border-color:var(--danger-border);">Revoke all</button></div>''')}
      {panel("Audit","Every access recorded",
        f'''<div style="display:flex;flex-direction:column;gap:6px;font-size:var(--text-xs);color:var(--text-secondary);">
          <div class="mono">14:02 · share.granted · ana@…</div>
          <div class="mono">13:41 · publication.viewed · anon</div>
          <div class="mono">11:20 · share-link.revoked · priya@…</div></div>''')}
    </div>
  </div>'''
write('Sharing.dc.html', page(share, theme="light", size=(1440,1120)))
print("Admin + Sharing written")
