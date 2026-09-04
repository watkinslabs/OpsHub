from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs

# F072 Inbound email — a sheet's own address, its sender policy, and the message log.

BTN = lambda t, k="secondary", i=None: f'<button class="btn btn-{k}">{icon(i,16) if i else ""}{t}</button>'
ADDRESS = "k7m2q9x4tb6vhz3npr8sfd@in.opshub.app"


def field(label, control, hint=""):
    return f'''<div style="display:flex;flex-direction:column;gap:6px;">
      <span class="th">{label}</span>{control}
      {f'<span style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:16px;">{hint}</span>' if hint else ''}
    </div>'''


def radio(label, hint, on):
    dot = ('<span style="width:16px;height:16px;border-radius:99px;border:5px solid var(--brand);'
           'background:var(--bg-surface);flex:none;"></span>') if on else \
          ('<span style="width:16px;height:16px;border-radius:99px;border:1px solid var(--border-strong);'
           'background:var(--bg-surface);flex:none;"></span>')
    return f'''<div style="display:flex;gap:var(--space-3);align-items:flex-start;padding:var(--space-2) var(--space-3);
      border:1px solid var({"--accent-border" if on else "--border-subtle"});border-radius:var(--radius-md);
      background:var({"--bg-selected" if on else "--bg-surface"});">{dot}
      <div style="display:flex;flex-direction:column;gap:2px;">
        <span style="font-size:var(--text-sm);font-weight:{600 if on else 500};">{label}</span>
        <span style="font-size:var(--text-xs);color:var(--text-secondary);line-height:16px;">{hint}</span>
      </div></div>'''


def pill(text, kind):
    return (f'<span class="mono" style="display:inline-flex;align-items:center;height:18px;padding:0 6px;'
            f'border-radius:var(--radius-sm);font-size:10px;font-weight:500;background:var(--{kind}-bg);'
            f'color:var(--{kind}-fg);border:1px solid var(--{kind}-border);">{text}</span>')


MAPPINGS = [("Subject", "Request", "text"), ("Body", "Details", "long text"),
            ("From", "Requested by", "contact"), ("Received", "Received at", "date"),
            ("Attachments", "Row files", "file")]

mapping_rows = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-md);
  padding:0 var(--space-2);border-radius:var(--radius-sm);background:var(--bg-sunken);">
  <span style="font-size:var(--text-sm);width:92px;flex:none;color:var(--text-secondary);">{src}</span>
  <span style="color:var(--text-tertiary);">{icon("chev",13)}</span>
  <span style="font-size:var(--text-sm);font-weight:600;">{col}</span>
  <span class="mono" style="margin-left:auto;font-size:10px;color:var(--text-tertiary);">{kind}</span>
</div>''' for src, col, kind in MAPPINGS)

settings = f'''<div style="width:392px;flex:none;display:flex;flex-direction:column;gap:var(--space-4);
  overflow:hidden;">
  <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
    <div style="display:flex;align-items:center;gap:var(--space-2);">
      <span style="color:var(--accent-fg);">{icon("doc",18)}</span>
      <span style="font-size:var(--text-base);font-weight:700;">Address</span>
      {chip("Active","success")}
    </div>
    {field("Sheet address",
      f'''<div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-lg);
        padding:0 var(--space-2) 0 var(--space-3);border:1px solid var(--border-default);
        border-radius:var(--radius-md);background:var(--bg-sunken);">
        <span class="mono" style="font-size:var(--text-xs);overflow:hidden;text-overflow:ellipsis;
          white-space:nowrap;">{ADDRESS}</span>
        <button class="btn btn-secondary" style="height:var(--control-sm);margin-left:auto;flex:none;">Copy</button>
      </div>''',
      "22 random characters. Anyone holding it can write to this sheet, so it is shown only to sheet editors.")}
    <div style="display:flex;gap:var(--space-2);">{BTN("Rotate","secondary","clock")}{BTN("Revoke","ghost","warn")}</div>
  </div>

  <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
    <div style="display:flex;align-items:center;gap:var(--space-2);">
      <span style="color:var(--accent-fg);">{icon("shield",18)}</span>
      <span style="font-size:var(--text-base);font-weight:700;">Who may send</span>
    </div>
    {radio("Anyone","Any authenticated sender. Still requires SPF, DKIM and DMARC to pass.",False)}
    {radio("Tenant members only","The From address must match an active Northfield user.",True)}
    {radio("Allow list","Only the addresses and domains listed below.",False)}
    <div style="display:flex;align-items:center;gap:var(--space-2);padding-top:var(--space-1);">
      <span class="th">Authentication</span>
      <span style="margin-left:auto;font-size:var(--text-xs);color:var(--text-secondary);">DMARC failure</span>
      {chip("Reject","danger")}
    </div>
    <div style="display:flex;align-items:center;gap:var(--space-2);">
      <span class="th">Limits</span>
      <span class="mono" style="margin-left:auto;font-size:var(--text-xs);color:var(--text-secondary);">60/hour · 25 MB · 10 files</span>
    </div>
  </div>

  <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
    <div style="display:flex;align-items:center;gap:var(--space-2);">
      <span style="color:var(--accent-fg);">{icon("layers",18)}</span>
      <span style="font-size:var(--text-base);font-weight:700;">Column mapping</span>
      <span style="margin-left:auto;color:var(--text-tertiary);">{icon("plus",16)}</span>
    </div>
    <div style="display:flex;flex-direction:column;gap:var(--space-1);">{mapping_rows}</div>
    <span style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:16px;">
      A mapping that fails writes the value to the primary column and records an issue on the row.
      A message is never dropped.</span>
  </div>
</div>'''

# received, sender, subject, spf, dkim, dmarc, disposition chip kind, disposition, result
LOG = [
  ("09:14", "dana.olusegun@northfield.co", "Vendor invoice — March hosting", "pass", "pass", "pass",
   "success", "Accepted", "Row 1482 · 1 file"),
  ("09:06", "priya.raman@northfield.co", "Re: Access request for the staging tenant", "pass", "pass", "pass",
   "success", "Accepted", "Comment on row 1471"),
  ("09:02", "billing@invoice-alerts.example", "Your invoice is overdue — action required", "fail", "fail", "fail",
   "danger", "Rejected", "DMARC fail · bounced"),
  ("08:47", "noreply@partner-mail.example", "Re: Access request", "pass", "none", "none",
   "warning", "Quarantined", "Unauthenticated · held 30 days"),
  ("08:31", "adam.whitlock@northfield.co", "Hosting renewal quote", "pass", "pass", "pass",
   "success", "Accepted", "Row 1479 · 2 files"),
  ("08:12", "digest@lists.example.org", "[ops-weekly] Digest 214", "pass", "pass", "pass",
   "danger", "Rejected", "Mailing list · no bounce"),
  ("07:58", "dana.olusegun@northfield.co", "Vendor invoice — March hosting", "pass", "pass", "pass",
   "danger", "Rejected", "Rate limit · 61st this hour"),
]

COLS = [("Time", 62), ("From", 236), ("Subject", 330), ("SPF · DKIM · DMARC", 178), ("Disposition", 132), ("Result", 0)]
head = "".join(f'''<div class="th" style="{"flex:1;min-width:0;" if w == 0 else f"width:{w}px;flex:none;"}
  display:flex;align-items:center;padding:0 var(--space-3);">{n}</div>''' for n, w in COLS)


def log_row(t, frm, subj, spf, dkim, dmarc, kind, disp, result, selected=False):
    auth = "".join(pill(f"{m} {v}", "success" if v == "pass" else ("danger" if v == "fail" else "warning"))
                   for m, v in (("SPF", spf), ("DKIM", dkim), ("DMARC", dmarc)))
    return f'''<div style="display:flex;height:44px;align-items:center;border-bottom:1px solid var(--border-subtle);
      background:{"var(--bg-selected)" if selected else "transparent"};">
      <div class="mono" style="width:62px;flex:none;padding:0 var(--space-3);font-size:var(--text-xs);
        color:var(--text-tertiary);">{t}</div>
      <div style="width:236px;flex:none;padding:0 var(--space-3);display:flex;align-items:center;gap:8px;
        min-width:0;">{avatar(frm[:2].upper(), 30 + len(frm) * 7 % 300)}
        <span style="font-size:var(--text-sm);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{frm}</span></div>
      <div style="width:330px;flex:none;padding:0 var(--space-3);font-size:var(--text-sm);font-weight:500;
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{subj}</div>
      <div style="width:178px;flex:none;padding:0 var(--space-3);display:flex;gap:4px;">{auth}</div>
      <div style="width:132px;flex:none;padding:0 var(--space-3);">{chip(disp, kind)}</div>
      <div style="flex:1;min-width:0;padding:0 var(--space-3);font-size:var(--text-xs);
        color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{result}</div>
    </div>'''


rows = "".join(log_row(*r, selected=(i == 0)) for i, r in enumerate(LOG))

COUNTS = [("Accepted", "412", "success"), ("Rejected", "37", "danger"), ("Quarantined", "6", "warning")]
counts = "".join(f'''<div style="display:flex;align-items:center;gap:8px;">
  <span style="width:8px;height:8px;border-radius:99px;background:var(--{k}-emphasis);"></span>
  <span style="font-size:var(--text-xs);color:var(--text-secondary);">{n}</span>
  <span class="mono" style="font-size:var(--text-xs);font-weight:600;">{v}</span></div>''' for n, v, k in COUNTS)

log = f'''<div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:var(--space-3);">
  <div style="display:flex;align-items:center;gap:var(--space-3);">
    <span style="font-size:var(--text-lg);font-weight:700;">Message log</span>
    <span style="font-size:var(--text-xs);color:var(--text-tertiary);">Last 30 days</span>
    <div style="margin-left:auto;display:flex;align-items:center;gap:var(--space-4);">{counts}</div>
  </div>
  <div class="card" style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
    <div style="display:flex;height:34px;flex:none;background:var(--bg-sunken);
      border-bottom:1px solid var(--border-default);">{head}</div>
    {rows}
    <div style="margin-top:auto;display:flex;align-items:center;gap:var(--space-2);height:44px;
      padding:0 var(--space-3);border-top:1px solid var(--border-subtle);background:var(--bg-surface);">
      <span style="font-size:var(--text-xs);color:var(--text-secondary);">
        Rejected and quarantined messages never became rows. Bodies are stored as text and never rendered as HTML.</span>
      <span class="mono" style="margin-left:auto;font-size:var(--text-xs);color:var(--text-tertiary);">1–7 of 455</span>
    </div>
  </div>
</div>'''

body = f'''<div style="flex:1;display:flex;gap:var(--space-5);padding:var(--space-5);
  background:var(--bg-canvas);min-height:0;">{settings}{log}</div>'''

screen = topbar("") + f'''
  <div style="flex:1;display:flex;min-height:0;">
    {rail("Sheets")}
    <main style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-canvas);">
      <div style="padding:var(--space-5) var(--space-5) 0;background:var(--bg-surface);">
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-bottom:6px;">
          Northfield Delivery / Vendor intake / Settings</div>
        <div style="display:flex;align-items:center;gap:var(--space-3);">
          <h1 style="margin:0;font-size:var(--text-2xl);line-height:32px;font-weight:700;
            letter-spacing:-.02em;">Inbound email</h1>
          {chip("Sheet setting","accent")}
        </div>
      </div>
      {toolbar(tabs(["Details","Columns","Sharing","Forms","Inbound email","Automation"],"Inbound email"),
               BTN("Filter","ghost","filter") + BTN("Export log","ghost","doc") + BTN("New address","primary","plus"))}
      {body}
    </main>
  </div>'''

write('InboundEmail.dc.html', page(screen, theme="light"))
print("InboundEmail written")
