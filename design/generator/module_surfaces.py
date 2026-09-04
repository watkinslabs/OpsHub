from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
import _charts as ch

# Seven advanced-module surfaces: F051 WorkApps, F052 Data Shuttle, F053 DataMesh,
# F054 Bridge, F055 Calendar, F057 Assets, F060 Conditional formatting.

CARD = ("background:var(--bg-surface);border:1px solid var(--border-subtle);border-radius:var(--radius-lg);box-shadow:var(--shadow-1);padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);")

def sect(title, inner, extra="", right=""):
    return (f'<div style="{CARD}{extra}"><div style="display:flex;align-items:center;gap:var(--space-2);"><span class="th">{title}</span><span style="margin-left:auto;display:flex;align-items:center;gap:var(--space-2);">{right}</span></div>{inner}</div>')

def note(text, kind="accent", ic="warn"):
    return (f'<div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--{kind}-bg);border:1px solid var(--{kind}-border);color:var(--{kind}-fg);font-size:var(--text-xs);line-height:17px;display:flex;gap:var(--space-2);align-items:flex-start;"><span style="flex:none;margin-top:1px;">{icon(ic,14)}</span><span>{text}</span></div>')

def dim(t, size="var(--text-xs)", tone="secondary"):
    return f'<div style="font-size:{size};color:var(--text-{tone});line-height:17px;">{t}</div>'

def gchip(t):
    return (f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-tertiary);border:1px solid var(--border-subtle);">{t}</span>')

def skel(w, h="var(--space-2)"):
    return (f'<span style="display:block;width:{w};height:{h};border-radius:var(--radius-sm);background:var(--bg-sunken);"></span>')

def notent(module, headline, bullets, plan="Business"):
    """The shared ModuleNotEntitled panel — the honest degraded surface, drawn as a labelled inset."""
    items = "".join(f'<div style="display:flex;gap:var(--space-2);align-items:flex-start;font-size:var(--text-xs);color:var(--text-secondary);line-height:17px;"><span style="flex:none;color:var(--text-tertiary);margin-top:1px;">{icon("check",13)}</span>{b}</div>' for b in bullets)
    return (f'<div style="border:1px dashed var(--border-strong);border-radius:var(--radius-lg);padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-3);background:var(--bg-sunken);"><div style="display:flex;align-items:center;gap:var(--space-2);"><span class="th">Same route, tenant without the entitlement</span></div><div style="{CARD}align-items:center;text-align:center;gap:var(--space-2);"><span style="width:36px;height:36px;border-radius:var(--radius-md);background:var(--bg-sunken);color:var(--text-tertiary);display:inline-flex;align-items:center;justify-content:center;">{icon("shield",20)}</span><div style="font-size:var(--text-base);font-weight:600;">{headline}</div>{dim("The module is not in this tenant&rsquo;s plan, so every route answers <span class=\'mono\'>403 denied</span> with <span class=\'mono\'>field_errors.module</span>. Nothing is hidden: the surface names itself and what it would do.")}<div style="display:flex;flex-direction:column;gap:6px;align-self:stretch;text-align:left;padding-top:var(--space-2);border-top:1px solid var(--border-subtle);">{items}</div><div style="display:flex;gap:var(--space-2);align-self:stretch;"><button class="btn btn-secondary" style="flex:1;justify-content:center;">Request from your admin</button><button class="btn btn-primary" style="flex:1;justify-content:center;">Start 14-day trial</button></div><span class="mono" style="font-size:11px;color:var(--text-tertiary);">module {module} · plan {plan}</span></div></div>')

def table(cols, rows, widths):
    """cols: header labels. rows: list of lists of already-rendered cell HTML."""
    head = "".join(f'<span class="th" style="{w}">{c}</span>' for c, w in zip(cols, widths))
    body = "".join('<div style="display:flex;align-items:center;height:var(--row-h);border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);">'
                   + "".join(f'<span style="{w}">{c}</span>' for c, w in zip(r, widths)) + '</div>' for r in rows)
    return (f'<div><div style="display:flex;align-items:center;height:var(--control-md);background:var(--bg-sunken);border-radius:var(--radius-sm);">{head}</div>{body}</div>')

# ============================ F051 · WorkApps ============================
NAVS = [("Intake form", "form", True), ("My vendors", "dynamic-view", True), ("Status board", "sheet", False),
        ("KPIs", "dashboard", False), ("Playbook", "text", False)]
appnav = "".join(
    f'<div class="rail-item{" on" if i == 0 else ""}" style="height:var(--control-md);font-size:var(--text-sm);{"" if vis else "opacity:.42;"}">{icon("doc" if k != "dashboard" else "chart", 15)}<span>{n}</span>{"" if vis else gchip("Procurement only")}</div>'
    for i, (n, k, vis) in enumerate(NAVS))

grid_rows = "".join(
    f'<div class="cell" style="border-bottom:1px solid var(--border-subtle);gap:var(--space-3);"><span style="width:170px;">{v}</span><span style="width:104px;">{chip(s, k)}</span><span class="mono" style="width:76px;color:var(--text-secondary);">{d}</span><span style="margin-left:auto;">{avatar(a, h)}</span></div>'
    for v, s, k, d, a, h in [("Acme Analytics", "In review", "accent", "12 Feb", "PR", 30), ("Beacon Data", "Approved", "success", "04 Feb", "SO", 70),
                             ("Cirrus Logistics", "Evidence due", "warning", "19 Feb", "PR", 30),
                             ("Delta Print Co", "In review", "accent", "21 Feb", "MW", 120)])

workapps = shell("Sheets", "Vendor onboarding",
    chip("Published · v3", "success") + gchip("draft_dirty"), ["Pages", "Roles", "Versions", "Preview"], "Preview",
    BTN("Preview as: Vendor", "secondary", "user") + BTN("Diff v2 → v3", "ghost", "layers") + BTN("Publish", "primary", "check"),
    f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:216px;flex:none;background:var(--bg-surface);border-right:1px solid var(--border-subtle);padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-2);">
      <div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2);border-radius:var(--radius-md);background:var(--accent-bg);border:1px solid var(--accent-border);color:var(--accent-fg);">
        {icon("user",15)}<span style="font-size:var(--text-xs);font-weight:600;">Role: Vendor</span></div>
      <span class="th">App pages</span>{appnav}
      {dim("Two of five pages. The manifest the server returns holds only the pages this role may see — the other three are not in the response at all.")}
    </div>
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);min-width:0;">
      {sect("Page 1 · Intake form <span style='color:var(--text-tertiary);font-weight:400;'>form embed</span>",
        f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-3);">
        {"".join(f'''<div style="display:flex;flex-direction:column;gap:5px;"><span class="th">{l}</span>
          <div style="height:var(--control-md);border:1px solid var(--border-default);border-radius:var(--radius-md);display:flex;align-items:center;padding:0 var(--space-3);font-size:var(--text-sm);color:var(--text-{"primary" if v else "tertiary"});">{v or ph}</div></div>'''
          for l, v, ph in [("Vendor legal name","Cirrus Logistics Ltd",""),("Primary contact","",'name@vendor.com'),
                           ("Category","Logistics",""),("Data processed","",'Select…')])}
        </div>""" + dim("The form loads through its own <span class='mono'>/api/v1/forms</span> endpoint under the viewer&rsquo;s session. The app grants nothing.")) }
      {sect("Page 2 · My vendors <span style='color:var(--text-tertiary);font-weight:400;'>dynamic view embed</span>",
        grid_rows + dim("4 rows of 1,284 · row filter <span class='mono'>Vendor = Cirrus Logistics</span> runs on the server"))}
      <div style="display:flex;gap:var(--space-4);">
        {sect("Page 4 · KPIs <span style='color:var(--text-tertiary);font-weight:400;'>dashboard embed</span>",
          f'<div style="display:flex;align-items:flex-end;gap:var(--space-4);">{ch.bars(240,88,[14,22,19,31,27],labels=["Oct","Nov","Dec","Jan","Feb"])}{ch.donut(88,[62,24,14],center="62%")}</div>', "flex:1;")}
        {sect("Page 3 · Status board",
          f'''<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:var(--space-2);padding:var(--space-4) 0;border:1px dashed var(--border-strong);border-radius:var(--radius-md);text-align:center;">
            <span style="color:var(--text-tertiary);">{icon("shield",22)}</span>
            <span style="font-size:var(--text-sm);font-weight:600;">You do not have access to this content</span>
            {dim("The source name is withheld. The sheet endpoint answered <span class='mono'>404</span> to this viewer.", tone="tertiary")}
          </div>''', "width:320px;")}
      </div>
    </div>
    <aside style="width:290px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
      {sect("Publish state", note("Draft has 1 page and 1 role changed since v3. <b>GET /apps/vendor-onboarding</b> still serves v3 until you publish.","warning") +
        f'<div style="display:flex;align-items:center;gap:var(--space-2);"><span class="mono" style="font-size:var(--text-xs);color:var(--text-secondary);">/apps/vendor-onboarding</span>{chip("live","success")}</div>', "box-shadow:none;padding:0;border:none;")}
      {sect("Versions", "".join(
        f'''<div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2) 0;border-bottom:1px solid var(--border-subtle);">
          <span class="mono" style="width:26px;font-size:var(--text-xs);font-weight:600;">v{v}</span>
          <div style="flex:1;min-width:0;"><div style="font-size:var(--text-sm);">{n}</div>
          <div style="font-size:11px;color:var(--text-tertiary);">{w} · {t}</div></div>
          {chip("current","accent") if cur else '<span style="color:var(--text-tertiary);font-size:var(--text-xs);">Restore</span>'}
        </div>''' for v, n, w, t, cur in [(3,"Vendor role loses KPIs","Priya Raman","4 Feb 09:12",True),
                                          (2,"Add Playbook page","Priya Raman","28 Jan 16:40",False),
                                          (1,"Initial release","Adaeze Okoro","14 Jan 11:02",False)]), "box-shadow:none;padding:0;border:none;")}
    </aside>
  </div>''', crumb="Northfield Delivery / Apps")
write('WorkApps.dc.html', page(workapps, theme="light"))

# ============================ F052 · Data Shuttle ============================
MAP = [("Cost Center", "Cost center", "text", True), ("Amount", "Amount", "currency", False),
       ("Period", "Period", "date", True), ("GL Account", "GL account", "text", False),
       ("Owner Email", "Owner", "text", False), ("Notes", "Notes", "text", False)]
maprows = [[f'<span class="mono">{s}</span>',
            f'<span style="color:var(--text-tertiary);">{icon("chev",13)}</span>',
            t, gchip(c), chip("key " + str(i + 1), "accent") if k else '<span style="color:var(--text-tertiary);">—</span>']
           for i, (s, t, c, k) in enumerate([m for m in MAP])]
RUNS = [("2026-02-24 06:00", "succeeded", "success", "120", "100", "20", "0", "scheduled"),
        ("2026-02-23 06:00", "partial", "warning", "118", "96", "14", "8", "scheduled"),
        ("2026-02-20 06:00", "failed", "danger", "134", "0", "0", "12", "scheduled"),
        ("2026-02-19 11:42", "succeeded", "success", "0", "0", "0", "0", "manual"),
        ("2026-02-19 06:00", "succeeded", "success", "127", "111", "16", "0", "scheduled")]
runrows = [[f'<span class="mono">{ts}</span>', chip(st, k), gchip(tr),
            f'<span class="mono">{rd}</span>', f'<span class="mono">{u}</span>', f'<span class="mono">{i}</span>',
            f'<span class="mono" style="color:var(--{"danger-fg" if rj != "0" else "text-tertiary"});">{rj}</span>']
           for ts, st, k, rd, u, i, rj, tr in RUNS]
REJ = [(14, "coerce_failed", "Amount", "1 240,50 EUR"), (22, "missing_required", "Cost center", "(empty)"),
       (23, "missing_required", "Cost center", "(empty)"), (57, "duplicate_key", "Cost Center", "CC-4180"),
       (61, "coerce_failed", "Period", "31/02/2026"), (88, "unknown_column", "Region", "EMEA-North"),
       (91, "coerce_failed", "Amount", "n/a"), (104, "row_denied", "Owner", "ops@northfield.io")]

shuttle = shell("Automation", "Budget import",
    chip("Import", "accent") + chip("Enabled", "success"), ["Setup", "Mapping", "Runs", "Archive"], "Runs",
    BTN("Run now", "secondary", "clock") + BTN("Replay run", "ghost", "flow") + BTN("Save flow", "primary", "check"),
    f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:394px;flex:none;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);border-right:1px solid var(--border-subtle);overflow:hidden;">
      {sect("Source and schedule", "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);font-size:var(--text-sm);">
          <span style="width:112px;color:var(--text-secondary);flex:none;">{l}</span>
          <span class="mono" style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;">{v}</span></div>'''
          for l, v in [("Location","inbox&nbsp;·&nbsp;finance/"),("Newest file","budget-2026-02-24.csv"),
                       ("SHA-256","3f9c…a17b"),("Schedule","0 6 * * 1-5"),("Timezone","America/New_York"),
                       ("Next run","2026-02-25 06:00 EST"),("Archive","keep 30 days")]),
        right=chip("cron · every weekday 06:00","accent"))}
      {sect("Column mapping",
        table(["Source column","","Sheet column","Coerce","Key"], maprows, ["width:118px;","width:20px;","flex:1;","width:74px;","width:62px;"]) +
        dim("Duplicate strategy <b>update</b> on 2 key columns · on_error <b>partial</b> · max_errors 100"))}
    </div>
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);min-width:0;">
      {sect("Run history",
        table(["Started","Status","Trigger","Read","Updated","Inserted","Rejected"], runrows,
              ["width:150px;","width:96px;","width:84px;","flex:1;text-align:right;padding-right:var(--space-4);",
               "flex:1;text-align:right;padding-right:var(--space-4);","flex:1;text-align:right;padding-right:var(--space-4);",
               "flex:1;text-align:right;padding-right:var(--space-3);"]) +
        dim("The 19 Feb 11:42 manual run finished <b>succeeded</b> with <span class='mono'>skipped_reason: duplicate_file</span> — same checksum, nothing written."),
        right=gchip("newest first"))}
      {sect("Run detail · 2026-02-20 06:00",
        note("<b>failed · validation_failed</b> — 12 rejected rows exceeded <span class='mono'>max_errors 5</span> under <span class='mono'>on_error: abort</span>. No rows were committed; the sheet is unchanged.","danger") +
        table(["Row","Reason","Source column","Value"], [[f'<span class="mono">{r}</span>', chip(rc,"danger" if rc!="row_denied" else "warning"),
                f'<span class="mono" style="color:var(--text-secondary);">{sc}</span>',
                f'<span class="mono" style="color:var(--text-tertiary);">{v}</span>'] for r, rc, sc, v in REJ],
              ["width:56px;","width:150px;","width:150px;","flex:1;"]) +
        dim("First 8 of 12 · <span class='mono'>shuttle_run_rejections</span> · archive retained until 22 Mar 2026"),
        right=BTN("Download report","ghost","doc"))}
    </div>
  </div>''', crumb="Northfield Delivery / Data Shuttle")
write('DataShuttle.dc.html', page(shuttle, theme="dark"))

# ============================ F053 · DataMesh ============================
KEYS = [("Vendor ID", "Vendor ID", "trim"), ("Region", "Region code", "case_insensitive")]
FMAP = [("Payment terms", "Terms", "→", "always", "success"), ("Contact", "Vendor contact", "⇄", "if_empty", "accent"),
        ("Risk tier", "Risk", "→", "if_empty", "accent"), ("Status", "Vendor status", "→", "never", "warning"), ("Bank ref", "—", "→", "never", "warning")]
CONF = [("both_changed", "danger", "Row 4180 · Contact", "master: j.hale@acme.io", "target: jo.hale@acme.io", "Both sides moved since cursor 8812"),
        ("ambiguous_match", "danger", "Key VEN-2231 · Region EU", "2 target rows matched", "no match written", "Key is not unique in target"),
        ("unmatched_source", "warning", "12 source rows", "policy: flag", "not created", "unmatched_policy = flag"),
        ("source_deleted", "warning", "Row 3907 · Cirrus (old)", "deleted 21 Feb", "target kept", "deletion_policy = flag")]

mesh = shell("Sheets", "Vendors master → Purchase requests",
    chip("on_change", "accent") + chip("4 open conflicts", "danger"), ["Setup", "Preview", "Runs", "Conflicts"], "Conflicts",
    BTN("Preview", "ghost", "search") + BTN("Sync now", "secondary", "flow") + BTN("Save mapping", "primary", "check"),
    f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:432px;flex:none;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);border-right:1px solid var(--border-subtle);overflow:hidden;">
      {sect("Match keys",
        table(["Ordinal","Source column","Target column","Normalize"],
              [[f'<span class="mono">{i+1}</span>', s, t, gchip(n)] for i, (s, t, n) in enumerate(KEYS)],
              ["width:62px;","flex:1;","flex:1;","width:132px;"]) +
        dim("Keys hash in ordinal order. A source row matching two target rows is never written — it becomes an <b>ambiguous_match</b> conflict."))}
      {sect("Field map",
        table(["Source","Dir","Target","Overwrite"], [[s, f'<span class="mono" style="color:var(--accent-fg);font-weight:600;">{d}</span>',
                (t if t != "—" else '<span style="color:var(--text-tertiary);">column deleted</span>'), chip(o, k)]
               for s, t, d, o, k in FMAP], ["flex:1;","width:38px;","flex:1;","width:92px;"]) +
        dim("<b>⇄</b> writes back to the master only when the target alone changed since the cursor."),
        right=gchip("5 of 100"))}
      {sect("Sync controls", "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);font-size:var(--text-sm);">
          <span style="width:150px;color:var(--text-secondary);flex:none;">{l}</span>{v}</div>'''
          for l, v in [("Sync mode", chip("on_change","accent") + '<span style="margin-left:8px;color:var(--text-tertiary);font-size:var(--text-xs);">debounced 60s</span>'),
                       ("Unmatched policy", chip("flag","warning")), ("Deletion policy", chip("flag","warning")),
                       ("Last cursor", '<span class="mono" style="font-size:var(--text-xs);">sheet_version 8812 · 09:41</span>'),
                       ("Last run", chip("succeeded","success") + '<span class="mono" style="margin-left:8px;font-size:var(--text-xs);color:var(--text-secondary);">840 matched · 96 written</span>')]))}
    </div>
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);min-width:0;">
      {sect("Conflict queue",
        "".join(f'''<div style="display:flex;gap:var(--space-3);padding:var(--space-3) 0;border-bottom:1px solid var(--border-subtle);align-items:flex-start;">
          <span style="width:150px;flex:none;">{chip(kind, tone)}</span>
          <div style="flex:1;min-width:0;"><div style="font-size:var(--text-sm);font-weight:600;">{what}</div>
            <div style="display:flex;gap:var(--space-3);margin-top:4px;">
              <span class="mono" style="font-size:11px;color:var(--text-secondary);">{a}</span>
              <span class="mono" style="font-size:11px;color:var(--text-secondary);">{b}</span></div>
            {dim(why, tone="tertiary")}</div>
          <div style="display:flex;gap:6px;flex:none;">
            <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Keep source</button>
            <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Keep target</button>
          </div></div>''' for kind, tone, what, a, b, why in CONF) +
        note("Nothing is resolved automatically. A resolve on a row whose version moved since the conflict was recorded returns <span class='mono'>409</span> and asks for a refresh.","accent","check"),
        right=gchip("filter: status = open"))}
      {notent("datamesh", "DataMesh is not part of this plan", ["Keep reference data aligned between two sheets by business key, not by copy-paste.",
         "Preview every create, update and clear before a single cell moves.", "Conflicts queue for a person instead of silently overwriting."])}
    </div>
  </div>''', crumb="Northfield Delivery / DataMesh")
write('DataMesh.dc.html', page(mesh, theme="light"))

# ============================ F054 · Bridge ============================
STEPS = [(1, "trigger", "Row created · Requests", "flow", "succeeded", "success", "0.2s"),
         (2, "connector_action", "jira.create_issue", "layers", "succeeded", "success", "1.4s"),
         (3, "wait", "Approval · Ops leads", "clock", "succeeded", "success", "4h 12m"),
         (4, "connector_action", "slack.post_message", "bell", "failed", "danger", "31.0s"),
         (5, "opshub_action", "Update field · Jira key", "grid", "queued", "warning", "—"),
         (6, "branch", "If priority = P1 → page on-call", "chev", "queued", "warning", "—")]
chain = "".join(
    f'''<div style="display:flex;gap:var(--space-3);align-items:flex-start;">
      <div style="width:28px;flex:none;display:flex;flex-direction:column;align-items:center;">
        <span style="width:26px;height:26px;border-radius:var(--radius-full);background:var(--{tone}-bg);color:var(--{tone}-fg);border:1px solid var(--{tone}-border);display:inline-flex;align-items:center;justify-content:center;">{icon(ic,14)}</span>
        {'<span style="width:2px;flex:1;min-height:var(--space-6);background:var(--border-default);"></span>' if n < 6 else ''}
      </div>
      <div style="flex:1;min-width:0;padding-bottom:var(--space-4);">
        <div style="display:flex;align-items:center;gap:var(--space-2);">
          <span style="font-size:var(--text-sm);font-weight:600;">{name}</span>
          <span class="mono" style="margin-left:auto;font-size:11px;color:var(--text-tertiary);">{dur}</span></div>
        <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">{gchip(kind)}{chip(st, tone)}</div>
      </div></div>''' for n, kind, name, ic, st, tone, dur in STEPS)

bridge = shell("Automation", "Jira intake",
    chip("v4 published", "success") + chip("Run failed at step 4", "danger"), ["Builder", "Runs", "Versions", "Settings"], "Runs",
    BTN("Cancel run", "ghost") + BTN("Retry step", "secondary", "flow") + BTN("Run now", "primary", "check"),
    f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:340px;flex:none;padding:var(--space-5);border-right:1px solid var(--border-subtle);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      {sect("Step chain", chain, right=gchip("6 of 50"))}
    </div>
    <div style="width:400px;flex:none;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);border-right:1px solid var(--border-subtle);overflow:hidden;">
      {sect("Step 4 · slack.post_message", "".join(f'''<div style="display:flex;flex-direction:column;gap:5px;"><span class="th">{l}</span>
          <div style="min-height:var(--control-md);border:1px solid var(--border-default);border-radius:var(--radius-md);display:flex;align-items:center;padding:var(--space-2) var(--space-3);font-size:var(--text-sm);background:var(--bg-surface);"><span class="mono" style="font-size:var(--text-xs);">{v}</span></div></div>'''
          for l, v in [("Connection","slack · Northfield workspace"), ("channel","#vendor-intake"),
                       ("text","New vendor {{row.Vendor}} — {{steps.2.output.key}}"), ("authorization","***")]) +
        note("Header and token fields are redacted to <span class='mono'>***</span> before the snapshot is written, so the run console never shows a secret.","accent","shield") +
        dim("Timeout 60s · retries 1s, 4s, 16s · re-checks the owner&rsquo;s access to this connection on every attempt"),
        right=chip("connector_action","accent"))}
    </div>
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);min-width:0;">
      {sect("Run console · run 01JQ8K…3F2",
        note("<b>Step 4 failed · rate_limited</b> after 3 attempts (1s, 4s, 16s). Slack answered <span class='mono'>429</span> with <span class='mono'>retry-after: 30</span>. The run is <b>failed</b>; steps 5 and 6 never started.","danger") +
        "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);height:var(--row-h);border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);">
          <span class="mono" style="width:64px;color:var(--text-tertiary);font-size:var(--text-xs);">{t}</span>
          <span style="flex:1;min-width:0;">{m}</span>{chip(s, k)}</div>'''
          for t, m, s, k in [("09:14:02","Run started · pinned to flow_version 4","started","accent"),
                             ("09:14:03","jira.create_issue → NF-4471","ok","success"),
                             ("09:14:04","Waiting for approval · Ops leads","waiting","warning"), ("13:26:11","Approved by Adaeze Okoro","ok","success"),
                             ("13:26:12","slack.post_message attempt 1","429","danger"), ("13:26:33","slack.post_message attempt 3","429","danger")]) +
        sect("What Retry step would do",
          "".join(f'<div style="display:flex;gap:var(--space-2);font-size:var(--text-xs);color:var(--text-secondary);line-height:18px;"><span style="color:var(--success-fg);flex:none;">{icon("check",13)}</span>{b}</div>'
                  for b in ["Re-executes step 4 only, from its captured <span class='mono'>input_snapshot</span> — no Jira issue is created twice.",
                            "Steps 1–3 keep their recorded outputs; step 2&rsquo;s issue key stays available to later steps.",
                            "On success the run resumes at step 5 and emits <span class='mono'>bridge-run.step-completed.v1</span>.",
                            "The retry is a new attempt row, not an edit — attempt history stays complete."]),
          "background:var(--bg-sunken);box-shadow:none;"),
        right=gchip("polling · 5s"))}
    </div>
  </div>''', crumb="Northfield Delivery / Bridge")
write('Bridge.dc.html', page(bridge, theme="dark"))

# ============================ F055 · Calendar ============================
SRC = [("Launches", ch.SER[0], True), ("Maintenance", ch.SER[1], True), ("Leave", ch.SER[2], True), ("Releases", ch.SER[3], False)]
EV = {2: [("Aurora 2.1 launch", 0, "")], 3: [("DB failover drill", 1, "22:00")], 5: [("Ivan Petrov — leave", 2, "")], 6: [("Aurora 2.1 launch", 0, "")],
      9: [("Region EU cutover", 1, "01:00"), ("Beta invite wave", 0, "")], 11: [("Patch window", 1, "23:30")], 12: [("Priya Raman — leave", 2, "")],
      13: [("Priya Raman — leave", 2, "")], 16: [("Vendor portal GA", 0, "")],
      17: [("Storage expansion", 1, "02:00")], 19: [("Marcus Webb — leave", 2, "")], 20: [("Q1 pricing update", 0, ""), ("Patch window", 1, "23:30")],
      23: [("Cert rotation", 1, "04:00")], 24: [("Northfield roadshow", 0, "")],
      25: [("Northfield roadshow", 0, "")], 26: [("Northfield roadshow", 0, "")], 27: [("Leap-day freeze begins", 0, "")]}
def TIME(t):
    return f'<span class="mono" style="color:var(--text-tertiary);">{t}</span>' if t else ''
CELLS = [("Jan", d, True) for d in range(26, 32)] + [("Feb", d, False) for d in range(1, 29)] + [("Mar", 1, True)]
def daycell(m, d, off):
    evs = "" if off else "".join(
        f'<div style="display:flex;align-items:center;gap:5px;padding:2px var(--space-2);border-radius:var(--radius-sm);background:color-mix(in oklch, {SRC[s][1]} 16%, transparent);font-size:11px;line-height:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><span style="width:6px;height:6px;border-radius:99px;background:{SRC[s][1]};flex:none;"></span>{TIME(t)}{n}</div>'
        for n, s, t in EV.get(d, []))
    return (f'<div style="flex:1;min-width:0;border-right:1px solid var(--border-subtle);border-bottom:1px solid var(--border-subtle);padding:var(--space-2);display:flex;flex-direction:column;gap:3px;{"background:var(--bg-sunken);" if off else ""}"><span class="mono" style="font-size:11px;color:var(--text-{"tertiary" if off else "secondary"});">{d if not off else m + " " + str(d)}</span>{evs}</div>')
weeks = "".join('<div style="flex:1;display:flex;min-height:0;">'
                + "".join(daycell(*c) for c in CELLS[i * 7:i * 7 + 7]) + '</div>' for i in range(5))
legend = "".join(
    f'''<div style="display:flex;align-items:center;gap:var(--space-2);padding:6px var(--space-2);border-radius:var(--radius-sm);{"" if on else "opacity:.45;"}">
      <span style="width:10px;height:10px;border-radius:3px;background:{c};flex:none;"></span>
      <span style="font-size:var(--text-sm);flex:1;">{n}</span>
      {icon("check",14) if on else icon("chev",14)}</div>''' for n, c, on in SRC)

calendar = shell("Calendar", "Ops overview",
    chip("4 sources", "accent") + chip("ICS published", "success"), ["Month", "Week", "Agenda", "Sources"], "Month",
    BTN("Timezone: America/Los_Angeles", "secondary", "clock") + BTN("Add source", "ghost", "plus") + BTN("Publish", "primary", "calendar"),
    f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-surface);">
      <div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--border-subtle);">
        <span style="font-size:var(--text-lg);font-weight:700;">February 2026</span>
        <span style="color:var(--text-tertiary);">{icon("chev",16)}</span>
        {gchip("week starts Monday")}
        <span style="margin-left:auto;font-size:var(--text-xs);color:var(--text-secondary);">
          Times shown in <b>PST (UTC−8)</b> · stored in each source&rsquo;s own zone</span></div>
      <div style="display:flex;height:var(--control-md);flex:none;background:var(--bg-sunken);border-bottom:1px solid var(--border-default);">
        {"".join(f'<span class="th" style="flex:1;display:flex;align-items:center;padding:0 var(--space-2);">{d}</span>' for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])}
      </div>
      <div style="flex:1;display:flex;flex-direction:column;min-height:0;">{weeks}</div>
    </div>
    <aside style="width:322px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      {sect("Sources", legend +
        note("<b>2 sources hidden by permissions.</b> They are not named or counted in any event. What you cannot read on the sheet you cannot read here.","warning","shield") +
        f'<div style="display:flex;align-items:center;gap:var(--space-2);opacity:.55;padding:6px var(--space-2);"><span style="width:10px;height:10px;border-radius:3px;background:var(--border-strong);flex:none;"></span><span style="font-size:var(--text-sm);flex:1;">Releases</span>{gchip("Source unavailable")}</div>',
        "box-shadow:none;padding:0;border:none;")}
      {sect("Publish · ICS feed",
        f'<div style="display:flex;align-items:center;gap:var(--space-2);height:var(--control-md);padding:0 var(--space-3);background:var(--bg-sunken);border:1px solid var(--border-subtle);border-radius:var(--radius-md);"><span class="mono" style="font-size:11px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;color:var(--text-secondary);">/public/calendars/9f3c…d21a.ics</span>{icon("doc",14)}</div>' +
        "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);font-size:var(--text-sm);">
          <span style="width:118px;color:var(--text-secondary);flex:none;">{l}</span>{v}</div>'''
          for l, v in [("Expires", chip("14 Mar 2026 · 18d","accent")), ("Details", chip("Titles included","success")),
                       ("Requests", '<span class="mono" style="font-size:var(--text-xs);">412 / 24h · 3 clients</span>')]) +
        note("The feed re-applies the publisher&rsquo;s permissions on every request. Un-share a source and it leaves the feed on the next fetch — no re-publish needed.","accent","shield") +
        f'<div style="display:flex;gap:var(--space-2);"><button class="btn btn-secondary" style="flex:1;justify-content:center;">Copy URL</button><button class="btn btn-secondary" style="flex:1;justify-content:center;color:var(--danger-fg);border-color:var(--danger-border);">Revoke</button></div>',
        "box-shadow:none;padding:0;border:none;")}
    </aside>
  </div>''', crumb="Northfield Delivery / Calendars")
write('Calendar.dc.html', page(calendar, theme="light"))

# ============================ F057 · Assets (DAM) ============================
TILES = [("aurora-hero-4k.jpg", "12.4 MB", "ready", "Approved", "success", 250), ("aurora-hero-alt.jpg", "11.8 MB", "ready", "Approved", "success", 40),
         ("brandmark-2026.svg", "84 KB", "ready", "Draft", "warning", 140), ("roadshow-reel.mp4", "412 MB", "pending", "In review", "accent", 190),
         ("pricing-onepager.pdf", "2.1 MB", "failed", "Approved", "success", 90), ("vendor-portal-ui.png", "3.7 MB", "ready", "Approved", "success", 300),
         ("team-offsite-01.jpg", "8.9 MB", "ready", "Rights expired", "danger", 20), ("packaging-mock.psd", "196 MB", "ready", "Draft", "warning", 160)]
tiles = "".join(
    f'''<div style="border:1px solid var(--border-{"strong" if i == 6 else "subtle"});border-radius:var(--radius-md);
      overflow:hidden;background:var(--bg-surface);{"box-shadow:0 0 0 2px var(--brand);" if i == 6 else ""}">
      <div style="height:96px;background:oklch(0.62 0.09 {hue});display:flex;align-items:center;justify-content:center;position:relative;">
        <span style="position:absolute;top:6px;left:6px;">{chip("renditions pending","warning") if rs == "pending" else (chip("rendition failed","danger") if rs == "failed" else "")}</span>
        <span style="position:absolute;top:6px;right:6px;">{chip(ap, k)}</span></div>
      <div style="padding:var(--space-2) var(--space-3);display:flex;flex-direction:column;gap:3px;">
        <span style="font-size:var(--text-xs);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{n}</span>
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="mono" style="font-size:11px;color:var(--text-tertiary);">{sz}</span>
          <span style="margin-left:auto;">{gchip("thumb·preview·web") if rs == "ready" else gchip("poster 0 of 2" if rs == "pending" else "unsupported_format")}</span>
        </div></div></div>''' for i, (n, sz, rs, ap, k, hue) in enumerate(TILES))
TREE = [("All assets", 0, "1,284", False), ("Brand", 1, "212", False), ("Logos", 2, "38", False),
        ("Photography", 1, "704", False), ("Campaign 2026", 2, "148", True), ("Offsite", 2, "96", False),
        ("Product", 1, "301", False), ("Archive", 1, "67", False)]
tree = "".join(
    f'''<div class="rail-item{" on" if on else ""}" style="height:var(--control-md);font-size:var(--text-sm);padding-left:calc(var(--space-3) + {d} * var(--space-4));">
      {icon("layers" if d < 2 else "doc",14)}<span style="flex:1;">{n}</span>
      <span class="mono" style="font-size:11px;color:var(--text-tertiary);">{c}</span></div>''' for n, d, c, on in TREE)

assets = shell("Documents", "Asset library",
    chip("1,284 assets", "accent") + chip("1 rights expired", "danger"), ["Library", "Collections", "Rights", "Schema"], "Library",
    BTN("Filter: rights_state", "ghost", "filter") + BTN("Register asset", "secondary", "plus") + BTN("Request approval", "primary", "check"),
    f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:236px;flex:none;background:var(--bg-surface);border-right:1px solid var(--border-subtle);padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-2);overflow:hidden;">
      <span class="th">Collections</span>{tree}
      {notent("dam", "Assets is not part of this plan", ["Renditions, rights windows and approvals on one record.",
         "Filter by territory, channel and usability, not by folder names."])}
    </div>
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);min-width:0;">
      {note("<b>team-offsite-01.jpg — rights expired 31 Jan 2026.</b> The asset stays visible and downloadable to editors, and is <span class='mono'>usable: false</span> everywhere it would be published. Renew the licence or archive it.","danger")}
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:var(--space-3);">{tiles}</div>
      {dim("8 of 1,284 · sorted by updated_at · <span class='mono'>roadshow-reel.mp4</span> is generating poster and 720p preview · <span class='mono'>pricing-onepager.pdf</span> failed 3 attempts with <span class='mono'>unsupported_format</span> — Retry is offered to editors.")}
    </div>
    <aside style="width:340px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      <div style="display:flex;align-items:center;gap:var(--space-2);">
        <span style="font-size:var(--text-base);font-weight:600;">team-offsite-01.jpg</span>
        {chip("Not usable","danger")}</div>
      {sect("Metadata", "".join(f'''<div style="display:flex;align-items:flex-start;gap:var(--space-3);font-size:var(--text-sm);">
          <span style="width:104px;color:var(--text-secondary);flex:none;">{l}</span>
          <span style="flex:1;min-width:0;">{v}</span></div>'''
          for l, v in [("Title","Offsite — keynote wide"),("Photographer","H. Lindqvist"), ("Shoot date",'<span class="mono">2025-01-22</span>'),
                       ("Tags", gchip("offsite") + " " + gchip("people") + " " + gchip("2025")),
                       ("Renditions",'<span class="mono" style="font-size:var(--text-xs);">thumbnail 256 · preview 1280 · web 1920</span>')]),
        "box-shadow:none;padding:0;border:none;")}
      {sect("Rights", "".join(f'''<div style="display:flex;align-items:flex-start;gap:var(--space-3);font-size:var(--text-sm);">
          <span style="width:104px;color:var(--text-secondary);flex:none;">{l}</span>
          <span style="flex:1;min-width:0;">{v}</span></div>'''
          for l, v in [("Licence", chip("licensed","accent")), ("Licensor","Nordlys Studio AB"),
                       ("Valid",'<span class="mono">2025-02-01 → 2026-01-31</span>'),
                       ("Territories", gchip("SE") + " " + gchip("NO") + " " + gchip("DK") + " " + gchip("FI")),
                       ("Channels", gchip("web") + " " + gchip("social") + " " + '<span style="opacity:.5;">' + gchip("print") + "</span>")]) +
        note("<b>Expired 34 days ago.</b> Every read returns <span class='mono'>rights_state: expired</span>; approval stays <b>approved</b> but <span class='mono'>usable</span> is false, so publishing surfaces refuse it.","danger"),
        "box-shadow:none;padding:0;border:none;", right=BTN("Renew","ghost"))}
    </aside>
  </div>''', crumb="Northfield Delivery / Assets")
write('Assets.dc.html', page(assets, theme="dark"))

# ============================ F060 · Conditional formatting ============================
RULES = [("Overdue and not complete", "format.red", "alert-triangle", "Late", "Row", True, True),
         ("Owner is me", "format.blue", "circle-dot", "Mine", "Row", True, False),
         ("Blocked by vendor", "format.amber", "flag", "Blocked", "Cells · 2", True, False),
         ("At risk margin", "format.violet", "octagon-x", "Risk", "Cells · 1", False, False),
         ("Closed this quarter", "format.green", "check-circle", "Done", "Row", True, False)]
FILL = {"format.red": "--danger", "format.blue": "--accent", "format.amber": "--warning", "format.violet": "--accent", "format.green": "--success"}
rules = "".join(
    f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) var(--space-2);border-radius:var(--radius-md);border:1px solid var(--border-{"default" if i == 0 else "subtle"});
      {"background:var(--bg-selected);" if i == 0 else ""}margin-bottom:6px;{"" if en else "opacity:.5;"}">
      <span class="mono" style="width:18px;font-size:11px;color:var(--text-tertiary);">{i+1}</span>
      <span style="color:var(--text-tertiary);">{icon("sort",14)}</span>
      <span style="width:22px;height:22px;border-radius:var(--radius-sm);background:var({FILL[f]}-bg);border:1px solid var({FILL[f]}-border);color:var({FILL[f]}-fg);display:inline-flex;align-items:center;justify-content:center;flex:none;">{icon("warn",12)}</span>
      <div style="flex:1;min-width:0;"><div style="font-size:var(--text-sm);font-weight:600;">{n}</div>
        <div style="font-size:11px;color:var(--text-tertiary);">{tgt} · badge &ldquo;{b}&rdquo; · {ic}</div></div>
      {chip("stop","warning") if stop else ""}{"" if en else gchip("disabled")}</div>'''
    for i, (n, f, ic, b, tgt, en, stop) in enumerate(RULES))

PREVIEW = [("Migrate billing exports", "2026-02-11", "In progress", "MW", 120, "--danger", "Late", True),
           ("Vendor security review", "2026-03-04", "In progress", "CW", 255, "--accent", "Mine", False),
           ("Cutover runbook draft", "2026-02-27", "Blocked", "AD", 210, "--warning", "Blocked", False),
           ("Accessibility audit", "2026-01-30", "Complete", "AD", 210, "--success", "Done", False),
           ("Load test 100k rows", "2026-02-09", "Not started", "MW", 120, "--danger", "Late", True),
           ("Pilot tenant provisioning", "2026-02-20", "Complete", "SO", 70, "--success", "Done", False),
           ("Rollback drill", "2026-03-11", "Not started", "CW", 255, "--accent", "Mine", False)]
prows = "".join(
    f'''<div style="display:flex;align-items:center;height:var(--row-h);border-bottom:1px solid var(--border-subtle);background:var({tone}-bg);font-size:var(--text-sm);">
      <span style="width:26px;display:flex;justify-content:center;color:var({tone}-fg);flex:none;">{icon("warn" if late else "check",14)}</span>
      <span style="flex:1;min-width:0;color:var({tone}-fg);{"font-weight:600;" if late else ""}">{n}</span>
      <span class="mono" style="width:104px;color:var({tone}-fg);">{d}</span>
      <span style="width:120px;">{s}</span>
      <span style="width:78px;">{chip(bd, tone.replace("--",""))}</span>
      <span style="width:46px;">{avatar(a,h)}</span></div>''' for n, d, s, a, h, tone, bd, late in PREVIEW)

fmt = shell("Sheets", "Cutover plan",
    chip("Conditional formatting", "accent") + gchip("5 rules · 100 max"), ["Grid", "Board", "Timeline", "Calendar", "Cards"], "Grid",
    BTN("Signals: Colour and icon", "secondary", "sparkle") + BTN("Legend", "ghost", "layers") + BTN("New rule", "primary", "plus"),
    f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:330px;flex:none;background:var(--bg-surface);border-right:1px solid var(--border-subtle);padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      {sect("Rules · precedence order", rules +
        dim("Rules apply top to bottom; a later rule overwrites only the properties it sets. Rule 1 carries <b>stop</b>, so rows it matches skip rules 2–5 entirely."),
        "box-shadow:none;padding:0;border:none;", right=gchip("sheet scope"))}
      {sect("View-scoped", '<div style="display:flex;flex-direction:column;gap:6px;">'
        + skel("64%") + skel("88%") + skel("46%") + "</div>" +
        dim("Loading rules for view <b>Cutover — exec</b>. View-scoped rules layer after every sheet-scoped rule.", tone="tertiary"),
        "box-shadow:none;padding:0;border:none;")}
    </div>
    <div style="width:376px;flex:none;padding:var(--space-5);border-right:1px solid var(--border-subtle);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      {sect("Rule 1 · Overdue and not complete", "".join(f'''<div style="display:flex;align-items:center;gap:6px;">
          <span style="width:34px;font-size:11px;color:var(--text-tertiary);text-align:right;flex:none;">{j}</span>
          <span style="flex:1;height:var(--control-sm);border:1px solid var(--border-default);border-radius:var(--radius-sm);display:flex;align-items:center;padding:0 var(--space-2);font-size:var(--text-xs);">{c}</span>
          <span style="width:86px;height:var(--control-sm);border:1px solid var(--border-default);border-radius:var(--radius-sm);display:flex;align-items:center;padding:0 var(--space-2);font-size:var(--text-xs);flex:none;">{o}</span>
          <span style="width:96px;height:var(--control-sm);border:1px solid var(--border-default);border-radius:var(--radius-sm);display:flex;align-items:center;padding:0 var(--space-2);font-size:var(--text-xs);flex:none;">{v}</span></div>'''
          for j, c, o, v in [("","Due date","before","today"),("and","Status","neq","Complete"), ("and","Owner","is_not_empty","—")]) +
        f'<div style="display:flex;gap:var(--space-2);"><button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Add condition</button><button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Add group</button><span style="margin-left:auto;font-size:11px;color:var(--text-tertiary);align-self:center;">3 of 20 leaves · depth 1 of 4</span></div>',
        right=chip("Target: Whole row","accent"))}
      {sect("Format",
        f'<div style="display:flex;gap:var(--space-2);flex-wrap:wrap;">'
        + "".join(f'<span style="width:30px;height:30px;border-radius:var(--radius-md);background:var({t}-bg);border:{"2px solid var(--brand)" if t == "--danger" else "1px solid var(" + t + "-border)"};display:inline-flex;align-items:center;justify-content:center;color:var({t}-fg);">{icon("check",13) if t == "--danger" else ""}</span>'
                  for t in ["--danger","--warning","--success","--accent"])
        + f'<span style="width:30px;height:30px;border-radius:var(--radius-md);background:var(--bg-sunken);border:1px solid var(--border-default);"></span></div>' +
        "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);font-size:var(--text-sm);">
          <span style="width:96px;color:var(--text-secondary);flex:none;">{l}</span>{v}</div>'''
          for l, v in [("Fill", '<span class="mono" style="font-size:var(--text-xs);">format.red</span>'), ("Icon", chip("alert-triangle","danger")),
                       ("Badge", '<span class="mono" style="font-size:var(--text-xs);">Late</span>'), ("Text style", gchip("bold")),
                       ("Stop", chip("Stop evaluating later rules","warning"))]) +
        note("Colour is never the only signal. A format that sets <b>fill</b> or <b>text colour</b> without an icon, badge or text style is rejected by the server with <span class='mono'>needs_non_color_signal</span> — and <b>Icon only</b> mode drops every fill while keeping the meaning.","accent","check"))}
    </div>
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);min-width:0;">
      {sect("Live preview · 7 of 10 rows",
        f'<div style="display:flex;align-items:center;height:var(--control-md);background:var(--bg-sunken);border-radius:var(--radius-sm);">'
        + "".join(f'<span class="th" style="{w}">{c}</span>' for c, w in
                  [("", "width:26px;"), ("Task", "flex:1;"), ("Due date", "width:104px;"),
                   ("Status", "width:120px;"), ("Signal", "width:78px;"), ("Owner", "width:46px;")])
        + "</div>" + prows +
        dim("Every formatted row carries <span class='mono'>aria-describedby</span> naming the rules that painted it; the cell menu&rsquo;s <b>Why is this row highlighted?</b> lists them in application order."),
        right=gchip("evaluate · not persisted"))}
      {sect("Page state",
        note("<b>Formatting paused for this page.</b> Evaluation crossed the 150 ms budget on 500 rows, so the rows are served unformatted with <span class='mono'>formatting.degraded = true</span> and <span class='mono'>reason: budget</span>. Reads never fail — they arrive plain.","warning") +
        note("Rule 4 references <b>Margin %</b>, a column this viewer cannot read. The leaf is treated as not matched and the rule ID is listed in <span class='mono'>hidden_inputs</span> — formatting never reveals a value the permission model hides.","accent","shield") +
        f'<div style="display:flex;gap:var(--space-2);"><button class="btn btn-secondary">Retry this page</button><span style="align-self:center;font-size:11px;color:var(--text-tertiary);" class="mono">correlation_id 01JQ8K7M…</span></div>')}
    </div>
  </div>''', crumb="Northfield Delivery / Migration")
write('Formatting.dc.html', page(fmt, theme="light"))

print("WorkApps + DataShuttle + DataMesh + Bridge + Calendar + Assets + Formatting written")
