from _common import icon, chip, page, write
from board_timeline import shell, BTN

# F071 Migration import — the review step. Nothing exists in the workspace yet: this screen is the
# dry run, and `Create everything` is the only thing that writes.

TABS = [("Milestones", "182 rows", 9, 0, True),
        ("Tasks", "1,240 rows", 12, 1, False),
        ("Owners", "48 rows", 5, 0, False),
        ("Rates", "36 rows", 4, 0, False),
        ("Risks", "97 rows", 7, 2, False),
        ("Budget", "310 rows", 11, 0, False),
        ("Vendors", "64 rows", 6, 0, False),
        ("Releases", "120 rows", 8, 1, False),
        ("Timesheets", "2,213 rows", 9, 0, False)]

COLUMNS = [("Milestone", "Vendor security review · Cutover runbook · Pilot tenant", "text", "0.998", "high", None),
           ("Owner", "ana.duarte@northfield.co · marcus.webb@northfield.co", "person", "0.960", "high", None),
           ("Stage", "Discovery · Build · Harden · Launch", "select", "0.994", "high", "4 options staged"),
           ("Start", "2026-03-02 · 2026-03-09 · 2026-03-16", "date", "0.981", "high", None),
           ("Due", "2026-03-14 09:00 · 2026-03-21 17:00", "datetime", "0.977", "high", None),
           ("Effort", "1:30 · 4:00 · 0:45", "duration", "0.912", "med", "also parses as number"),
           ("Budget", "€ 42,500 · € 18,000 · € 6,250", "currency", "0.968", "high", "EUR"),
           ("Signed off", "TRUE · FALSE · TRUE", "boolean", "1.000", "high", None),
           ("Rate card", "Rates!B2 · Rates!B7 · Rates!B4", "link", "0.874", "med", "links to Rates"),
           ("Notes", "see attached · n/a · revisit after gate 2", "text", "0.640", "low", "fell back to text")]

ISSUES = [("blocking", "Milestones has more rows than a sheet can take",
           "Rows 100,001–120,000 on Timesheets will not be brought over. Split the tab or waive this.",
           "row_cap_exceeded · Timesheets"),
          ("warning", "A formula function OpsHub does not have",
           "GETPIVOTDATA in Budget!F14 was replaced with its last calculated value.",
           "unsupported_formula_function · Budget!F14"),
          ("warning", "Conditional formatting was not brought over",
           "The red-amber-green rule on Milestones has no equivalent yet. Recreate it after the move.",
           "conditional_format_dropped · Milestones"),
          ("warning", "A reference to another workbook",
           "Tasks!H2 points at 2025 actuals, which is not part of this upload. The value came over as text.",
           "cross_workbook_reference · Tasks!H2"),
          ("warning", "One attachment is too large",
           "vendor-pack.pdf is 31.4 MB; the limit is 25 MB. Every other attachment came over.",
           "attachment_over_size_cap · Vendors"),
          ("info", "Only five sorts per view",
           "Milestones had six saved sorts. The first five became the view's sort order.",
           "view_sorts_truncated · Milestones"),
          ("info", "A pivot table has no equivalent",
           "The Budget summary pivot was not brought over. Build it as a report once the sheets exist.",
           "unsupported_view_kind · Budget")]

CONF = {"high": ("High", "success", "check"), "med": ("Medium", "warning", "warn"), "low": ("Low", "danger", "warn")}
SEV = {"blocking": ("Blocking", "danger", "warn"), "warning": ("Warning", "warning", "warn"),
       "info": ("Information", "accent", "doc")}


def tab_row(name, rows, cols, issues, on):
    badge = ""
    if issues:
        badge = ('<span class="chip" style="background:var(--warning-bg);color:var(--warning-fg);'
                 'border:1px solid var(--warning-border);height:18px;padding:0 6px;">%d</span>' % issues)
    return f'''<div style="display:flex;align-items:center;gap:var(--space-2);height:44px;padding:0 var(--space-3);
      border-radius:var(--radius-md);background:{"var(--bg-selected)" if on else "transparent"};">
      <span style="color:var(--{"accent-fg" if on else "text-tertiary"});">{icon("panel",16)}</span>
      <div style="flex:1;min-width:0;">
        <div style="font-size:var(--text-sm);font-weight:{600 if on else 500};
          color:var(--{"accent-fg" if on else "text-primary"});">{name}</div>
        <div class="mono" style="font-size:11px;color:var(--text-tertiary);margin-top:1px;">{rows} · {cols} columns</div>
      </div>{badge}</div>'''


def conf_chip(kind, value):
    label, tone, ic = CONF[kind]
    return (f'<span class="chip" style="background:var(--{tone}-bg);color:var(--{tone}-fg);'
            f'border:1px solid var(--{tone}-border);gap:5px;">{icon(ic,12,"currentColor","2")}{label}'
            f'<span class="mono" style="font-weight:500;opacity:.8;">{value}</span></span>')


def type_select(value, flagged):
    border = "var(--warning-emphasis)" if flagged else "var(--border-default)"
    return f'''<span style="display:inline-flex;align-items:center;gap:var(--space-2);height:var(--control-sm);
      padding:0 var(--space-2);border:1px solid {border};border-radius:var(--radius-md);
      background:var(--bg-surface);font-size:var(--text-sm);font-weight:500;min-width:118px;">
      {value}<span style="margin-left:auto;color:var(--text-tertiary);">{icon("down",14)}</span></span>'''


def column_row(name, samples, kind, conf, level, note):
    flagged = level != "high"
    note_html = ""
    if note:
        note_html = (f'<div style="font-size:var(--text-xs);color:var(--{"warning-fg" if flagged else "text-tertiary"});'
                     f'margin-top:2px;">{note}</div>')
    return f'''<div style="display:flex;align-items:center;gap:var(--space-3);min-height:52px;padding:var(--space-2) var(--space-4);
      border-bottom:1px solid var(--border-subtle);">
      <div style="width:150px;flex:none;">
        <div style="font-size:var(--text-sm);font-weight:600;">{name}</div>{note_html}</div>
      <div style="flex:1;min-width:0;font-size:var(--text-sm);color:var(--text-secondary);
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{samples}</div>
      <div style="width:132px;flex:none;display:flex;justify-content:flex-end;">{conf_chip(level, conf)}</div>
      <div style="width:130px;flex:none;display:flex;justify-content:flex-end;">{type_select(kind, flagged)}</div>
    </div>'''


def issue_card(sev, title, body, ref):
    label, tone, ic = SEV[sev]
    action = "Waive" if sev != "info" else "Got it"
    return f'''<div class="card" style="padding:var(--space-3);display:flex;flex-direction:column;gap:6px;">
      <div style="display:flex;align-items:center;gap:var(--space-2);">
        <span style="color:var(--{tone}-emphasis);">{icon(ic,15,"currentColor","2")}</span>
        <span style="font-size:var(--text-sm);font-weight:600;line-height:18px;">{title}</span></div>
      <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:17px;">{body}</div>
      <div style="display:flex;align-items:center;gap:var(--space-2);">
        <span class="mono" style="font-size:10px;color:var(--text-tertiary);">{ref}</span>
        <span style="margin-left:auto;font-size:var(--text-xs);font-weight:600;color:var(--accent-fg);">{action}</span></div>
    </div>'''


def issue_group(sev):
    label, tone, _ = SEV[sev]
    rows = [i for i in ISSUES if i[0] == sev]
    cards = "".join(issue_card(*r) for r in rows)
    return f'''<div style="display:flex;flex-direction:column;gap:var(--space-2);">
      <div style="display:flex;align-items:center;gap:var(--space-2);">
        <span class="th">{label}</span>
        <span class="mono" style="font-size:11px;color:var(--text-tertiary);">{len(rows)}</span></div>
      {cards}</div>'''


tab_list = f'''<div style="width:250px;flex:none;background:var(--bg-canvas);
  border-right:1px solid var(--border-subtle);padding:var(--space-4) var(--space-3);display:flex;
  flex-direction:column;gap:2px;overflow:hidden;">
  <div style="display:flex;align-items:center;gap:8px;padding:0 var(--space-3) var(--space-2);">
    <span class="th">Tabs in this workbook</span>
    <span class="mono" style="font-size:11px;color:var(--text-tertiary);margin-left:auto;">12</span></div>
  {"".join(tab_row(*t) for t in TABS)}
  <div style="margin-top:auto;padding:var(--space-3);border-top:1px solid var(--border-subtle);
    font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
    Nothing has been created yet. This is what the move would produce.</div>
</div>'''

review = f'''<div style="flex:1;display:flex;flex-direction:column;min-width:0;background:var(--bg-surface);overflow:hidden;">
  <div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-4) var(--space-4) var(--space-3);">
    <div>
      <div style="font-size:var(--text-lg);font-weight:700;letter-spacing:-.01em;">Milestones</div>
      <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:2px;">
        Becomes a sheet in Northfield Delivery / Delivery · header row 1 · primary column Milestone</div>
    </div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:var(--space-2);">
      {chip("1 grid view", "accent")}{chip("1 link column", "accent")}{chip("2 to decide", "warning")}</div>
  </div>
  <div style="display:flex;align-items:center;gap:var(--space-3);height:32px;padding:0 var(--space-4);
    background:var(--bg-sunken);border-top:1px solid var(--border-default);border-bottom:1px solid var(--border-default);">
    <span class="th" style="width:150px;flex:none;">Column</span>
    <span class="th" style="flex:1;">Values in the workbook</span>
    <span class="th" style="width:132px;flex:none;text-align:right;">Confidence</span>
    <span class="th" style="width:130px;flex:none;text-align:right;">Type in OpsHub</span>
  </div>
  <div style="flex:1;overflow:hidden;">{"".join(column_row(*c) for c in COLUMNS)}</div>
  <div style="height:60px;flex:none;display:flex;align-items:center;gap:var(--space-3);
    padding:0 var(--space-4);border-top:1px solid var(--border-default);background:var(--bg-surface);">
    <span style="color:var(--danger-emphasis);">{icon("warn",16,"currentColor","2")}</span>
    <span style="font-size:var(--text-sm);color:var(--text-secondary);">
      1 blocking issue and 2 undecided columns to settle before anything is created.</span>
    <div style="margin-left:auto;display:flex;align-items:center;gap:var(--space-2);">
      {BTN("Discard", "ghost")}
      <button class="btn btn-primary" style="opacity:.45;">{icon("check",16,"#fff","2")}Create everything</button>
    </div>
  </div>
</div>'''

issues = f'''<div style="width:340px;flex:none;background:var(--bg-canvas);
  border-left:1px solid var(--border-subtle);display:flex;flex-direction:column;overflow:hidden;">
  <div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-4) var(--space-4) var(--space-3);">
    <span style="font-size:var(--text-base);font-weight:700;">What will not come over</span>
    <span class="mono" style="font-size:11px;color:var(--text-tertiary);margin-left:auto;">7</span></div>
  <div style="flex:1;overflow:hidden;padding:0 var(--space-4) var(--space-4);display:flex;
    flex-direction:column;gap:var(--space-4);">
    {issue_group("blocking")}{issue_group("warning")}{issue_group("info")}
  </div>
</div>'''

body = f'''<div style="flex:1;display:flex;min-height:0;">{tab_list}{review}{issues}</div>'''

migration = shell("Sheets", "Q3 delivery.xlsx",
                  chip("Dry run · nothing created yet", "warning"),
                  ["Review", "Progress", "History"], "Review",
                  BTN("Source: Excel workbook", "ghost", "doc")
                  + BTN("12 tabs · 4,310 rows", "ghost", "layers")
                  + BTN("Re-analyse", "secondary", "search"),
                  body, crumb="Northfield Delivery / Delivery / Bring in a workbook")

write('Migration.dc.html', page(migration, theme="light"))
print("Migration written")
