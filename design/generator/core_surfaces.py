from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN

# ---- shared parts (every screen reuses the shell components above) ----
FX = "display:flex;align-items:center;"
COL = "display:flex;flex-direction:column;"
D = lambda s, inner="": f'<div style="{s}">{inner}</div>'
SP = lambda s, inner="": f'<span style="{s}">{inner}</span>'
TT = "color:var(--text-tertiary);"
NEU = lambda t: f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-secondary);border:1px solid var(--border-subtle);">{t}</span>'
CARD = lambda inner, pad="var(--space-4)", extra="": f'<div class="card" style="padding:{pad};{extra}">{inner}</div>'
TH = lambda t, s="": f'<span class="th" style="{s}">{t}</span>'
MONO = lambda t, s="": f'<span class="mono" style="{s}">{t}</span>'
SMALL = lambda t, s="": SP(f"font-size:var(--text-xs);{TT}{s}", t)


def banner(kind, ic, title, body, action=""):
    return D(f'{FX}align-items:flex-start;gap:var(--space-3);padding:var(--space-3);border-radius:var(--radius-md);'
             f'background:var(--{kind}-bg);border:1px solid var(--{kind}-border);',
             SP(f"color:var(--{kind}-fg);flex:none;margin-top:1px;", icon(ic, 17))
             + D("flex:1;min-width:0;",
                 D(f"font-size:var(--text-sm);font-weight:600;color:var(--{kind}-fg);", title)
                 + D(f"font-size:var(--text-xs);color:var(--text-secondary);line-height:17px;margin-top:2px;", body))
             + action)


RETRY = '<button class="btn btn-secondary" style="height:var(--control-sm);">Retry</button>'
label = lambda t: D("margin-bottom:6px;", TH(t))
field = lambda text, s="", mono=False: (
    f'<div class="{"mono" if mono else ""}" style="height:var(--control-md);{FX}gap:var(--space-2);padding:0 var(--space-3);'
    f'border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--bg-surface);font-size:var(--text-sm);{s}">{text}</div>')
select = lambda t, s="": field(SP("flex:1;", t) + SP(TT, icon("down", 15)), s)
sk = lambda w, h=10, r="var(--radius-sm)": SP(f"display:block;width:{w};height:{h}px;border-radius:{r};background:var(--bg-active);")
toggle = lambda on=True: SP(
    f'width:34px;height:20px;border-radius:var(--radius-full);flex:none;background:var({"--brand" if on else "--border-strong"});'
    f'{FX}padding:2px;justify-content:{"flex-end" if on else "flex-start"};',
    SP("width:16px;height:16px;border-radius:99px;background:#fff;"))
sect = lambda title, inner, right="": D(f"{COL}gap:var(--space-3);", D(FX, TH(title) + SP("margin-left:auto;", right)) + inner)

# ============================ 1. Workspace (F005) ============================
TREE = [("Projects", 1, "open", "", ""), ("Q4 Migration", 2, "open", "on", ""), ("Cutover", 3, "leaf", "", ""),
        ("Runbooks", 3, "leaf", "", ""), ("Q1 Rollout", 2, "closed", "", "drag"), ("Discovery", 2, "closed", "", ""),
        ("Operations", 1, "open", "", ""), ("Incidents", 2, "leaf", "", ""), ("Vendor reviews", 2, "loading", "", ""),
        ("Templates", 1, "closed", "", "")]


def tnode(name, depth, kind, on, mark):
    lead = icon("down", 14) if kind == "open" else (icon("chev", 14) if kind in ("closed", "loading") else SP("width:14px;display:inline-block;"))
    s = "background:var(--bg-selected);color:var(--accent-fg);font-weight:600;" if on else ""
    if mark == "drag":
        s += "opacity:.45;border:1px dashed var(--accent-border);border-radius:var(--radius-md);"
    return D(f"{FX}gap:6px;height:30px;padding-left:{8 + (depth - 1) * 16}px;padding-right:var(--space-2);"
             f"font-size:var(--text-sm);color:var(--text-secondary);{s}",
             SP(TT + "display:inline-flex;", lead) + icon("doc", 15) + SP("flex:1;", name)
             + (MONO("6", f"font-size:11px;{TT}") if kind != "leaf" else ""))


tree = "".join(tnode(*t) for t in TREE[:5])
tree += D("height:2px;background:var(--brand);margin:2px 8px 2px 40px;border-radius:2px;position:relative;",
          SP("position:absolute;left:0;top:-3px;width:8px;height:8px;border-radius:99px;background:var(--brand);"))
tree += D("margin:0 var(--space-2) var(--space-2) 40px;display:inline-flex;align-items:center;gap:6px;padding:4px var(--space-2);"
          "border-radius:var(--radius-md);background:var(--bg-raised);box-shadow:var(--shadow-2);"
          "border:1px solid var(--border-default);font-size:var(--text-xs);color:var(--text-secondary);",
          icon("layers", 13) + 'Move <b style="color:var(--text-primary);">Q1 Rollout</b> into Projects · depth 2')
tree += "".join(tnode(*t) for t in TREE[5:9])
tree += D("padding:6px 8px 6px 40px;" + COL + "gap:6px;", sk("62%") + sk("48%") + sk("70%"))
tree += "".join(tnode(*t) for t in TREE[9:])

SHEETS = [("Cutover plan", "Projects / Q4 Migration", "8 min ago", "1,284 rows", "PR", 30, "accent", "Grid"),
          ("Vendor risk register", "Operations / Vendor reviews", "42 min ago", "318 rows", "AD", 210, "warning", "Report"),
          ("Runbook checklist", "Projects / Q4 Migration / Runbooks", "2 h ago", "96 rows", "MW", 120, "accent", "Grid"),
          ("Incident log 2026", "Operations / Incidents", "yesterday", "2,940 rows", "SO", 70, "danger", "Board"),
          ("Rollout capacity", "Projects / Q1 Rollout", "2 d ago", "412 rows", "AD", 210, "success", "Timeline")]
recent = "".join(D(f"{FX}gap:var(--space-3);padding:var(--space-3);border-bottom:1px solid var(--border-subtle);",
                   SP("width:32px;height:32px;border-radius:var(--radius-md);background:var(--accent-bg);color:var(--accent-fg);"
                      "display:inline-flex;align-items:center;justify-content:center;flex:none;", icon("grid", 17))
                   + D("min-width:0;flex:1;", D("font-size:var(--text-sm);font-weight:600;", n) + SMALL(p))
                   + chip(v, k) + MONO(r, f"width:92px;font-size:var(--text-xs);{TT}")
                   + MONO(u, "width:96px;font-size:var(--text-xs);color:var(--text-secondary);") + avatar(i, h))
                 for n, p, u, r, i, h, k, v in SHEETS)

MEMBERS = [("Priya Raman", "PR", 30, "priya@northfield.co", "Owner", "user"), ("Ana Duarte", "AD", 210, "ana@northfield.co", "Admin", "user"),
           ("Delivery guild", "DG", 265, "12 members · SCIM group", "Editor", "group"), ("Marcus Webb", "MW", 120, "marcus@northfield.co", "Editor", "user"),
           ("Sam Okafor", "SO", 70, "sam@northfield.co", "Commenter", "user"), ("Ines Moreau", "IM", 160, "ines@studio-mo.fr", "Viewer", "user")]
members = "".join(D(f"{FX}gap:var(--space-2);height:44px;",
                    (avatar(i, h) if k == "user" else SP("width:24px;height:24px;border-radius:var(--radius-sm);background:var(--bg-active);"
                                                         "color:var(--text-secondary);display:inline-flex;align-items:center;justify-content:center;flex:none;", icon("people", 14)))
                    + D("min-width:0;flex:1;", D("font-size:var(--text-sm);font-weight:500;", n) + SMALL(e, "overflow:hidden;text-overflow:ellipsis;"))
                    + SP("font-size:var(--text-xs);color:var(--text-secondary);", r) + SP(TT, icon("down", 14)))
                  for n, i, h, e, r, k in MEMBERS)

empty = CARD(SP("width:52px;height:52px;border-radius:var(--radius-lg);background:var(--accent-bg);color:var(--accent-fg);"
                "display:inline-flex;align-items:center;justify-content:center;", icon("doc", 26))
             + D("font-size:var(--text-lg);font-weight:600;", "Ops Analytics has no folders yet")
             + D("font-size:var(--text-sm);color:var(--text-secondary);max-width:420px;line-height:19px;",
                 "Created 3 minutes ago by you. Folders hold sheets, reports and documents, and inherit workspace membership.")
             + D("display:flex;gap:var(--space-2);margin-top:var(--space-1);",
                 BTN("Create your first folder", "primary", "plus") + BTN("Import from template", "secondary", "layers")),
             "var(--space-7)", f"{COL}align-items:center;gap:var(--space-3);text-align:center;border-style:dashed;"
             "border-color:var(--border-default);background:var(--bg-sunken);")

ws_body = D("flex:1;display:flex;min-height:0;",
            D("width:288px;flex:none;background:var(--bg-surface);border-right:1px solid var(--border-subtle);" + COL,
              D(f"{FX}gap:var(--space-2);padding:var(--space-3) var(--space-3) var(--space-2);",
                TH("Folders") + MONO("28 / 2,000", f"font-size:11px;{TT}") + SP(f"margin-left:auto;{TT}", icon("plus", 16)))
              + D("flex:1;overflow:hidden;", tree)
              + D(f"border-top:1px solid var(--border-subtle);padding:var(--space-2) var(--space-3);{FX}gap:8px;"
                  "font-size:var(--text-sm);color:var(--text-secondary);",
                  icon("clock", 15) + "Trash" + MONO("3", f"margin-left:auto;font-size:11px;{TT}")))
            + D(f"flex:1;min-width:0;{COL}gap:var(--space-4);padding:var(--space-5);overflow:hidden;",
                banner("warning", "warn", "This workspace changed while you were editing",
                       "Ana Duarte moved 2 folders · tree version 148 → 151 · correlation 8f2c-41ab",
                       '<button class="btn btn-secondary" style="height:var(--control-sm);">Reload</button>')
                + CARD(D(f"{FX}padding:var(--space-3) var(--space-3) var(--space-2);",
                         TH("Recent sheets") + SP("margin-left:auto;font-size:var(--text-xs);color:var(--accent-fg);", "View all 46")) + recent,
                       "0", "overflow:hidden;")
                + empty)
            + D("width:316px;flex:none;background:var(--bg-surface);border-left:1px solid var(--border-subtle);"
                f"padding:var(--space-4);{COL}gap:var(--space-3);",
                D(FX, TH("Members") + MONO("6 of 500", f"margin-left:auto;font-size:11px;{TT}"))
                + banner("danger", "shield", "You can view members but not change them",
                         "Your role on Northfield Delivery is Commenter. Ask an owner for Admin to edit membership.")
                + D(COL, members)
                + D(f"font-size:var(--text-xs);color:var(--danger-fg);{FX}gap:6px;", icon("warn", 14) + "A workspace must keep at least one owner.")
                + D("margin-top:auto;display:flex;gap:var(--space-2);",
                    f'<button class="btn btn-secondary" style="flex:1;justify-content:center;opacity:.5;">{icon("plus", 16)}Add member</button>')))

write('Workspace.dc.html', page(shell("Sheets", "Northfield Delivery", chip("Workspace · owner Priya Raman", "accent"),
      ["Overview", "Sheets", "Members", "Trash"], "Overview",
      BTN("New folder", "secondary", "plus") + BTN("Members", "ghost", "people") + BTN("New sheet", "primary", "grid"),
      ws_body, crumb="Workspaces / Northfield Delivery"), theme="light"))

# ============================ 2. ColumnEditor (F007) ============================
TYPES = [("doc", "Text", 0), ("chart", "Number", 1), ("chart", "Currency", 0), ("calendar", "Date", 0), ("clock", "Datetime", 0),
         ("check", "Checkbox", 0), ("user", "Person", 0), ("flow", "Link", 0), ("layers", "File", 0), ("filter", "Select", 0),
         ("sparkle", "Formula", 0), ("clock", "Duration", 0)]
typegrid = "".join(D(f"{COL}align-items:center;justify-content:center;gap:5px;height:58px;border-radius:var(--radius-md);"
                     f"font-size:var(--text-xs);border:1px solid var({'--brand' if on else '--border-default'});"
                     f"background:var({'--bg-selected' if on else '--bg-surface'});"
                     f"color:var({'--accent-fg' if on else '--text-secondary'});font-weight:{600 if on else 500};",
                     icon(i, 17) + n) for i, n, on in TYPES)

# option swatches name colour tokens, as F007 requires (12 token names, never free-form hex)
OPTIONS = [("Todo", "var(--text-tertiary)", 0), ("Doing", "var(--brand)", 0), ("Blocked", "var(--danger-emphasis)", 0),
           ("In review", "var(--warning-emphasis)", 0), ("Done", "var(--success-emphasis)", 0),
           ("Deferred", "var(--accent-emphasis)", 1)]
optlist = "".join(D(f"{FX}gap:var(--space-2);height:32px;padding:0 var(--space-2);border-radius:var(--radius-sm);"
                    f"background:var(--bg-surface);border:1px solid var(--border-subtle);opacity:{.55 if a else 1};",
                    SP(TT, icon("dots", 14)) + SP(f"width:12px;height:12px;border-radius:99px;background:{c};flex:none;")
                    + SP("flex:1;font-size:var(--text-sm);", n) + (NEU("Archived") if a else "")
                    + MONO("0" if a else "148", f"font-size:11px;{TT}")) for n, c, a in OPTIONS)

GRID_COLS = [("Task", 260), ("Status", 128), ("Owner", 132), ("Due", 104), ("Estimate", 120), ("Total", 108)]
GRID_ROWS = [("Vendor security review", "Doing", "accent", "PR", 30, "Mar 14", "12", "", "18.0"),
             ("Data migration dry run", "Blocked", "danger", "MW", 120, "Mar 18", "24", "", "36.0"),
             ("Cutover runbook draft", "Doing", "accent", "AD", 210, "Mar 21", "n/a", "bad", "#TYPE"),
             ("Pilot tenant provisioning", "Done", "success", "SO", 70, "Mar 08", "16", "", "16.0"),
             ("Permission model sign-off", "In review", "warning", "PR", 30, "Mar 25", "6", "", "9.0"),
             ("Load test 100k rows", "Todo", "neutral", "–", 0, "Apr 02", "two days", "bad", "#TYPE"),
             ("Accessibility audit", "Doing", "accent", "AD", 210, "Apr 04", "14", "", "21.0"),
             ("Rollback drill", "Todo", "neutral", "MW", 120, "Apr 09", "10", "pend", "…")]
OWNER = {"PR": "Priya", "MW": "Marcus", "AD": "Ana", "SO": "Sam", "–": "Unassigned"}


def gcell(v, w, bad="", mono=False):
    warn = (SP("color:var(--danger-emphasis);margin-left:auto;", icon("warn", 14)) if bad == "bad"
            else (SP("margin-left:auto;", sk("34", 8, "99px")) if bad == "pend" else ""))
    return (f'<div class="cell {"mono" if mono else ""}" style="width:{w}px;flex:none;'
            f'color:var(--text-{"primary" if not bad else "secondary"});">{v}{warn}</div>')


grid_rows = "".join(D(f"display:flex;background:var({'--bg-surface' if k % 2 == 0 else '--bg-sunken'});",
                      gcell(t, 260) + f'<div class="cell" style="width:128px;flex:none;">{chip(s, sk_) if sk_ != "neutral" else NEU(s)}</div>'
                      + f'<div class="cell" style="width:132px;flex:none;gap:8px;color:var(--text-secondary);">'
                      + (avatar(i, h) if i != "–" else SP("width:24px;height:24px;border-radius:99px;border:1px dashed var(--border-strong);display:inline-block;flex:none;"))
                      + SP("overflow:hidden;text-overflow:ellipsis;white-space:nowrap;", OWNER[i]) + "</div>"
                      + gcell(d, 104, mono=True) + gcell(e, 120, b, True) + gcell(tot, 108, b, True))
                    for k, (t, s, sk_, i, h, d, e, b, tot) in enumerate(GRID_ROWS))

optpanel = D("position:absolute;left:288px;top:118px;width:296px;border-radius:var(--radius-lg);background:var(--bg-raised);"
             f"border:1px solid var(--border-default);box-shadow:var(--shadow-3);padding:var(--space-3);{COL}gap:var(--space-2);",
             D(FX, TH("Status · select options") + MONO("6 / 200", f"margin-left:auto;font-size:11px;{TT}")) + optlist
             + D(f"{FX}gap:8px;height:30px;color:var(--accent-fg);font-size:var(--text-sm);", icon("plus", 15) + "Add option")
             + SMALL("Archived options stay valid on existing cells and are rejected on new writes. Alt+↑/↓ reorders.", "line-height:16px;"))

ce_drawer = D(f"width:404px;flex:none;background:var(--bg-surface);border-left:1px solid var(--border-subtle);{COL}",
              D(f"padding:var(--space-4);border-bottom:1px solid var(--border-subtle);{FX}align-items:flex-start;gap:8px;",
                D("flex:1;", D("font-size:var(--text-lg);font-weight:600;", "Edit column")
                  + MONO("COL-0f31 · v7 · position 3", f"font-size:var(--text-xs);{TT}display:block;margin-top:2px;")) + NEU("Estimate"))
              + D(f"flex:1;padding:var(--space-4);{COL}gap:var(--space-4);overflow:hidden;",
                  D("", label("Label") + field(SP("flex:1;", "Estimate") + MONO("8/120", f"font-size:11px;{TT}")))
                  + sect("Type", D("display:grid;grid-template-columns:repeat(4,1fr);gap:var(--space-2);", typegrid))
                  + banner("warning", "warn", "Changing text → number will coerce 1,284 cells",
                           "3 cells cannot be parsed and will hold state <b>invalid</b> with code <b>type_mismatch</b>: “n/a”, “two days”, “tbd”. "
                           "Above 10,000 rows this runs as an async job and cells show pending.")
                  + D("display:flex;gap:var(--space-2);",
                      '<button class="btn btn-primary" style="flex:1;justify-content:center;">Apply type change</button>'
                      + BTN("Preview 3 cells", "secondary", "search"))
                  + sect("Validation · number",
                         D(f"{COL}gap:var(--space-3);",
                           D(f"{FX}gap:var(--space-2);font-size:var(--text-sm);", toggle(True) + "Required")
                           + D("display:flex;gap:var(--space-2);",
                               D("flex:1;", label("Min") + field(MONO("0")))
                               + D("flex:1;", label("Max") + field(MONO("240")))
                               + D("flex:1;", label("Precision") + select("2")))
                           + D(f"{FX}gap:var(--space-2);font-size:var(--text-sm);", toggle(False) + "Unique across rows")
                           + SMALL("4 of 16 rules used · one row per rule name")), NEU("2 rules")))
              + D("padding:var(--space-4);border-top:1px solid var(--border-subtle);display:flex;gap:var(--space-2);",
                  '<button class="btn btn-primary" style="flex:1;justify-content:center;">Save column</button>' + BTN("Cancel", "ghost")))

ce_body = D("flex:1;display:flex;min-height:0;position:relative;",
            D(f"flex:1;min-width:0;{COL}background:var(--bg-surface);overflow:hidden;",
              D("display:flex;height:36px;background:var(--bg-sunken);border-bottom:1px solid var(--border-default);",
                "".join(f'<div class="th" style="width:{w}px;flex:none;{FX}gap:6px;padding:0 var(--space-3);">{c}</div>' for c, w in GRID_COLS)
                + f'<div class="th" style="flex:1;{FX}padding:0 var(--space-3);color:var(--accent-fg);">{icon("plus", 14)}</div>')
              + grid_rows
              + D(f"height:var(--row-h);{FX}gap:8px;padding:0 var(--space-3);{TT}font-size:var(--text-sm);", icon("plus", 15) + "Add row")
              + D(f"margin-top:auto;height:40px;{FX}gap:var(--space-3);padding:0 var(--space-5);"
                  f"border-top:1px solid var(--border-subtle);font-size:var(--text-xs);{TT}",
                  MONO("8 of 1,284 rows") + "<span>·</span><span>7 of 500 columns</span>"
                  + SP("margin-left:auto;display:inline-flex;align-items:center;gap:6px;color:var(--danger-fg);",
                       icon("warn", 13) + "3 invalid cells in Estimate")))
            + optpanel + ce_drawer)

write('ColumnEditor.dc.html', page(shell("Sheets", "Cutover plan", chip("Column editor", "accent"),
      ["Grid", "Board", "Timeline", "Calendar", "Cards"], "Grid",
      BTN("Validate column", "ghost", "check") + BTN("Hide", "ghost", "panel") + BTN("Share", "secondary", "people"),
      ce_body), theme="dark"))

# ============================ 3. Schedules (F011) ============================
IV = ["09:00 – 12:30", "13:15 – 17:00"]
WEEK = [("Monday", IV, "7.25 h"), ("Tuesday", IV, "7.25 h"), ("Wednesday", IV, "7.25 h"), ("Thursday", IV, "7.25 h"),
        ("Friday", ["09:00 – 12:30", "13:15 – 15:30"], "5.75 h"), ("Saturday", [], "0 h"), ("Sunday", [], "0 h")]
week = "".join(D(f"{FX}gap:var(--space-2);height:40px;border-bottom:1px solid var(--border-subtle);",
                 SP(f"width:96px;font-size:var(--text-sm);font-weight:{600 if ivs else 400};"
                    f"color:var(--text-{'primary' if ivs else 'tertiary'});", d)
                 + ("".join(f'<span class="chip mono" style="background:var(--accent-bg);color:var(--accent-fg);'
                            f'border:1px solid var(--accent-border);height:24px;">{iv}</span>' for iv in ivs)
                    or SP(f"font-size:var(--text-sm);{TT}", "Non-working"))
                 + MONO(hrs, f"margin-left:auto;font-size:var(--text-xs);{TT}") + SP(TT, icon("plus", 15)))
               for d, ivs, hrs in WEEK)

EXC = [("2026-10-03", "Holiday", "danger", "German Unity Day", "—"), ("2026-11-27", "Working", "success", "Company offsite", "10:00 – 16:00"),
       ("2026-12-24", "Working", "success", "Christmas Eve (half day)", "09:00 – 13:00"), ("2026-12-25", "Holiday", "danger", "Christmas Day", "—"),
       ("2026-12-26", "Holiday", "danger", "Boxing Day", "—"), ("2027-01-01", "Holiday", "danger", "New Year's Day", "—")]
exc = "".join(D(f"{FX}height:34px;border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);",
                MONO(d, "width:120px;color:var(--text-secondary);") + SP("width:110px;", chip(k, kk)) + SP("flex:1;", lb)
                + MONO(h, "width:140px;color:var(--text-secondary);") + SP(TT, icon("dots", 16))) for d, k, kk, lb, h in EXC)

roles = "".join(D("", label(k) + select(v)) for k, v in
                [("Start column", "Start date · date"), ("End column", "Finish date · date"),
                 ("Duration column", "Effort (days) · duration"), ("Milestone column", "Is milestone · checkbox"),
                 ("Percent complete", "% complete · number")])

preview = D(f"{COL}gap:var(--space-2);",
            D(f"{FX}gap:8px;font-size:var(--text-sm);font-weight:600;", "Data migration dry run" + NEU("3 d"))
            + "".join(D(f"{FX}height:28px;font-size:var(--text-sm);border-bottom:1px solid var(--border-subtle);",
                        SP("width:158px;color:var(--text-secondary);", z) + MONO(s, "flex:1;")
                        + SP(TT + "margin:0 6px;", "→") + MONO(e))
                      for z, s, e in [("Sheet · Europe/Berlin", "Fri 11 Sep 09:00", "Wed 16 Sep 15:30"),
                                      ("You · America/New_York", "Fri 11 Sep 03:00", "Wed 16 Sep 09:30"),
                                      ("Stored · UTC", "2026-09-11T07:00Z", "2026-09-16T13:30Z")])
            + D(f"{FX}gap:8px;padding-top:var(--space-1);", sk("120", 10) + SMALL("recomputing 412 rows…"))
            + banner("success", "calendar", "Snapped to the next working day",
                     "Start moved from Sat 12 Sep → Mon 14 Sep. Skipped Sat, Sun. add_working_days(Fri 11 Sep, 3) = Wed 16 Sep."))

sc_body = D("flex:1;display:flex;min-height:0;",
            D(f"flex:1;min-width:0;padding:var(--space-5);{COL}gap:var(--space-4);overflow:hidden;",
              CARD(D(f"{FX}gap:var(--space-3);", TH("Working calendar") + chip("Tenant default", "accent")
                     + SP("margin-left:auto;display:flex;gap:var(--space-2);", BTN("Duplicate", "ghost", "layers") + BTN("Save", "primary", "check")))
                   + D("display:flex;gap:var(--space-3);",
                       D("flex:1.4;", label("Name") + field("Standard"))
                       + D("flex:1.4;", label("Timezone") + select("Europe/Berlin (CEST, UTC+2)"))
                       + D("width:132px;", label("Hours per day") + field(MONO("7.25"))))
                   + D("", week)
                   + SMALL("At most 4 intervals per weekday · intervals may not overlap · 36 h working week"),
                   "var(--space-4)", f"{COL}gap:var(--space-3);")
              + CARD(D(f"{FX}gap:var(--space-3);", TH("Exceptions &amp; holidays") + MONO("6 of 400", f"font-size:11px;{TT}")
                       + SP("margin-left:auto;", BTN("Add exception", "secondary", "plus")))
                     + banner("danger", "warn", "Could not load 2027 exceptions",
                              "Request failed after 3 attempts · correlation_id 4b71-90de-2f14 · showing cached rows from 09:41.", RETRY)
                     + D("", exc), "var(--space-4)", f"{COL}gap:var(--space-3);"))
            + D("width:392px;flex:none;background:var(--bg-surface);border-left:1px solid var(--border-subtle);"
                f"padding:var(--space-4);{COL}gap:var(--space-4);overflow:hidden;",
                sect("Sheet schedule settings",
                     D(f"{COL}gap:var(--space-3);", roles + D("", label("Calendar") + select("Standard · Europe/Berlin"))
                       + D("", label("Dependency lag") + D("opacity:.5;", select("Finish-to-start · 0 d"))
                           + SMALL("Set in Dependencies — lag and predecessors belong to F012, not schedule settings.", "margin-top:4px;display:block;"))),
                     NEU("Cutover plan"))
                + sect("Timezone-aware preview", preview)
                + D("margin-top:auto;display:flex;gap:var(--space-2);",
                    '<button class="btn btn-primary" style="flex:1;justify-content:center;">Save settings</button>' + BTN("Cancel", "ghost"))))

write('Schedules.dc.html', page(shell("Calendar", "Working calendars", chip("Admin · schedules", "accent"),
      ["Calendars", "Schedule settings", "Exceptions", "Audit"], "Calendars",
      BTN("Timezone: Europe/Berlin", "ghost", "clock") + BTN("New calendar", "primary", "plus"),
      sc_body, crumb="Admin / Working calendars"), theme="light"))

# ============================ 4. FormulaEditor (F035) ============================
tok = lambda t, c: SP(f"color:var(--{c});", t)
colref = lambda t: SP("display:inline-flex;align-items:center;height:20px;padding:0 6px;border-radius:var(--radius-sm);"
                      "background:var(--accent-bg);color:var(--accent-fg);border:1px solid var(--accent-border);"
                      "font-size:var(--text-xs);font-weight:600;", t)
expr = (SP(TT, "=") + tok("SUM", "accent-emphasis") + "(" + tok("CHILDREN", "accent-emphasis") + "(" + colref("Estimate") + ")) "
        + tok("*", "text-secondary") + " " + tok("IF", "accent-emphasis") + "(" + colref("Priority") + " " + tok("=", "text-secondary")
        + " " + tok("&quot;High&quot;", "success-fg") + ", " + tok("1.5", "warning-fg") + ", " + tok("1", "warning-fg") + ")"
        + tok(" * ", "text-secondary") + colref("Weighted score")
        + SP("display:inline-block;width:1.5px;height:18px;background:var(--brand);vertical-align:-4px;"))

FUNCS = [("Aggregation", [("SUM(number…)", "number"), ("AVG(number…)", "number"), ("COUNTIF(range, criterion)", "number"),
                          ("SUMIF(range, criterion, sum)", "number")]),
         ("Conditional", [("IF(test, then, else)", "any"), ("IFERROR(value, fallback)", "any"), ("AND(bool…)", "boolean"),
                          ("ISBLANK(value)", "boolean")]),
         ("Text", [("CONCAT(text…)", "text"), ("LEFT(text, n)", "text"), ("SUBSTITUTE(t, old, new)", "text")]),
         ("Datetime", [("DATEADD(date, n, unit)", "date"), ("NETWORKDAYS(start, end)", "number"), ("WEEKDAY(date)", "number")]),
         ("Hierarchy", [("CHILDREN([col])", "range"), ("PARENT([col])", "any"), ("DESCENDANTS([col])", "range")]),
         ("Cross-sheet", [("LOOKUP({sheet}!{col}, key, {col})", "any")])]
funclist = "".join(D(f"{COL}gap:2px;margin-bottom:var(--space-3);", TH(g, "margin-bottom:4px;display:block;")
                     + "".join(D(f"{FX}gap:8px;height:28px;padding:0 var(--space-2);border-radius:var(--radius-sm);"
                                 f"background:var({'--bg-selected' if s.startswith('SUM(') else 'transparent'});",
                                 SP(TT, icon("sparkle", 13))
                                 + MONO(s, f"font-size:var(--text-xs);flex:1;color:var(--text-{'primary' if s.startswith('SUM(') else 'secondary'});"
                                        "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;")
                                 + SP(f"font-size:11px;{TT}", r)) for s, r in fs)) for g, fs in FUNCS)

PREV = [("Cutover runbook draft", "8", "High", "18.0", "ok"), ("Data migration dry run", "24", "High", "36.0", "ok"),
        ("Vendor security review", "12", "Normal", "12.0", "ok"), ("Rollout capacity model", "16", "High", "#CYCLE", "cycle"),
        ("Load test 100k rows", "20", "Normal", "", "pending"), ("Archived vendor sheet", "—", "Low", "#REF", "ref")]
resultcell = lambda v, st: (SP("display:inline-flex;align-items:center;gap:6px;", sk("46", 9, "99px")) if st == "pending"
                            else (MONO(v) if st == "ok" else chip(v, "danger" if st == "cycle" else "warning")))
prev = "".join(D(f"{FX}height:32px;border-bottom:1px solid var(--border-subtle);font-size:var(--text-sm);",
                 SP("flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;", t)
                 + MONO(e, "width:80px;color:var(--text-secondary);") + SP("width:92px;", NEU(p))
                 + SP("width:96px;text-align:right;", resultcell(v, st))) for t, e, p, v, st in PREV)

cyclegraph = "".join(SP("display:inline-flex;align-items:center;gap:6px;",
                        f'<span class="chip mono" style="background:var(--danger-bg);color:var(--danger-fg);'
                        f'border:1px solid var(--danger-border);height:24px;">{n}</span>'
                        + (SP("color:var(--danger-fg);", "→") if arrow else ""))
                     for n, arrow in [("Total", 1), ("Weighted score", 1), ("Risk index", 1), ("Total", 0)])

fe_body = D("flex:1;display:flex;min-height:0;",
            D(f"flex:1;min-width:0;padding:var(--space-5);{COL}gap:var(--space-4);overflow:hidden;",
              CARD(D(f"{FX}gap:var(--space-3);", TH("Expression") + NEU("Result type · number")
                     + MONO("42 nodes / 10,000", f"margin-left:auto;font-size:var(--text-xs);{TT}"))
                   + f'<div class="mono" style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--bg-sunken);'
                     f'border:1px solid var(--border-default);font-size:var(--text-base);line-height:26px;min-height:76px;">{expr}</div>'
                   + D(f"{FX}gap:var(--space-2);flex-wrap:wrap;", TH("References", "margin:0;") + colref("Estimate") + colref("Priority")
                       + colref("Weighted score") + NEU("Risk register!Score")
                       + SP("margin-left:auto;display:flex;gap:var(--space-2);",
                            BTN("Formula graph", "ghost", "flow") + '<button class="btn btn-primary">Save formula</button>')),
                   "var(--space-4)", f"{COL}gap:var(--space-3);")
              + banner("danger", "warn", "Circular reference — this formula cannot be saved",
                       'field_errors.expression = <span class="mono">cycle:col_total,col_weighted,col_risk</span>. '
                       '<b>Total</b> reads <b>Weighted score</b>, which reads <b>Risk index</b>, which reads <b>Total</b> again. '
                       'Remove one edge, or reference a snapshot column instead.',
                       '<button class="btn btn-secondary" style="height:var(--control-sm);">Open graph</button>')
              + CARD(cyclegraph + SMALL("detected at PUT /formula · depth 3", "margin-left:auto;"),
                     "var(--space-3) var(--space-4)", f"{FX}gap:8px;flex-wrap:wrap;border-color:var(--danger-border);")
              + CARD(D(f"{FX}gap:var(--space-3);", TH("Live preview · 6 sample rows")
                       + MONO("evaluate · 14 ms of 2,000 ms budget", f"margin-left:auto;font-size:var(--text-xs);{TT}"))
                     + D(f"{FX}height:24px;", TH("Row", "flex:1;") + TH("Estimate", "width:80px;") + TH("Priority", "width:92px;")
                         + TH("Result", "width:96px;text-align:right;")) + prev
                     + D(f"{FX}gap:var(--space-3);font-size:var(--text-xs);{TT}padding-top:var(--space-2);",
                         "<span>#CYCLE cycle</span><span>#REF missing_reference</span><span>#TYPE type_mismatch</span>"
                         "<span>#TIMEOUT timeout</span>" + SP("margin-left:auto;", "4,200 cells queued for recalculation")),
                     "var(--space-4)", f"{COL}gap:var(--space-2);flex:1;overflow:hidden;"))
            + D("width:352px;flex:none;background:var(--bg-surface);border-left:1px solid var(--border-subtle);"
                f"padding:var(--space-4);{COL}overflow:hidden;",
                D(f"{FX}margin-bottom:var(--space-3);", TH("Function reference") + MONO("48 functions", f"margin-left:auto;font-size:11px;{TT}"))
                + field(icon("search", 15) + SP(TT, "Filter functions")) + D("height:var(--space-3);")
                + D("flex:1;overflow:hidden;", funclist)))

write('FormulaEditor.dc.html', page(shell("Sheets", "Total", chip("Formula column", "accent"),
      ["Grid", "Board", "Timeline", "Calendar", "Cards"], "Grid",
      BTN("Recalculate all", "ghost", "flow") + BTN("Read-only view", "ghost", "doc") + BTN("Share", "secondary", "people"),
      fe_body, crumb="Northfield Delivery / Migration / Cutover plan / Total"), theme="dark"))

# ============================ 5. Comments (F016) ============================
mention = lambda t: SP("display:inline-flex;align-items:center;height:20px;padding:0 6px;border-radius:var(--radius-sm);"
                       "background:var(--accent-bg);color:var(--accent-fg);font-weight:600;font-size:var(--text-xs);", "@" + t)
comment = lambda ini, hue, who, when, body, meta="", reply=False: D(
    f"display:flex;gap:var(--space-2);padding-left:{28 if reply else 0}px;",
    avatar(ini, hue) + D("flex:1;min-width:0;",
                         D(f"{FX}gap:8px;", SP("font-size:var(--text-sm);font-weight:600;", who)
                           + MONO(when, f"font-size:11px;{TT}") + meta + SP(f"margin-left:auto;{TT}", icon("dots", 15)))
                         + D("font-size:var(--text-sm);line-height:20px;color:var(--text-secondary);margin-top:2px;", body)))

thread1 = CARD(D(f"{COL}gap:var(--space-3);",
                 D(f"{FX}gap:8px;", NEU("Row · Data migration dry run")
                   + SP("margin-left:auto;display:flex;gap:var(--space-2);",
                        f'<button class="btn btn-ghost" style="height:var(--control-sm);">{icon("check", 15)}Resolve</button>'))
                 + comment("PR", 30, "Priya Raman", "Mar 16 · 09:12",
                           f'The dry run failed on the second batch. {mention("Dana Ruiz")} can you confirm the staging snapshot was taken '
                           'after the schema change? Blocking the Mar 18 window until we know.')
                 + comment("DR", 340, "Dana Ruiz", "Mar 16 · 09:41",
                           "Snapshot is from 02:00, before the migration. Re-taking it now — should be ready in about 40 minutes.", reply=True)
                 + comment("MW", 120, "Marcus Webb", "Mar 16 · 10:20",
                           f'Re-ran with the new snapshot, 2 of 1,284 rows still reject. Raised as {mention("Delivery guild")} follow-up.',
                           NEU("edited"), True)
                 + D(f"{FX}gap:8px;font-size:var(--text-xs);color:var(--warning-fg);", icon("warn", 14)
                     + '<span><b class="mono">@[user:tom@acme.dev]</b> has no access to this row — kept as plain text, not notified.</span>')))

thread2 = CARD(D(f"{FX}gap:var(--space-2);", SP("color:var(--success-emphasis);", icon("check", 17))
                 + D("flex:1;min-width:0;", D("font-size:var(--text-sm);font-weight:600;", "Do we need a second approver for the cutover?")
                     + SMALL("4 comments · resolved by Ana Duarte · Mar 14"))
                 + chip("Resolved", "success") + SP(TT, icon("chev", 15))), "var(--space-3)")

thread3 = CARD(D(f"{COL}gap:var(--space-3);",
                 D(f"{FX}gap:8px;", NEU("Cell · Due") + MONO("THR-91c4", f"font-size:11px;{TT}margin-left:auto;"))
                 + D(f"display:flex;gap:var(--space-2);align-items:center;padding:var(--space-2);border-radius:var(--radius-md);"
                     f"background:var(--bg-sunken);border:1px dashed var(--border-default);font-size:var(--text-sm);{TT}",
                     icon("doc", 15) + "[deleted] · comment removed by its author, kept because it has replies")
                 + comment("SO", 70, "Sam Okafor", "Mar 15 · 16:02",
                           "Agreed — moving the date to Mar 21 and telling the vendor today.", reply=True)))

loading_thread = CARD(D("display:flex;gap:var(--space-2);", SP("width:24px;height:24px;border-radius:99px;background:var(--bg-active);flex:none;")
                        + D(f"flex:1;{COL}gap:6px;", sk("38%") + sk("92%") + sk("64%"))))

ACT = [("PR", 30, "Priya Raman", "user", "row.updated", "Status", "In progress", "Blocked", "Mar 16 · 09:10"),
       ("AU", 190, "Escalation rule", "automation", "workflow-run.completed", "Health", "On track", "At risk", "Mar 16 · 09:11"),
       ("MW", 120, "Marcus Webb", "user", "cell.updated", "Due", "2026-03-18", "2026-03-21", "Mar 16 · 10:22"),
       ("DR", 340, "Dana Ruiz", "user", "comment.created", "thread THR-4a20", "", "", "Mar 16 · 09:41"),
       ("IN", 265, "Jira sync", "integration", "cell.updated", "External ref", "OPS-118", "OPS-204", "Mar 15 · 22:04"),
       ("AD", 210, "Ana Duarte", "user", "comment.resolved", "thread THR-33c9", "", "", "Mar 14 · 11:30")]
KINDCHIP = {"user": ("accent", "Person"), "automation": ("warning", "Automation"), "integration": ("accent", "Integration")}


def diff(f, a, b):
    if not a:
        return SMALL(f)
    return SP("display:inline-flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:var(--text-xs);",
              SP(TT, f) + f'<span class="chip mono" style="background:var(--danger-bg);color:var(--danger-fg);'
              f'border:1px solid var(--danger-border);text-decoration:line-through;">{a}</span>' + SP(TT, "→")
              + f'<span class="chip mono" style="background:var(--success-bg);color:var(--success-fg);'
                f'border:1px solid var(--success-border);">{b}</span>')


activity = "".join(D("display:flex;gap:var(--space-3);padding:var(--space-3) 0;border-bottom:1px solid var(--border-subtle);",
                     D(f"{COL}align-items:center;flex:none;width:24px;",
                       (avatar(i, h) if k == "user" else SP("width:24px;height:24px;border-radius:var(--radius-sm);background:var(--warning-bg);"
                                                            "color:var(--warning-fg);display:inline-flex;align-items:center;justify-content:center;", icon("flow", 14)))
                       + SP("flex:1;width:1px;background:var(--border-subtle);margin-top:6px;"))
                     + D(f"flex:1;min-width:0;{COL}gap:6px;",
                         D(f"{FX}gap:8px;", SP("font-size:var(--text-sm);font-weight:600;", n)
                           + ("" if k == "user" else chip(KINDCHIP[k][1], KINDCHIP[k][0]))
                           + MONO(w, f"margin-left:auto;font-size:11px;{TT}"))
                         + MONO(a, "font-size:11px;color:var(--accent-fg);") + diff(f, o, nv)))
                   for i, h, n, k, a, f, o, nv, w in ACT)

seg = "".join(D(f"height:28px;{FX}padding:0 var(--space-3);border-radius:var(--radius-md);font-size:var(--text-sm);"
                f"font-weight:{600 if on else 500};background:var({'--bg-surface' if on else 'transparent'});"
                f"box-shadow:{'var(--shadow-1)' if on else 'none'};color:var({'--text-primary' if on else '--text-secondary'});", t)
              for t, on in [("Comments · 3", 1), ("Activity · 148", 0)])

cm_body = D("flex:1;display:flex;min-height:0;",
            D(f"flex:1;min-width:0;padding:var(--space-5);{COL}gap:var(--space-3);overflow:hidden;",
              D(f"{FX}gap:var(--space-2);",
                D("display:flex;gap:2px;padding:3px;border-radius:var(--radius-md);background:var(--bg-sunken);"
                  "border:1px solid var(--border-subtle);", seg) + NEU("Unresolved") + NEU("All targets")
                + SMALL("Ctrl+Enter sends · R resolves", "margin-left:auto;"))
              + thread1 + thread3 + thread2 + loading_thread
              + D(f"margin-top:auto;{FX}gap:var(--space-2);padding:var(--space-3);border-radius:var(--radius-md);"
                  "background:var(--bg-sunken);border:1px dashed var(--border-default);",
                  SP(TT, icon("shield", 17))
                  + D("font-size:var(--text-sm);color:var(--text-secondary);",
                      '<b style="color:var(--text-primary);">You can view but not comment.</b> '
                      "Your role on Cutover plan is Viewer — ask an owner for Commenter to reply or resolve.")))
            + D("width:412px;flex:none;background:var(--bg-surface);border-left:1px solid var(--border-subtle);"
                f"padding:var(--space-4);{COL}gap:var(--space-3);overflow:hidden;",
                D(FX, TH("Activity") + MONO("newest first · 148", f"margin-left:auto;font-size:11px;{TT}"))
                + D("display:flex;gap:6px;flex-wrap:wrap;", NEU("Actor: any") + chip("changed_field: Status", "accent")
                    + NEU("Since Mar 01") + NEU("action: row.*"))
                + D("flex:1;overflow:hidden;", activity)
                + D(f"{FX}gap:8px;font-size:var(--text-xs);{TT}border-top:1px solid var(--border-subtle);padding-top:var(--space-2);",
                    icon("clock", 13) + "Projection lag 0.4 s · idempotent by source_event_id")))

write('Comments.dc.html', page(shell("Sheets", "Data migration dry run", chip("Row · ROW-2471", "accent"),
      ["Details", "Conversation", "Activity", "Attachments"], "Conversation",
      BTN("Resolve thread", "ghost", "check") + BTN("Follow", "ghost", "bell") + BTN("Share", "secondary", "people"),
      cm_body, crumb="Northfield Delivery / Migration / Cutover plan"), theme="light"))

print("core surfaces written")
