from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN

# ---------------- Signup / trial ----------------
def step(n, label, state):
    c = {"done":"success","now":"accent","next":"neutral"}[state]
    bg = "var(--bg-sunken)" if state=="next" else f"var(--{c}-bg)"
    fg = "var(--text-tertiary)" if state=="next" else f"var(--{c}-fg)"
    mark = icon("check",13,"currentColor","3") if state=="done" else f'<span style="font-size:11px;font-weight:700;">{n}</span>'
    return ('<div style="display:flex;align-items:center;gap:8px;">'
            '<span style="width:22px;height:22px;border-radius:99px;background:%s;color:%s;display:inline-flex;'
            'align-items:center;justify-content:center;">%s</span>'
            '<span style="font-size:var(--text-sm);color:%s;font-weight:%d;">%s</span></div>'
            % (bg, fg, mark, fg, 600 if state=="now" else 500, label))

signup = f'''<div style="flex:1;display:flex;">
  <div style="flex:1;display:flex;align-items:center;justify-content:center;background:var(--bg-canvas);">
    <div style="width:440px;display:flex;flex-direction:column;gap:var(--space-5);">
      <div style="display:flex;align-items:center;gap:var(--space-2);">
        <span style="width:30px;height:30px;border-radius:9px;background:var(--brand);display:inline-flex;
          align-items:center;justify-content:center;">{icon("layers",18,"#fff","2")}</span>
        <span style="font-size:var(--text-lg);font-weight:700;letter-spacing:-.02em;">OpsHub</span></div>
      <div style="display:flex;gap:var(--space-5);">
        {step(1,"Your details","done")}{step(2,"Verify email","now")}{step(3,"Workspace","next")}</div>
      <div>
        <h1 style="margin:0;font-size:var(--text-2xl);font-weight:700;letter-spacing:-.02em;">Check your email</h1>
        <p style="margin:8px 0 0;font-size:var(--text-sm);color:var(--text-secondary);line-height:21px;">
          We sent a link to <span style="font-weight:600;color:var(--text-primary);">priya@northfield.co</span>.
          It expires in 24 hours and can be used once.</p></div>
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span class="th">Your 14-day trial includes</span>
        {"".join(f'''<div style="display:flex;align-items:center;gap:10px;font-size:var(--text-sm);">
          <span style="color:var(--success-fg);">{icon("check",15)}</span>{t}</div>'''
          for t in ["10 users and 5 GB of storage","Sheets, views, forms, dashboards and automation",
                    "Dynamic View, WorkApps, Calendar and Pivot","No card required — and no charge at expiry"])}
      </div>
      <div style="display:flex;gap:var(--space-2);">
        <button class="btn btn-secondary" style="flex:1;justify-content:center;">Resend link</button>
        <button class="btn btn-ghost">Change email</button></div>
      <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:18px;">
        At expiry your workspace becomes read-only for 7 days and your data is kept — nothing is deleted
        without you asking.</div>
    </div>
  </div>
  <div style="width:480px;flex:none;background:linear-gradient(160deg,
    color-mix(in oklch, var(--brand) 20%, var(--bg-canvas)), var(--bg-canvas));
    border-left:1px solid var(--border-subtle);padding:var(--space-9);display:flex;align-items:center;">
    <div style="display:flex;flex-direction:column;gap:var(--space-5);">
      <div style="font-size:var(--text-2xl);font-weight:700;line-height:32px;letter-spacing:-.02em;">
        Set up in minutes, not a quarter.</div>
      {"".join(f'''<div style="display:flex;gap:var(--space-3);align-items:flex-start;">
        <span style="width:28px;height:28px;border-radius:var(--radius-md);background:var(--bg-surface);
          color:var(--accent-fg);display:inline-flex;align-items:center;justify-content:center;flex:none;
          box-shadow:var(--shadow-1);">{icon(i,16)}</span>
        <div><div style="font-size:var(--text-sm);font-weight:600;">{t}</div>
        <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:18px;margin-top:2px;">{d}</div></div></div>'''
        for i,t,d in [("grid","Start from a template","Delivery, intake, vendor review and more"),
                      ("people","Invite your team","Or connect Microsoft Entra and use your directory"),
                      ("shield","Enterprise from day one","Row-level permissions, audit and SSO on every plan")])}
    </div>
  </div>
</div>'''
write('Signup.dc.html', page(signup, theme="light"))

# ---------------- Notifications + preferences ----------------
NOTIF=[("Marcus Webb mentioned you","in Cutover runbook · \\u201c@priya can you confirm the freeze window?\\u201d","people",30,"MW",120,"4m",True),
       ("Approval waiting: Cutover window","Escalates to you in 1h 48m","shield",0,"",0,"12m",True),
       ("Data migration dry run is blocked","Health changed to At risk by automation","warn",0,"",0,"1h",True),
       ("Ana Duarte shared Delivery overview","Dashboard · you have viewer access","chart",0,"AD",210,"3h",False),
       ("Weekly digest","17 changes across 3 sheets","doc",0,"",0,"Mon",False)]
nrows="".join(f'''<div style="display:flex;gap:var(--space-3);padding:var(--space-3) var(--space-4);
  border-bottom:1px solid var(--border-subtle);background:{"var(--bg-selected)" if unread else "transparent"};">
  <span style="width:28px;height:28px;border-radius:99px;background:var(--bg-sunken);color:var(--text-secondary);
    display:inline-flex;align-items:center;justify-content:center;flex:none;">{icon(ic,15)}</span>
  <div style="flex:1;min-width:0;">
    <div style="font-size:var(--text-sm);font-weight:{600 if unread else 500};">{t}</div>
    <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:3px;line-height:17px;">{d}</div></div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
    <span class="mono" style="font-size:11px;color:var(--text-tertiary);">{w}</span>
    {'<span style="width:7px;height:7px;border-radius:99px;background:var(--brand);"></span>' if unread else ''}</div>
</div>''' for t,d,ic,_,ai,ah,w,unread in NOTIF)

CATS=["Mentions","Assignments","Approvals","Shares","Due soon","Workflow failures","Comments","Digest"]
matrix="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-2) 0;
  border-bottom:1px solid var(--border-subtle);">
  <span style="flex:1;font-size:var(--text-sm);">{c}</span>
  {"".join(f'<span style="width:70px;display:flex;justify-content:center;"><span style="width:16px;height:16px;border-radius:4px;border:1.5px solid var({"--brand" if on else "--border-strong"});background:{"var(--brand)" if on else "transparent"};display:inline-flex;align-items:center;justify-content:center;">{icon("check",11,"#fff","3") if on else ""}</span></span>' for on in states)}
</div>''' for c,states in zip(CATS,[(1,1,1),(1,1,0),(1,1,1),(1,0,0),(1,1,0),(1,1,1),(1,0,0),(0,1,0)]))

notif = shell("Sheets","Notifications", chip("3 unread","accent"),
  ["Inbox","Preferences","Digest","Channels"],"Preferences",
  BTN("Mark all read","ghost","check")+BTN("Test notification","secondary","bell"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;display:flex;flex-direction:column;background:var(--bg-surface);overflow:hidden;">
      <div style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--border-default);
        display:flex;gap:8px;background:var(--bg-sunken);">
        {"".join(f'<span class="chip" style="height:26px;background:var(--{"accent-bg" if a else "bg-surface"});color:var(--{"accent-fg" if a else "text-secondary"});border:1px solid var(--{"accent-border" if a else "border-subtle"});">{n}</span>' for n,a in [("All",True),("Unread",False),("Mentions",False),("Approvals",False)])}
      </div>
      {nrows}
    </div>
    <aside style="width:420px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
      <div><span class="th">Delivery per category</span>
        <div style="display:flex;align-items:center;margin-top:var(--space-3);padding-bottom:6px;
          border-bottom:1px solid var(--border-default);">
          <span class="th" style="flex:1;">Category</span>
          {"".join(f'<span class="th" style="width:70px;text-align:center;">{n}</span>' for n in ["In-app","Email","Push"])}</div>
        {matrix}</div>
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--bg-sunken);
        border:1px solid var(--border-subtle);display:flex;flex-direction:column;gap:var(--space-2);">
        <span class="th">Quiet hours</span>
        <div style="font-size:var(--text-sm);color:var(--text-secondary);">
          22:00 – 07:00 · Europe/London</div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
          Email and push are held until the window ends. Approvals still arrive in-app.</div></div>
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--accent-bg);
        border:1px solid var(--accent-border);font-size:var(--text-xs);color:var(--accent-fg);line-height:17px;">
        Mail is delivered through your Microsoft 365 tenant (Entra), so it passes your own SPF and DMARC.</div>
    </aside>
  </div>''', crumb="Northfield Delivery / You")
write('Notifications.dc.html', page(notif, theme="dark"))
print("Signup + Notifications written")
