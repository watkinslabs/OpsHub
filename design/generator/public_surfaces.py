from _common import icon, chip, avatar, page, write

def publicpage(title, sub, body, foot, w=760):
    return f'''<div style="flex:1;display:flex;flex-direction:column;background:var(--bg-canvas);overflow:hidden;">
  <div style="height:56px;flex:none;display:flex;align-items:center;gap:var(--space-2);padding:0 var(--space-6);
    background:var(--bg-surface);border-bottom:1px solid var(--border-subtle);">
    <span style="width:26px;height:26px;border-radius:8px;background:var(--brand);display:inline-flex;
      align-items:center;justify-content:center;">{icon("layers",16,"#fff","2")}</span>
    <span style="font-size:var(--text-base);font-weight:700;">OpsHub</span>
    <span style="margin-left:auto;font-size:var(--text-xs);color:var(--text-tertiary);">
      Secure link · no account needed</span></div>
  <div style="flex:1;display:flex;justify-content:center;padding:var(--space-7) var(--space-5);overflow:hidden;">
    <div style="width:{w}px;display:flex;flex-direction:column;gap:var(--space-5);">
      <div><h1 style="margin:0;font-size:var(--text-2xl);font-weight:700;letter-spacing:-.02em;">{title}</h1>
        <p style="margin:8px 0 0;font-size:var(--text-sm);color:var(--text-secondary);line-height:21px;">{sub}</p></div>
      {body}
    </div>
  </div>
  <div style="flex:none;padding:var(--space-4) var(--space-6);border-top:1px solid var(--border-subtle);
    background:var(--bg-surface);font-size:var(--text-xs);color:var(--text-tertiary);text-align:center;">{foot}</div>
</div>'''

fields = "".join(f'''<div style="display:flex;flex-direction:column;gap:6px;">
  <span class="th">{l}</span>
  <div style="min-height:{h}px;border:1px solid var(--border-{b});border-radius:var(--radius-md);
    background:var(--bg-surface);display:flex;align-items:center;padding:var(--space-3);
    font-size:var(--text-sm);color:var(--text-{c});">{v}
    {'<span style="margin-left:auto;color:var(--text-tertiary);">'+icon("down",15)+'</span>' if d else ''}</div>
  {f'<span style="font-size:11px;color:var(--text-tertiary);">{hint}</span>' if hint else ''}</div>'''
  for l,v,h,b,c,d,hint in [
    ("Status","In review",34,"default","primary",True,"Only these three fields were shared with you"),
    ("Expected completion","24 April 2026",34,"default","primary",True,""),
    ("Evidence","security-review-v4.pdf · 2.1 MB",56,"default","secondary",False,"pdf or docx, max 25 MB")])

update = publicpage("Update requested: Vendor security review",
  "Priya Raman at Northfield Delivery asked you to update three fields. Your answer goes straight onto the record — you do not need an account.",
  f'''<div class="card" style="padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);">
    <div style="display:flex;align-items:center;gap:var(--space-3);padding-bottom:var(--space-3);
      border-bottom:1px solid var(--border-subtle);">
      {avatar("PR",30)}
      <div style="flex:1;"><div style="font-size:var(--text-sm);font-weight:600;">Priya Raman</div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);">Northfield Delivery · requested 2 days ago</div></div>
      {chip("Expires in 5 days","warning")}</div>
    <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:20px;
      padding:var(--space-3);background:var(--bg-sunken);border-radius:var(--radius-md);
      border-left:3px solid var(--brand);">
      "Could you confirm the review status and attach the signed questionnaire? We need it before the change
      board on Friday."</div>
    {fields}
    <div style="display:flex;gap:var(--space-2);">
      <button class="btn btn-primary" style="flex:1;justify-content:center;height:var(--control-lg);">Submit update</button>
      <button class="btn btn-secondary" style="height:var(--control-lg);">Save and finish later</button></div>
  </div>
  <div style="display:flex;gap:var(--space-4);">
    {"".join(f'''<div style="display:flex;gap:10px;align-items:flex-start;flex:1;">
      <span style="color:var(--success-fg);flex:none;">{icon("shield",16)}</span>
      <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:17px;">{t}</div></div>'''
      for t in ["This link works once, for you, and expires on 24 April.",
                "You can see and change only the three fields above — nothing else on the record.",
                "Your submission is recorded in the customer's audit log with your email."])}
  </div>''',
  "Powered by OpsHub · This link was sent to supplier@vendorco.com · Report a problem")
write('UpdateRequest.dc.html', page(update, theme="light"))

# ---------------- Public published dashboard ----------------
import _charts as ch
pubview = f'''<div style="flex:1;display:flex;flex-direction:column;background:var(--bg-canvas);overflow:hidden;">
  <div style="height:56px;flex:none;display:flex;align-items:center;gap:var(--space-3);padding:0 var(--space-6);
    background:var(--bg-surface);border-bottom:1px solid var(--border-subtle);">
    <span style="width:26px;height:26px;border-radius:8px;background:var(--brand);display:inline-flex;
      align-items:center;justify-content:center;">{icon("layers",16,"#fff","2")}</span>
    <span style="font-size:var(--text-base);font-weight:700;">Delivery overview</span>
    {chip("Read-only","accent")}
    <span style="margin-left:auto;display:flex;align-items:center;gap:var(--space-3);
      font-size:var(--text-xs);color:var(--text-tertiary);">
      <span style="display:inline-flex;align-items:center;gap:6px;">
        <span style="width:7px;height:7px;border-radius:99px;background:var(--success-emphasis);"></span>
        Updated 41 seconds ago</span>
      <span class="mono">Published by Northfield Delivery</span></span></div>
  <div style="flex:1;padding:var(--space-6);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
    <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:var(--space-4);">
      {"".join(f'''<div class="card" style="padding:var(--space-4);">
        <span class="th">{l}</span>
        <div style="display:flex;align-items:flex-end;gap:8px;margin-top:4px;">
          <span class="mono" style="font-size:var(--text-3xl);line-height:34px;font-weight:600;">{v}</span>
          <span class="mono" style="font-size:11px;color:var(--{c}-fg);padding-bottom:6px;">{d}</span></div></div>'''
        for l,v,d,c in [("On-time","94.2%","▲ 2.1","success"),("Open risks","17","▲ 4","danger"),
                        ("Cycle time","6.4d","▼ 0.8","success"),("Milestones","31/38","82%","accent")])}
    </div>
    <div style="display:grid;grid-template-columns:2fr 1fr;gap:var(--space-4);flex:1;min-height:0;">
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span style="font-size:var(--text-sm);font-weight:600;">Burndown — Migration programme</span>
        {ch.line(700,190,[120,116,109,104,98,88,83,74,66,57,51,44,36,31])}</div>
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span style="font-size:var(--text-sm);font-weight:600;">Work by status</span>
        <div style="display:flex;align-items:center;justify-content:center;flex:1;">{ch.donut(160,[52,23,14,11],center="1,284")}</div></div>
    </div>
  </div>
  <div style="flex:none;padding:var(--space-3) var(--space-6);border-top:1px solid var(--border-subtle);
    background:var(--bg-surface);display:flex;align-items:center;gap:var(--space-3);
    font-size:var(--text-xs);color:var(--text-tertiary);">
    <span>Renders as the publisher's permissions at request time — rows they cannot see are never counted.</span>
    <span class="mono" style="margin-left:auto;">Link expires 30 Apr 2026</span></div>
</div>'''
write('PublicView.dc.html', page(pubview, theme="dark"))
print("UpdateRequest + PublicView written")
