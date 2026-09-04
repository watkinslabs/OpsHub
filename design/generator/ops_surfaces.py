from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
from entra_billing import adminshell, field, toggle
import _charts as ch

TH = lambda t, w=None: f'<span class="th" style="{f"width:{w}px;flex:none;" if w else "flex:1;"}">{t}</span>'
MONO = lambda t, s="var(--text-sm)", c="--text-primary": f'<span class="mono" style="font-size:{s};color:var({c});">{t}</span>'

def panel(title, right, inner, pad="var(--space-4)"):
    return f'''<div class="card" style="display:flex;flex-direction:column;min-height:0;">
      <div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-3) {pad};
        border-bottom:1px solid var(--border-subtle);">
        <span style="font-size:var(--text-sm);font-weight:600;">{title}</span>
        <span style="margin-left:auto;display:flex;align-items:center;gap:var(--space-2);">{right}</span></div>
      <div style="padding:{pad};display:flex;flex-direction:column;gap:var(--space-3);min-height:0;overflow:hidden;">
        {inner}</div></div>'''

def note(kind, ic, head, body, actions=""):
    return f'''<div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--{kind}-bg);
      border:1px solid var(--{kind}-border);">
      <div style="display:flex;align-items:center;gap:8px;color:var(--{kind}-fg);">{icon(ic,16)}
        <span style="font-size:var(--text-sm);font-weight:600;">{head}</span></div>
      <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:6px;line-height:17px;">{body}</div>
      {f'<div style="display:flex;gap:6px;margin-top:var(--space-3);">{actions}</div>' if actions else ''}</div>'''

SKEL = lambda w: (f'<span style="display:inline-block;width:{w}px;height:8px;border-radius:var(--radius-sm);'
                  f'background:var(--bg-active);"></span>')
ELL = lambda t: (f'<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{t}</span>')

# ================= F019 — Workflow runs =================
RUNS = [("01JQ8F2K7Y", "row.updated · Requests", "completed", "success", "4.2 s", "09:41:02", 0),
        ("01JQ8E9M4T", "webhook · tok_9fa2", "dead_lettered", "danger", "15 m 04 s", "09:12:55", 1),
        ("01JQ8D1P0R", "schedule · daily 09:00", "running", "accent", "6.8 s", "09:00:00", 0),
        ("01JQ8C7W3B", "approval.decided", "queued", "warning", "—", "08:58:31", 2),
        ("01JQ8B4H8N", "row.created · Requests", "completed", "success", "2.9 s", "08:44:10", 0),
        ("01JQ8A0V6C", "form.submitted · Intake", "cancelled", "warning", "1.1 s", "08:30:07", 0),
        ("01JQ89X2D9", "row.updated · Requests", "completed", "success", "3.4 s", "08:21:44", 0)]

runrows = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);height:var(--row-h);
  padding:0 var(--space-3);border-bottom:1px solid var(--border-subtle);
  background:{'var(--bg-selected)' if k=='danger' else 'transparent'};
  border-left:2px solid {'var(--brand)' if k=='danger' else 'transparent'};">
  {MONO(i, "11px", "--text-secondary")}
  <span style="flex:1;font-size:var(--text-sm);color:var(--text-secondary);overflow:hidden;
    text-overflow:ellipsis;white-space:nowrap;">{t}</span>
  {SKEL(58) if sk==2 else chip(s, k)}
  {MONO(d, "var(--text-xs)", "--text-tertiary")}
  <span style="width:52px;text-align:right;">{MONO(at, "11px", "--text-tertiary")}</span></div>'''
  for i, t, s, k, d, at, sk in RUNS)

STEPS = [("1", "match_trigger", "completed", "success", "12 ms", "1 / 1",
          "event row.updated.v1 · Status → Approved", "{ matched: true, version_no: 7 }"),
         ("2", "update_fields", "completed", "success", "240 ms", "1 / 5",
          "{ Owner: \"Dana Whitlock\", Reviewed: \"2026-09-03\" }", "{ row_version: 41, cells_written: 2 }"),
         ("3", "send_in_app", "completed", "success", "86 ms", "1 / 5",
          "{ to: \"dana@northfield.co\", template: \"assigned\" }", "{ notification_id: \"ntf_7c31\" }"),
         ("4", "call_webhook", "failed", "danger", "30.0 s", "5 / 5",
          "POST https://hooks.contoso.example/ops · HMAC-SHA256", "—")]

steprows = "".join(f'''<div style="display:flex;gap:var(--space-3);padding:var(--space-3) 0;
  border-bottom:1px solid var(--border-subtle);">
  <div style="width:22px;flex:none;display:flex;flex-direction:column;align-items:center;gap:4px;">
    <span style="width:22px;height:22px;border-radius:var(--radius-full);background:var(--{k}-bg);
      border:1px solid var(--{k}-border);color:var(--{k}-fg);display:inline-flex;align-items:center;
      justify-content:center;">{icon("check" if k=="success" else "warn",13)}</span>
    <span style="flex:1;width:1px;background:var(--border-default);"></span></div>
  <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:6px;">
    <div style="display:flex;align-items:center;gap:8px;">
      <span style="font-size:var(--text-sm);font-weight:600;">{n}. {kind}</span>{chip(s,k)}
      <span style="margin-left:auto;display:flex;gap:var(--space-3);">
        {MONO("attempt "+att, "11px", "--text-tertiary")}{MONO(ms, "11px", "--text-secondary")}</span></div>
    <div style="display:grid;grid-template-columns:64px 1fr;gap:4px var(--space-2);align-items:start;">
      <span class="th">Input</span>{MONO(inp, "11px", "--text-secondary")}
      <span class="th">Output</span>{MONO(out, "11px", "--text-secondary")}</div>
  </div></div>''' for n, kind, s, k, ms, att, inp, out in STEPS)

runs_body = f'''<div style="flex:1;display:flex;min-height:0;background:var(--bg-canvas);gap:var(--space-4);
  padding:var(--space-4);">
  <div style="width:430px;flex:none;display:flex;flex-direction:column;gap:var(--space-3);min-height:0;">
    {panel("Runs", MONO("1,284 in 24 h", "11px", "--text-tertiary"),
      f'''<div style="display:flex;gap:var(--space-2);">
        {"".join(f'<span style="font-size:var(--text-xs);font-weight:600;padding:3px var(--space-2);border-radius:var(--radius-full);background:var(--{c});color:var(--{fg});">{t}</span>' for t,c,fg in [("All","bg-active","text-primary"),("Failed","bg-sunken","text-secondary"),("Dead letter","bg-sunken","text-secondary"),("Queued","bg-sunken","text-secondary")])}
        <span style="margin-left:auto;display:flex;align-items:center;gap:6px;color:var(--text-tertiary);
          font-size:var(--text-xs);">{icon("clock",14)}polling · 5 s</span></div>
      <div style="margin:0 calc(-1 * var(--space-4));">{runrows}</div>
      {note("warning","clock","3 runs queued behind the tenant quota",
            "100 concurrent runs in flight. Queued runs are dequeued round-robin and are not failures.")}''', "var(--space-4)")}
  </div>
  <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:var(--space-3);">
    {panel("Run 01JQ8E9M4T", chip("dead_lettered","danger") + BTN("Cancel","ghost") + BTN("Replay from step 4","primary","clock"),
      f'''<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:var(--space-3);">
        {"".join(f'<div><span class="th">{l}</span><div style="margin-top:3px;">{MONO(v,"var(--text-sm)")}</div></div>' for l,v in [("Workflow","Assign on approve"),("Version","v7 (pinned)"),("Trigger","webhook_received"),("Duration","15 m 04 s"),("Correlation","cor_3f81a9")])}
      </div>
      <div style="height:1px;background:var(--border-subtle);"></div>
      <div style="overflow:hidden;">{steprows}</div>
      {note("danger","warn","Step 4 failed · error_code action_failed",
        "<span class='mono'>502 Bad Gateway from https://hooks.contoso.example/ops after 30.0 s</span><br>"
        "Attempts 1–5 backed off 5 s, 10 s, 20 s, 40 s, 15 m (capped). Dead-lettered at 09:27:59 and retryable for 30 days.",
        BTN("Replay from step 4","secondary","clock") + BTN("Copy correlation ID","ghost","doc") + BTN("Open dead-letter queue","ghost"))}''')}
  </div></div>'''

write('WorkflowRuns.dc.html', page(shell("Automation", "Runs",
  chip("Assign on approve · v7", "accent"), ["Runs", "Definition", "Triggers", "Inbound webhook"], "Runs",
  BTN("Status: all", "ghost", "filter") + BTN("Failure class", "ghost", "warn") + BTN("Last 24 h", "ghost", "calendar")
  + BTN("Export runs", "secondary", "doc"), runs_body,
  crumb="Northfield Delivery / Automation"), theme="dark"))

# ================= F022 — Metrics =================
FILTERS = [("Risks · Status", "is any of", "Open, Mitigating"), ("Risks · Severity", "is any of", "High, Critical"),
           ("Risks · Programme", "is", "Migration programme")]
fil = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-md);
  padding:0 var(--space-2);border:1px solid var(--border-default);border-radius:var(--radius-md);
  background:var(--bg-surface);font-size:var(--text-sm);">
  <span style="color:var(--text-secondary);">{a}</span>
  <span style="color:var(--text-tertiary);font-size:var(--text-xs);">{op}</span>
  <span style="font-weight:600;">{v}</span>
  <span style="margin-left:auto;color:var(--text-tertiary);">{icon("dots",15)}</span></div>''' for a, op, v in FILTERS)

SERIES = [11, 12, 10, 13, 15, 14, 12, 11, 13, 10, 9, 11, 12, 10, 9, 8, 10, 9, 7]
MRUNS = [("run_9d21", "succeeded", "success", "8.4 s", "12,481", "09:35"), ("run_9c07", "succeeded", "success", "7.9 s", "12,455", "08:35"),
         ("run_9b93", "failed", "danger", "30.0 s", "—", "07:35")]
mrun = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-2);padding:6px 0;
  border-bottom:1px solid var(--border-subtle);font-size:var(--text-xs);">
  {MONO(i,"11px","--text-secondary")}{chip(s,k)}
  <span style="margin-left:auto;display:flex;gap:var(--space-3);">{MONO(d,"11px","--text-tertiary")}
  {MONO(r+" rows","11px","--text-tertiary")}{MONO(at,"11px","--text-tertiary")}</span></div>''' for i, s, k, d, r, at in MRUNS)

DASH = [("Weekly review", "KPI tile", "Dana Whitlock", "DW", 30), ("Programme health", "Trend chart", "Priya Rao", "PR", 90),
        ("Exec summary", "KPI tile", "Sam Okafor", "SO", 200)]
dash = "".join(f'''<div style="display:flex;align-items:center;gap:8px;padding:var(--space-2) 0;
  border-bottom:1px solid var(--border-subtle);">
  <span style="color:var(--text-tertiary);">{icon("chart",15)}</span>
  <span style="font-size:var(--text-sm);font-weight:500;">{n}</span>
  <span style="font-size:var(--text-xs);color:var(--text-tertiary);">{u}</span>
  <span style="margin-left:auto;display:flex;align-items:center;gap:6px;">{avatar(ini,h)}</span></div>''' for n, u, o, ini, h in DASH)

met_body = f'''<div style="flex:1;display:flex;min-height:0;background:var(--bg-canvas);gap:var(--space-4);
  padding:var(--space-4);">
  <div style="width:340px;flex:none;display:flex;flex-direction:column;gap:var(--space-3);">
    {panel("Definition", chip("draft changes","warning"),
      f'''{field("Source","Report · Portfolio status","Latest succeeded snapshot 09:30")}
      <div style="display:flex;gap:var(--space-3);">{field("Measure","count","","default","50%")}
        {field("Column","—","not required for count","default","50%")}</div>
      <div style="display:flex;gap:var(--space-3);">{field("Period grain","week","","default","50%")}
        {field("Week starts","Monday","","default","50%")}</div>
      {field("Timezone","America/New_York","Buckets align to this zone")}
      <div style="display:flex;gap:var(--space-3);">{field("Comparison","previous_period","","default","55%")}
        {field("Target","5 · down is good","","default","45%")}</div>
      {toggle(False,"Owner scope","Blocked: tenant policy reports.aggregate_hidden_values is off")}''')}
  </div>
  <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:var(--space-3);">
    {panel("Filter conditions", BTN("Add condition","ghost","plus"),
      f'''{fil}<div style="font-size:var(--text-xs);color:var(--text-tertiary);">
        3 of 50 predicates · depth 1 of 4</div>''')}
    <div class="card" style="padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:var(--text-sm);font-weight:600;">Open high risks</span>
        {chip("stale · updated 09:35","warning")}
        <span style="margin-left:auto;font-size:var(--text-xs);color:var(--text-tertiary);">
          week of 31 Aug · complete bucket</span></div>
      <div style="display:flex;align-items:flex-end;gap:var(--space-5);">
        <span class="mono" style="font-size:52px;line-height:52px;font-weight:700;flex:none;">7</span>
        <div style="padding-bottom:6px;display:flex;flex-direction:column;gap:3px;flex:none;white-space:nowrap;">
          <span style="font-size:var(--text-base);font-weight:600;color:var(--success-fg);">▼ down 2 vs last week</span>
          <span style="font-size:var(--text-xs);color:var(--text-tertiary);">−22.2% · target 5 · down is good</span></div>
        <div style="margin-left:auto;flex:none;">{ch.line(210,70,SERIES)}</div></div>
      <div style="display:flex;align-items:center;gap:var(--space-3);">
        <div style="flex:1;height:6px;border-radius:99px;background:var(--bg-sunken);">
          <div style="width:71%;height:100%;border-radius:99px;background:var(--brand);"></div></div>
        <span style="white-space:nowrap;">{MONO("7 of target 5","11px","--text-tertiary")}</span></div>
      <div style="display:flex;align-items:center;gap:var(--space-3);padding-top:var(--space-3);
        border-top:1px solid var(--border-subtle);">
        <span style="font-size:var(--text-xs);color:var(--text-tertiary);">
          52 weekly buckets · scope viewer · sample 12,481 rows</span>
        <span style="margin-left:auto;display:flex;align-items:center;gap:var(--space-3);">
          <span style="font-size:var(--text-xs);color:var(--text-tertiary);">week of 7 Sep</span>
          {SKEL(52)}{chip("computing","accent")}</span></div>
    </div>
    {panel("Weekly values", MONO("last 12 complete buckets · count","11px","--text-tertiary"),
      f'''<div>{ch.bars(430,96,SERIES[-12:],labels=["21","28","5","12","19","26","2","9","16","23","30","6"])}</div>
      <div style="display:flex;align-items:center;gap:var(--space-3);font-size:var(--text-xs);
        color:var(--text-tertiary);">
        <span>Rolled up from week to month by sum; count_distinct would be recomputed, never summed.</span>
        <span style="margin-left:auto;white-space:nowrap;">min 7 · max 15 · avg 11.1</span></div>''')}
  </div>
  <div style="width:300px;flex:none;display:flex;flex-direction:column;gap:var(--space-3);">
    {panel("Recompute", chip("queued","accent"),
      f'''<div style="display:flex;align-items:center;gap:8px;">
        <div style="flex:1;height:6px;border-radius:99px;background:var(--bg-sunken);overflow:hidden;">
          <div style="width:34%;height:100%;background:var(--brand);"></div></div>{MONO("34%","11px","--text-tertiary")}</div>
      <span style="font-size:var(--text-xs);color:var(--text-tertiary);">run_9e08 · 18 of 52 buckets · scope_key sc_4471</span>
      <div style="height:1px;background:var(--border-subtle);"></div>{mrun}
      {note("danger","warn","run_9b93 failed · render_timeout",
            "Source snapshot replaced mid-run.", BTN("Retry","secondary","clock"))}''')}
    {panel("Used by", MONO("3 dashboards","11px","--text-tertiary"), dash)}
  </div></div>'''

write('Metrics.dc.html', page(shell("Dashboards", "Open high risks",
  chip("metric · week", "accent"), ["Definition", "Values", "History", "Permissions"], "Definition",
  BTN("Preview", "ghost", "chart") + BTN("Recompute", "secondary", "clock") + BTN("Save", "primary", "check"),
  met_body, crumb="Northfield Delivery / Metrics"), theme="light"))

# ================= F025 — Exports =================
EXP = [("exp_7f21", "Weekly review", "PDF · A4 landscape", "completed", "success", "4 pages", "2.1 MB", 100),
       ("exp_7f18", "Portfolio status", "XLSX", "running", "accent", "48,210 rows", "—", 62),
       ("exp_7f12", "Risk register", "CSV", "queued", "warning", "—", "—", 0),
       ("exp_7f04", "Programme costs", "CSV", "failed", "danger", "—", "—", 0),
       ("exp_7ef9", "Exec summary", "PNG · 1440×1024", "completed", "success", "1 page", "780 KB", 100),
       ("exp_7ee2", "Audit extract", "XLSX", "expired", "warning", "112,004 rows", "18 MB", 100)]
exprows = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);height:var(--row-h);
  padding:0 var(--space-3);border-bottom:1px solid var(--border-subtle);
  background:{'var(--bg-selected)' if i=='exp_7f21' else 'transparent'};">
  {MONO(i,"11px","--text-secondary")}
  <span style="width:150px;flex:none;font-size:var(--text-sm);font-weight:500;">{n}</span>
  <span style="flex:1;font-size:var(--text-xs);color:var(--text-tertiary);">{f}</span>
  <span style="width:120px;flex:none;">{MONO(r,"var(--text-xs)","--text-secondary")}</span>
  <span style="width:72px;flex:none;">{MONO(b,"var(--text-xs)","--text-tertiary")}</span>
  <div style="width:70px;flex:none;height:5px;border-radius:99px;background:var(--bg-sunken);">
    <div style="width:{p}%;height:100%;border-radius:99px;background:var(--{k}-emphasis);"></div></div>
  <span style="width:96px;flex:none;display:flex;justify-content:flex-end;">{chip(s,k)}</span></div>'''
  for i, n, f, s, k, r, b, p in EXP)

DRILL = [("RSK-118", "Vendor certification lapse", "Risks · Migration", "allowed", "Critical"),
         ("RSK-121", "Data residency gap", "Risks · Migration", "allowed", "High"),
         ("RSK-124", "Cutover rollback untested", "Risks · Migration", "allowed", "High"),
         ("RSK-130", "Third-party SLA breach", "Risks · Partner portal", "denied", "—"),
         ("RSK-133", "Key person dependency", "Risks · Migration", "allowed", "High")]
drill = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);height:var(--row-h);
  padding:0 var(--space-3);border-bottom:1px solid var(--border-subtle);
  opacity:{'.62' if a=='denied' else '1'};">
  {MONO(rid,"11px","--text-secondary")}
  <span style="flex:1;font-size:var(--text-sm);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{t}</span>
  <span style="width:180px;flex:none;font-size:var(--text-xs);color:var(--text-tertiary);">{src}</span>
  <span style="width:80px;flex:none;">{MONO(sev,"var(--text-xs)","--text-secondary")}</span>
  <span style="width:104px;flex:none;display:flex;justify-content:flex-end;">
    {chip("No access","danger") if a=="denied" else f'<a style="font-size:var(--text-xs);font-weight:600;">Open row</a>'}</span></div>'''
  for rid, t, src, a, sev in DRILL)

exp_body = f'''<div style="flex:1;display:flex;min-height:0;background:var(--bg-canvas);gap:var(--space-4);
  padding:var(--space-4);">
  <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:var(--space-3);">
    {panel("Export centre", MONO("6 exports · 3 running of 3 allowed","11px","--text-tertiary"),
      f'''<div style="display:flex;gap:var(--space-3);padding:0 var(--space-3);">
        {TH("Export",84)}{TH("Source",150)}{TH("Format")}{TH("Rows / pages",120)}{TH("Size",72)}{TH("Progress",70)}
        <span class="th" style="width:96px;flex:none;text-align:right;">Status</span></div>
      <div style="margin:0 calc(-1 * var(--space-4));">{exprows}</div>''')}
    {panel("Drill-through · Weekly review › Dana — 7 risks",
      chip("snapshot 09:30 · scope viewer","accent") + BTN("Reload","ghost","clock"),
      f'''<div style="display:flex;gap:var(--space-3);padding:0 var(--space-3);">
        {TH("Row",84)}{TH("Title")}{TH("Source sheet",180)}{TH("Severity",80)}
        <span class="th" style="width:104px;flex:none;text-align:right;">Access</span></div>
      <div style="margin:0 calc(-1 * var(--space-4));">{drill}</div>
      <div style="display:flex;align-items:center;gap:8px;font-size:var(--text-xs);color:var(--text-tertiary);">
        <span>Showing 5 of 7 · 1 row counted but not visible · 2 columns hidden (Cost, Owner notes)</span>
        <span style="margin-left:auto;">{chip("aggregate scope owner","warning")}</span></div>''')}
  </div>
  <aside style="width:360px;flex:none;display:flex;flex-direction:column;gap:var(--space-3);">
    {panel("exp_7f21 · Weekly review", chip("completed","success"),
      f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-3);">
        {"".join(f'<div><span class="th">{l}</span><div style="margin-top:3px;">{MONO(v,"var(--text-sm)")}</div></div>' for l,v in [("Format","PDF · A4 landscape"),("Pages","4"),("Size","2.1 MB"),("Rows rendered","7")])}
      </div>
      {MONO("sha256 9f2c…41ab","11px","--text-tertiary")}
      <div style="display:flex;gap:8px;">{BTN("Download","primary","doc")}{BTN("Copy link","ghost")}</div>
      {note("warning","clock","Signed link expires in 14 min",
            "The object is deleted 7 days after completion, on 10 Sep 2026. Every download is audited. "
            "2 of 12 widgets were still computing after the 120 s refresh wait, so the PDF is marked "
            "<b>partial</b> and those tiles read <b>Not available</b>.")}''')}
    {panel("exp_7f04 · Programme costs", chip("failed","danger"),
      note("danger","shield","41 of 1,204 rows excluded",
            "Rendered under your scope, not the report owner's. Sheet <b>Finance · Contracts</b> is not readable by you, "
            "and columns <b>Unit cost</b> and <b>Margin</b> are hidden by field ACL.<br>"
            "<span class='mono'>error_code limit_exceeded · correlation_id cor_5a19</span>",
            BTN("Retry","secondary","clock") + BTN("Request access","ghost","people")))}
  </aside></div>'''

write('Exports.dc.html', page(shell("Dashboards", "Exports",
  chip("your exports", "accent"), ["All", "Reports", "Dashboards", "Scheduled"], "All",
  BTN("Format", "ghost", "filter") + BTN("Last 7 days", "ghost", "calendar") + BTN("New export", "primary", "plus"),
  exp_body, crumb="Northfield Delivery / Exports"), theme="light"))

# ================= F026 — SSO and SCIM =================
ATTR = [("email", "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress", "required", "success"),
        ("given_name", "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname", "required", "success"),
        ("family_name", "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname", "required", "success"),
        ("groups", "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups", "optional", "warning")]
attr = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);height:var(--row-h);
  border-bottom:1px solid var(--border-subtle);">
  <span style="width:110px;flex:none;font-size:var(--text-sm);font-weight:600;">{a}</span>
  <span style="color:var(--text-tertiary);flex:none;">→</span>
  <span class="mono" style="flex:1;min-width:0;font-size:11px;color:var(--text-secondary);
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{c}</span>
  <span style="flex:none;">{chip(r,k)}</span></div>''' for a, c, r, k in ATTR)

SCIM = [("Users created", "34"), ("Users updated", "211"), ("Deactivated", "6"),
        ("Groups synced", "9"), ("Members added", "148")]
scim = "".join(f'''<div style="flex:1;padding:var(--space-3);border:1px solid var(--border-subtle);
  border-radius:var(--radius-md);background:var(--bg-sunken);">
  <div class="mono" style="font-size:var(--text-xl);font-weight:600;">{v}</div>
  <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;
    white-space:nowrap;">{l}</div></div>''' for l, v in SCIM)

CHECKS = [("Certificate parses and is in date", "pass", "success", "expires 14 Dec 2026 · 101 days"),
          ("SSO URL reachable", "pass", "success", "HEAD 200 in 412 ms"),
          ("SP metadata renders", "pass", "success", "2.4 KB · signed"),
          ("Second certificate for rotation", "warn", "warning", "none staged — rotation would cause downtime")]
checks = "".join(f'''<div style="display:flex;gap:8px;padding:var(--space-2) 0;
  border-bottom:1px solid var(--border-subtle);">
  <span style="color:var(--{k}-fg);flex:none;margin-top:1px;">{icon("check" if k=="success" else "warn",15)}</span>
  <div><div style="font-size:var(--text-sm);font-weight:500;">{t}</div>
    <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;">{d}</div></div></div>'''
  for t, r, k, d in CHECKS)

GMAP = [("opshub-admins", "tenant-admin", "4"), ("delivery-leads", "report-editor, workflow-editor", "18")]
gmaps = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);height:var(--row-h);
  border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);">
  <span style="width:150px;flex:none;font-weight:500;">{g}</span>
  <span style="color:var(--text-tertiary);flex:none;">→</span>
  <span style="flex:1;min-width:0;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;
    white-space:nowrap;">{r}</span>
  <span style="flex:none;">{MONO(m+" members","11px","--text-tertiary")}</span></div>''' for g, r, m in GMAP)

sso_body = f'''<div style="flex:1;display:flex;min-height:0;">
  <div style="flex:1;min-width:0;padding:var(--space-5);display:flex;flex-direction:column;
    gap:var(--space-4);overflow:hidden;">
    <div style="display:flex;gap:var(--space-3);">
      {field("Connection name",ELL("Contoso Entra ID"),"","ok","46%")}
      {field("Domains",ELL("contoso.com +2"),"","ok","30%")}
      {field("Clock skew","120 s","0–300","default","24%")}
    </div>
    <div style="display:flex;gap:var(--space-3);">
      {field("IdP metadata URL",ELL("https://login.microsoftonline.com/72f988bf/federationmetadata.xml"),
             "IdP entity ID https://sts.windows.net/72f988bf/","ok","54%")}
      {field("Certificate fingerprint (SHA-256)",ELL("3A:7F:C2:19:8B:04:DE:61:AA:5C:90:12:F7:6E:B3:08"),
             "valid until 14 Dec 2026 · no second certificate staged","ok","46%")}
    </div>
    <div style="display:flex;gap:var(--space-5);">
      {toggle(True,"Just-in-time provisioning","Creates the user on first assertion")}
      {toggle(True,"Signed assertions required","Response-only signatures rejected")}
    </div>
    <div style="display:flex;flex-direction:column;gap:var(--space-2);">
      <div style="display:flex;align-items:center;"><span class="th">Attribute mapping</span>
        <button class="btn btn-secondary" style="margin-left:auto;height:var(--control-sm);font-size:var(--text-xs);">
          {icon("plus",14)}Add claim</button></div>{attr}</div>
    <div style="display:flex;flex-direction:column;gap:var(--space-2);">
      <div style="display:flex;align-items:center;gap:8px;">
        <span class="th" style="flex:none;white-space:nowrap;">SCIM provisioning</span>
        <span style="flex:none;white-space:nowrap;">{chip("token active","success")}</span>
        <span style="margin-left:auto;font-size:var(--text-xs);color:var(--text-tertiary);
          white-space:nowrap;">last sync 09:28 · 27 removed · old token invalid 09:55</span></div>
      <div style="display:flex;gap:var(--space-3);">{scim}</div></div>
    <div style="display:flex;flex-direction:column;gap:var(--space-2);">
      <span class="th">Group to role mappings</span>{gmaps}</div>
  </div>
  <aside style="width:330px;flex:none;border-left:1px solid var(--border-subtle);padding:var(--space-4);
    display:flex;flex-direction:column;gap:var(--space-4);">
    <div style="display:flex;align-items:center;gap:8px;">
      <span style="font-size:var(--text-sm);font-weight:600;">Test connection</span>
      <span style="margin-left:auto;">{chip("3 pass · 1 warning","warning")}</span></div>
    <div>{checks}</div>
    {note("danger","shield","Last failed sign-in · 08:52",
          "<span class='mono'>saml.login.failed · audience_mismatch</span><br>"
          "Assertion Audience was <span class='mono'>urn:contoso:test</span>, expected "
          "<span class='mono'>https://app.opshub.io/sp</span>. No session was created; assertion contents are not stored.")}
    <div><span class="th">ACS URL</span>
      <div class="mono" style="margin-top:6px;padding:var(--space-2);background:var(--bg-sunken);
        border-radius:var(--radius-sm);font-size:11px;color:var(--text-secondary);word-break:break-all;">
        https://app.opshub.io/auth/saml/c_8f21/acs</div></div>
    <div style="display:flex;gap:8px;">{BTN("Run test","secondary","shield")}{BTN("Activate","primary","check")}</div>
  </aside></div>'''

write('Sso.dc.html', page(adminshell("SSO &amp; SCIM", chip("draft · not yet active", "warning"),
  ["Connection", "Mapping", "Provisioning", "Audit"], "Connection",
  BTN("SP metadata", "ghost", "doc") + BTN("Rotate token", "ghost", "cog") + BTN("Test", "secondary", "shield"),
  sso_body), theme="dark"))

# ================= F049 — Localization =================
PREV = [("Date", "03.09.2026", "3 Sep 2026"), ("Date and time", "03.09.2026, 14:00", "3 Sep 2026, 2:00 PM"),
        ("Number", "1.234.567,891", "1,234,567.891"), ("Currency", "1.234,57 €", "€1,234.57")]
prev = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:5px 0;
  border-bottom:1px solid var(--border-subtle);">
  <span style="width:110px;flex:none;font-size:var(--text-xs);color:var(--text-tertiary);">{l}</span>
  {MONO(de,"var(--text-sm)")}<span style="margin-left:auto;">{MONO(en,"var(--text-xs)","--text-tertiary")}</span></div>'''
  for l, de, en in PREV)

CAT = [("English (US)", "en-US", 2148, 2148, 100, "success"), ("Deutsch", "de-DE", 1934, 2148, 90, "success"),
       ("Français", "fr-FR", 1871, 2148, 87, "success"), ("Español", "es-ES", 1702, 2148, 79, "warning"),
       ("Português (BR)", "pt-BR", 1544, 2148, 72, "warning"), ("日本語", "ja-JP", 1109, 2148, 52, "danger"),
       ("English (UK)", "en-GB", 412, 2148, 19, "danger")]
cat = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:4px 0;
  border-bottom:1px solid var(--border-subtle);">
  <span style="width:118px;flex:none;font-size:var(--text-sm);font-weight:500;">{n}</span>
  {MONO(t,"11px","--text-tertiary")}
  <div style="flex:1;height:6px;border-radius:99px;background:var(--bg-sunken);">
    <div style="width:{p}%;height:100%;border-radius:99px;background:var(--{k}-emphasis);"></div></div>
  <span style="width:96px;flex:none;text-align:right;">{MONO(f"{d:,} / {tot:,}","11px","--text-secondary")}</span>
  <span style="width:38px;flex:none;text-align:right;">{MONO(str(p)+"%","var(--text-xs)","--"+k+"-fg")}</span></div>'''
  for n, t, d, tot, p, k in CAT)

DAYS = [("Mon", True), ("Tue", True), ("Wed", True), ("Thu", True), ("Fri", True), ("Sat", False), ("Sun", False)]
days = "".join(f'''<span style="height:var(--control-md);min-width:44px;display:inline-flex;align-items:center;
  justify-content:center;font-size:var(--text-sm);font-weight:{600 if on else 400};border-radius:var(--radius-md);
  border:1px solid var(--{'accent-border' if on else 'border-default'});
  background:var(--{'accent-bg' if on else 'bg-surface'});
  color:var(--{'accent-fg' if on else 'text-tertiary'});">{d}</span>''' for d, on in DAYS)

loc_body = f'''<div style="flex:1;display:flex;min-height:0;background:var(--bg-canvas);gap:var(--space-4);
  padding:var(--space-4);">
  <div style="width:400px;flex:none;display:flex;flex-direction:column;gap:var(--space-3);">
    {panel("Tenant defaults", chip("applies to 412 people","accent"),
      f'''{field("Locale","Deutsch (Deutschland)","Falls back to en-US for missing keys")}
      {field("Timezone","Europe/Berlin (UTC+02:00)","Browser detected Europe/Berlin")}
      <div style="display:flex;gap:var(--space-3);">{field("Hour cycle","h23","","default","50%")}
        {field("Currency","EUR","ISO 4217","default","50%")}</div>
      <div style="display:flex;flex-direction:column;gap:6px;">
        <span class="th">Week starts on</span>
        <div style="display:flex;gap:6px;">
          {"".join(f'<span style="height:var(--control-md);padding:0 var(--space-3);display:inline-flex;align-items:center;font-size:var(--text-sm);border-radius:var(--radius-md);border:1px solid var(--{"accent-border" if on else "border-default"});background:var(--{"accent-bg" if on else "bg-surface"});color:var(--{"accent-fg" if on else "text-secondary"});font-weight:{600 if on else 400};">{d}</span>' for d,on in [("Monday",True),("Sunday",False),("Saturday",False)])}
        </div></div>
      <div style="display:flex;flex-direction:column;gap:6px;">
        <span class="th">Working week</span><div style="display:flex;gap:5px;">{days}</div>
        <span style="font-size:11px;color:var(--text-tertiary);">Duration maths and date rollovers skip Sat and Sun.</span></div>''')}
    {panel("Your override", chip("overrides the tenant default","warning"),
      f'''<div style="display:flex;gap:var(--space-3);">
        {field("Locale",ELL("Português (Brasil)"),"","ok","46%")}
        {field("Timezone",ELL("America/Sao_Paulo (UTC−03:00)"),"","ok","54%")}</div>
      <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
        Resolution order: your override → tenant default → platform default en-US / UTC / Monday / h12.
        Saving re-renders the app without a reload.</div>''')}
  </div>
  <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:var(--space-3);">
    {note("warning","warn","Tenant settings changed while you were editing",
      "Sam Okafor set the timezone to <b>Europe/Berlin</b> at 09:22. Saving now returns 409 conflict.",
      BTN("Reload","secondary","clock") + BTN("Keep my draft","ghost"))}
    {panel("Format preview", MONO("de-DE vs en-US","11px","--text-tertiary"), "<div>"+prev+"</div>")}
    {panel("Translation catalogue", MONO("v41 · built 08:10","11px","--text-tertiary"),
      f'''<div style="display:flex;gap:var(--space-3);">{TH("Language",118)}{TH("Tag",44)}{TH("Coverage")}
        <span class="th" style="width:96px;flex:none;text-align:right;">Keys</span>
        <span class="th" style="width:38px;flex:none;"></span></div><div>{cat}</div>
      <div style="display:flex;align-items:center;gap:8px;color:var(--danger-fg);white-space:nowrap;">
        {icon("warn",15)}<span style="font-size:var(--text-xs);">1,039 ja-JP keys fall back to en-US ·
        en-XA hidden</span></div>''')}
  </div></div>'''

write('Localization.dc.html', page(adminshell("Localization", chip("de-DE · Europe/Berlin", "accent"),
  ["Tenant", "My settings", "Catalogue", "Formats"], "Tenant",
  BTN("Reset to platform default", "ghost") + BTN("Preview as viewer", "ghost", "user") + BTN("Save", "primary", "check"),
  loc_body), theme="light"))

# ================= F001 — /status (browser defaults, deliberately no token) =================
DEPS = [("database", "postgres 18 · primary", "degraded", "412 ms", "connection pool 48/50, 3 queries queued"),
        ("nats", "nats 2.11 · JetStream", "ok", "3 ms", "consumer workflow-runtime lag 0"),
        ("object storage", "s3 · eu-central-1", "ok", "38 ms", "bucket opshub-prod reachable")]
deprows = "".join(f'''
    <tr>
      <td style="padding:6px 16px 6px 0;">{n}</td>
      <td style="padding:6px 16px 6px 0;color:#555;">{d}</td>
      <td style="padding:6px 16px 6px 0;"><b>{s}</b></td>
      <td style="padding:6px 16px 6px 0;text-align:right;">{ms}</td>
      <td style="padding:6px 0;color:#555;">{note_}</td>
    </tr>''' for n, d, s, ms, note_ in DEPS)

status_body = f'''
  <div style="font-family:initial;font-size:16px;background:#fff;color:#000;width:1440px;height:900px;
    padding:32px;overflow:hidden;">
    <h1 style="margin:0 0 4px;">OpsHub status</h1>
    <p style="margin:0 0 24px;color:#555;">GET /healthz · polled every 10 seconds</p>
    <p style="margin:0 0 24px;font-size:20px;">
      State: <b style="border:2px solid #000;padding:2px 8px;">degraded</b>
      <span style="color:#555;font-size:16px;"> — 1 of 3 dependencies is not healthy</span></p>
    <h2 style="margin:0 0 8px;font-size:18px;">Dependencies</h2>
    <table style="border-collapse:collapse;font-size:14px;margin-bottom:24px;">
      <thead><tr style="border-bottom:1px solid #000;text-align:left;">
        <th style="padding:4px 16px 4px 0;">dependency</th><th style="padding:4px 16px 4px 0;">detail</th>
        <th style="padding:4px 16px 4px 0;">state</th><th style="padding:4px 16px 4px 0;text-align:right;">latency</th>
        <th style="padding:4px 0;">note</th></tr></thead>
      <tbody>{deprows}</tbody>
    </table>
    <h2 style="margin:0 0 8px;font-size:18px;">Build</h2>
    <ul style="margin:0 0 24px;padding-left:20px;font-size:14px;line-height:22px;">
      <li>version: 0.1.0</li>
      <li>commit: 91f8b915c4d2e77a0b3c6f81ad4499e2c7b15d30</li>
      <li>built: 2026-09-03T22:14:07Z</li>
      <li>checked: 2026-09-04T09:41:12Z</li>
    </ul>
    <p style="margin:0 0 8px;font-size:14px;">correlation id: 018f2c41-9a7e-7b23-8f60-2d9c4a11e0b7</p>
    <p style="margin:0;"><button style="font-size:14px;padding:4px 10px;">Retry</button></p>
    <p style="margin:24px 0 0;color:#777;font-size:13px;">
      This page ships before F062, uses no design token and no web font, and is styled only by the browser
      plus the minimum needed to read a table.</p>
  </div>'''

write('Status.dc.html', page(status_body, theme="light"))
print("Workflow runs, metrics, exports, SSO, localization and status written")
