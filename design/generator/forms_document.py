from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN

# ---------------- Form builder + public form ----------------
def fld(label, kind, req=False, hint=""):
    return f'''<div class="card" style="padding:var(--space-3);display:flex;align-items:center;gap:var(--space-3);">
      <span style="color:var(--text-tertiary);cursor:grab;">{icon("dots",16)}</span>
      <div style="flex:1;"><div style="font-size:var(--text-sm);font-weight:600;">{label}
        {'<span style="color:var(--danger-fg);"> *</span>' if req else ''}</div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;">{kind}{" · "+hint if hint else ""}</div></div>
      <span style="color:var(--text-tertiary);">{icon("cog",15)}</span></div>'''

palette="".join(f'''<div style="display:flex;align-items:center;gap:8px;height:var(--control-md);padding:0 var(--space-2);
  border:1px solid var(--border-subtle);border-radius:var(--radius-md);background:var(--bg-surface);
  font-size:var(--text-sm);color:var(--text-secondary);">{icon(i,15)}{n}</div>'''
  for i,n in [("doc","Short text"),("doc","Long text"),("down","Dropdown"),("check","Checkbox"),
              ("calendar","Date"),("user","Person"),("chart","Number"),("layers","Attachment")])

preview = f'''<div style="width:380px;flex:none;background:var(--bg-sunken);padding:var(--space-5);
  display:flex;flex-direction:column;gap:var(--space-3);overflow:hidden;">
  <span class="th">Live preview</span>
  <div class="card" style="padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);
    box-shadow:var(--shadow-2);">
    <div><div style="font-size:var(--text-xl);font-weight:700;letter-spacing:-.01em;">Vendor intake</div>
      <div style="font-size:var(--text-sm);color:var(--text-secondary);margin-top:4px;line-height:19px;">
        Tell us about the vendor and we will start the security review.</div></div>
    {"".join(f'''<div style="display:flex;flex-direction:column;gap:5px;"><span class="th">{l}</span>
      <div style="height:var(--control-md);border:1px solid var(--border-default);border-radius:var(--radius-md);
        background:var(--bg-surface);display:flex;align-items:center;padding:0 var(--space-3);
        font-size:var(--text-sm);color:var(--text-tertiary);">{p}</div></div>''' for l,p in
      [("Vendor name","Acme Analytics"),("Contact email","you@vendor.com"),("Data classification","Select…")])}
    <button class="btn btn-primary" style="justify-content:center;">Submit request</button>
    <div style="font-size:11px;color:var(--text-tertiary);text-align:center;">Powered by OpsHub · no account needed</div>
  </div>
</div>'''

form = shell("Sheets","Vendor intake", chip("Published","success"),
  ["Build","Settings","Responses","Share"],"Build",
  BTN("Preview","ghost","search")+BTN("Unpublish","ghost")+BTN("Copy link","secondary","people")+BTN("Save","primary","check"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:236px;flex:none;border-right:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-2);">
      <span class="th">Field types</span>{palette}</div>
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-3);
      background:var(--bg-canvas);overflow:hidden;">
      <span class="th">Fields · drag to reorder</span>
      {fld("Vendor name","Short text",True)}
      {fld("Contact email","Short text",True,"validated as email")}
      {fld("Data classification","Dropdown",True,"Public · Internal · Confidential")}
      {fld("Expected go-live","Date")}
      {fld("Security questionnaire","Attachment",False,"pdf, docx · max 25 MB")}
      <div style="height:44px;border:1px dashed var(--border-strong);border-radius:var(--radius-md);
        display:flex;align-items:center;justify-content:center;gap:8px;color:var(--text-tertiary);
        font-size:var(--text-sm);">{icon("plus",15)}Drop a field here</div>
    </div>
    {preview}
  </div>''', crumb="Northfield Delivery / Vendors / Forms")
write('Forms.dc.html', page(form, theme="light"))

# ---------------- Document editor with live collaboration ----------------
para = lambda t, s="": f'<p style="margin:0 0 var(--space-4);font-size:15px;line-height:26px;color:var(--text-primary);{s}">{t}</p>'
doc_body = f'''
  <div style="flex:1;display:flex;min-height:0;">
    <div style="width:236px;flex:none;border-right:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-1);">
      <span class="th" style="margin-bottom:6px;">Outline</span>
      {"".join(f'<div style="padding:6px var(--space-2);border-radius:var(--radius-sm);font-size:var(--text-sm);color:var(--text-{"primary" if a else "secondary"});background:{"var(--bg-selected)" if a else "transparent"};font-weight:{600 if a else 400};padding-left:{12 if l==1 else 24}px;">{n}</div>' for n,l,a in [("Cutover runbook",1,False),("Preconditions",2,True),("Freeze window",2,False),("Migration steps",2,False),("Verification",2,False),("Rollback",2,False)])}
    </div>
    <div style="flex:1;overflow:hidden;display:flex;justify-content:center;padding:var(--space-7) var(--space-5);
      background:var(--bg-canvas);">
      <div style="width:720px;">
        <h1 style="margin:0 0 var(--space-2);font-size:32px;line-height:40px;font-weight:700;letter-spacing:-.025em;">Cutover runbook</h1>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:var(--space-6);font-size:var(--text-xs);
          color:var(--text-tertiary);">Last edited 2 minutes ago by Ana Duarte · v12</div>
        <h2 style="margin:0 0 var(--space-3);font-size:20px;line-height:28px;font-weight:600;">Preconditions</h2>
        {para('Every item below must be green before the freeze window opens. The migration lead confirms each one in the linked sheet and records the operator who verified it.')}
        {para('<span style="background:color-mix(in oklch, var(--brand) 18%, transparent);border-bottom:2px solid var(--brand);">Pilot tenant provisioning is complete and the smoke suite passed on the pilot data set.</span><span style="display:inline-flex;align-items:center;gap:4px;margin-left:8px;vertical-align:middle;"><span style="width:2px;height:18px;background:#0e9aa7;display:inline-block;"></span><span style="font-size:10px;font-weight:700;color:#fff;background:#0e9aa7;padding:1px 5px;border-radius:3px;">Ana</span></span>')}
        {para('Backups verified with a restore drill inside the last seven days, evidence stored under the release folder.')}
        <div style="border-left:3px solid var(--warning-emphasis);background:var(--warning-bg);padding:var(--space-3) var(--space-4);
          border-radius:0 var(--radius-md) var(--radius-md) 0;margin-bottom:var(--space-4);">
          <div style="font-size:var(--text-sm);font-weight:600;color:var(--warning-fg);">Blocking</div>
          <div style="font-size:var(--text-sm);color:var(--text-secondary);margin-top:2px;line-height:20px;">
            Data migration dry run is still failing on the vendor table. Do not open the freeze window.</div></div>
        {para('If any precondition fails, the cutover is postponed to the next window and this document is updated before the postponement is announced.')}
      </div>
    </div>
    <aside style="width:300px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
      display:flex;flex-direction:column;">
      <div style="padding:var(--space-4);border-bottom:1px solid var(--border-subtle);display:flex;
        align-items:center;gap:8px;">
        <span style="font-size:var(--text-sm);font-weight:600;">Comments</span>
        {chip("3 open","accent")}</div>
      <div style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
        {"".join(f'''<div style="display:flex;gap:var(--space-2);">{avatar(i,h)}
          <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:baseline;gap:6px;">
              <span style="font-size:var(--text-sm);font-weight:600;">{n}</span>
              <span style="font-size:11px;color:var(--text-tertiary);">{w}</span></div>
            <div style="font-size:var(--text-sm);color:var(--text-secondary);line-height:19px;margin-top:3px;">{t}</div>
            {'<div style="margin-top:6px;display:flex;gap:6px;"><button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Reply</button><button class="btn btn-ghost" style="height:var(--control-sm);font-size:var(--text-xs);">Resolve</button></div>' if r else ''}
          </div></div>'''
          for i,h,n,w,t,r in [("PR",30,"Priya Raman","2h","Can we cite the restore-drill evidence path here rather than the folder?",True),
                              ("MW",120,"Marcus Webb","1h","The vendor table failure is a mapping bug, not data. Retest tonight.",True)])}
      </div>
      <div style="margin-top:auto;padding:var(--space-4);border-top:1px solid var(--border-subtle);">
        <div style="height:64px;border:1px solid var(--border-default);border-radius:var(--radius-md);
          padding:var(--space-3);font-size:var(--text-sm);color:var(--text-tertiary);">Comment or @mention…</div>
      </div>
    </aside>
  </div>'''

doc = topbar("") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("Documents")}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;">
      <div style="padding:var(--space-5) var(--space-5) 0;background:var(--bg-surface);">
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;letter-spacing:-.02em;">Cutover runbook</h1>
          <span style="display:flex;align-items:center;gap:6px;margin-left:auto;">
            <span style="display:flex;">{avatar("AD",210)}{avatar("PR",30)}{avatar("MW",120)}</span>
            <span style="font-size:var(--text-xs);color:var(--success-fg);display:inline-flex;align-items:center;gap:5px;">
              <span style="width:7px;height:7px;border-radius:99px;background:var(--success-emphasis);"></span>3 editing</span>
          </span>
        </div>
      </div>
      {toolbar(tabs(["Document","Versions","Attachments","Permissions"],"Document"),
        BTN("Version history","ghost","clock")+BTN("Export","ghost","doc")+BTN("Share","secondary","people")+BTN("Request review","primary","check"))}
      {doc_body}
    </main>
  </div>'''
write('Document.dc.html', page(doc, theme="light"))
print("Forms + Document written")
