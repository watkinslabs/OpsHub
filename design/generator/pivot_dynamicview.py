from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
import _charts as ch

# ---------------- Pivot ----------------
ROWS=[("Discovery",[38,12,4,54],"Migration"),("Build",[52,19,7,78],"Migration"),
      ("Harden",[21,14,9,44],"Migration"),("Launch",[8,5,2,15],"Migration"),
      ("Discovery",[14,6,1,21],"Mobile"),("Build",[26,11,5,42],"Mobile")]
cols=["Done","In progress","Blocked","Total"]
prow="".join(f'''<div style="display:flex;height:34px;align-items:center;border-bottom:1px solid var(--border-subtle);
  font-size:var(--text-sm);">
  <span style="width:130px;flex:none;padding-left:var(--space-5);color:var(--text-secondary);">{g}</span>
  <span style="width:130px;flex:none;font-weight:500;">{p}</span>
  {"".join(f'<span class="mono" style="flex:1;text-align:right;padding-right:var(--space-4);{"font-weight:600;" if i==3 else "color:var(--text-secondary);"}">{v}</span>' for i,v in enumerate(vals))}
</div>''' for p,vals,g in ROWS)

pivot = shell("Dashboards","Delivery pivot", chip("Live","success"),
  ["Configure","Output","Schedule","Permissions"],"Configure",
  BTN("Recalculate","ghost","clock")+BTN("Export","secondary","doc")+BTN("Save output","primary","check"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="width:260px;flex:none;border-right:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-4);">
      {"".join(f'''<div><span class="th">{t}</span>
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:8px;">
          {"".join(f'<div style="display:flex;align-items:center;gap:8px;padding:6px var(--space-2);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);background:var(--bg-surface);font-size:var(--text-xs);">{icon("dots",13)}{n}<span class="mono" style="margin-left:auto;color:var(--text-tertiary);">{k}</span></div>' for n,k in items)}
          <div style="height:30px;border:1px dashed var(--border-strong);border-radius:var(--radius-sm);
            display:flex;align-items:center;justify-content:center;font-size:11px;color:var(--text-tertiary);">drop field</div>
        </div></div>'''
        for t,items in [("Rows",[("Programme","group"),("Phase","select")]),
                        ("Columns",[("Status","select")]),
                        ("Measures",[("Count of rows","count"),("Sum of effort","sum")]),
                        ("Filters",[("Due before 30 Jun","date")])])}
    </div>
    <div style="flex:1;display:flex;flex-direction:column;background:var(--bg-surface);overflow:hidden;">
      <div style="display:flex;height:36px;align-items:center;background:var(--bg-sunken);
        border-bottom:1px solid var(--border-default);">
        <span class="th" style="width:130px;flex:none;padding-left:var(--space-5);">Programme</span>
        <span class="th" style="width:130px;flex:none;">Phase</span>
        {"".join(f'<span class="th" style="flex:1;text-align:right;padding-right:var(--space-4);">{c}</span>' for c in cols)}</div>
      {prow}
      <div style="display:flex;height:38px;align-items:center;background:var(--bg-sunken);
        border-top:1px solid var(--border-default);font-size:var(--text-sm);font-weight:600;">
        <span style="width:260px;flex:none;padding-left:var(--space-5);">Grand total</span>
        {"".join(f'<span class="mono" style="flex:1;text-align:right;padding-right:var(--space-4);">{v}</span>' for v in [159,67,28,254])}</div>
      <div style="padding:var(--space-5);display:flex;gap:var(--space-4);">
        <div class="card" style="flex:1;padding:var(--space-4);">
          <span class="th">By status</span>
          <div style="margin-top:var(--space-3);">{ch.stacked(420,120,[[38,12,4],[52,19,7],[21,14,9],[8,5,2]],labels=["Disc","Build","Hard","Launch"])}</div></div>
        <div class="card" style="width:280px;padding:var(--space-4);display:flex;flex-direction:column;gap:8px;">
          <span class="th">Output</span>
          <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:18px;">
            Saved outputs are a rebuildable cache with their source versions recorded — reopening after a
            source changes shows the staleness rather than silently different numbers.</div>
          <div class="mono" style="font-size:11px;color:var(--text-tertiary);">254 rows · computed 41s ago</div></div>
      </div>
    </div>
  </div>''', crumb="Northfield Delivery")
write('Pivot.dc.html', page(pivot, theme="light"))

# ---------------- Dynamic View (scoped external editing) ----------------
dv = shell("Sheets","Vendor status — shared view", chip("Scoped view","warning"),
  ["Fields","Recipients","Activity","Settings"],"Fields",
  BTN("Preview as recipient","ghost","search")+BTN("Revoke access","ghost")+BTN("Share","primary","people"),
  f'''<div style="flex:1;display:flex;min-height:0;">
    <div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-4);overflow:hidden;">
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span class="th">Fields the recipient sees</span>
        {"".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) 0;
          border-bottom:1px solid var(--border-subtle);">
          <span style="color:var(--text-tertiary);">{icon("doc",15)}</span>
          <span style="flex:1;font-size:var(--text-sm);">{n}</span>
          <span style="width:110px;">{chip(v,"accent" if v=="Visible" else ("success" if v=="Editable" else "neutral"))}</span>
        </div>''' if v!="Hidden" else f'''<div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) 0;
          border-bottom:1px solid var(--border-subtle);opacity:.55;">
          <span style="color:var(--text-tertiary);">{icon("doc",15)}</span>
          <span style="flex:1;font-size:var(--text-sm);">{n}</span>
          <span style="width:110px;"><span class="chip" style="background:var(--bg-sunken);color:var(--text-tertiary);border:1px solid var(--border-subtle);">Hidden</span></span></div>'''
          for n,v in [("Vendor name","Visible"),("Review status","Editable"),("Evidence","Editable"),
                      ("Internal risk score","Hidden"),("Contract value","Hidden"),("Owner notes","Hidden")])}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);">
        <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
          <span class="th">Row filter</span>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            {"".join(f'<span class="chip" style="background:var(--accent-bg);color:var(--accent-fg);border:1px solid var(--accent-border);height:26px;">{t}</span>' for t in ["Vendor = Acme Analytics","Status is not Archived"])}</div>
          <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:18px;">
            The filter runs on the server for every request. A recipient cannot widen it by editing a
            request, and a row that stops matching disappears on their next read.</div></div>
        <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
          <span class="th">Recipients</span>
          {"".join(f'''<div style="display:flex;align-items:center;gap:8px;font-size:var(--text-sm);">
            {avatar(i,h)}<span style="flex:1;">{n}</span>{chip(s,k)}</div>'''
            for i,h,n,s,k in [("VC",95,"supplier@vendorco.com","Active","success"),("BD",180,"ops@beacondata.io","Expires 4d","warning")])}
          <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
            No OpsHub account. Every edit is attributed to the token and appears in the audit log.</div></div>
      </div>
    </div>
    <aside style="width:340px;flex:none;border-left:1px solid var(--border-subtle);background:var(--bg-surface);
      padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
      <span class="th">Recipient preview</span>
      <div style="border:1px solid var(--border-default);border-radius:var(--radius-md);overflow:hidden;">
        <div style="padding:var(--space-3);background:var(--bg-sunken);border-bottom:1px solid var(--border-subtle);
          font-size:var(--text-sm);font-weight:600;">Acme Analytics</div>
        <div style="padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-3);">
          {"".join(f'''<div style="display:flex;flex-direction:column;gap:5px;"><span class="th">{l}</span>
            <div style="height:var(--control-md);border:1px solid var(--border-{b});border-radius:var(--radius-md);
              display:flex;align-items:center;padding:0 var(--space-3);font-size:var(--text-sm);
              background:var(--bg-{bg});color:var(--text-{c});">{v}</div></div>'''
            for l,v,b,bg,c in [("Vendor name","Acme Analytics","subtle","sunken","secondary"),
                               ("Review status","In review","default","surface","primary"),
                               ("Evidence","questionnaire-v4.pdf","default","surface","primary")])}
          <button class="btn btn-primary" style="justify-content:center;">Save</button>
        </div></div>
      <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--accent-bg);
        border:1px solid var(--accent-border);font-size:var(--text-xs);color:var(--accent-fg);line-height:17px;">
        Three fields of eighteen, one row of 1,284. The recipient can never see the shape of what they
        are not shown.</div>
    </aside>
  </div>''', crumb="Northfield Delivery / Vendors")
write('DynamicView.dc.html', page(dv, theme="dark"))
print("Pivot + DynamicView written")
