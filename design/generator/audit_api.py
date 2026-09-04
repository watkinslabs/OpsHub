from _common import icon, chip, avatar, page, write
from _shell import topbar, rail, toolbar, tabs
from board_timeline import shell, BTN
from entra_billing import adminshell, field, toggle

# ---------------- Audit log ----------------
AUD=[("14:02:11","share.granted","Priya Raman","PR",30,"Sheet · Cutover plan","group Delivery → editor","success"),
     ("13:58:40","cell.updated","Ana Duarte","AD",210,"Row · ROW-2471","Status: In progress → Review","accent"),
     ("13:41:02","publication.viewed","anonymous","–",0,"Dashboard · Delivery overview","token 8fJ2q… · 51.x.x.x","accent"),
     ("13:22:57","entra.signin","Marcus Webb","MW",120,"Session","Entra OIDC · oid 9f2a…","success"),
     ("12:04:19","entitlement.updated","Priya Raman","PR",30,"Module · workapps","none → trial (14d)","warning"),
     ("11:20:33","share-link.revoked","Priya Raman","PR",30,"View · Q3 plan","3 links revoked","danger"),
     ("09:11:08","export.completed","Sam Okafor","SO",70,"Sheet · Vendor register","xlsx · 1,284 rows","accent")]
rows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-2) var(--space-5);
  border-bottom:1px solid var(--border-subtle);gap:var(--space-3);font-size:var(--text-sm);">
  <span class="mono" style="width:76px;flex:none;color:var(--text-tertiary);font-size:11px;">{t}</span>
  <span style="width:170px;flex:none;">{chip(a,k)}</span>
  <span style="width:170px;flex:none;display:flex;align-items:center;gap:8px;color:var(--text-secondary);">
    {avatar(i,h) if i!="–" else '<span style="width:24px;height:24px;border-radius:99px;border:1px dashed var(--border-strong);display:inline-block;"></span>'}{n}</span>
  <span style="width:230px;flex:none;color:var(--text-secondary);">{tgt}</span>
  <span style="flex:1;color:var(--text-tertiary);font-size:var(--text-xs);">{d}</span>
  <span style="color:var(--text-tertiary);">{icon("chev",15)}</span>
</div>''' for t,a,n,i,h,tgt,d,k in AUD)

audit = adminshell("Audit log", chip("append-only","success"),
  ["Events","Access reviews","Retention","Legal holds"],"Events",
  BTN("Range: today","ghost","calendar")+BTN("Filter","ghost","filter")+BTN("Export","secondary","doc"),
  f'''<div style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
    <div style="padding:var(--space-3) var(--space-5);display:flex;gap:8px;align-items:center;">
      <div style="display:flex;align-items:center;gap:8px;height:var(--control-md);flex:1;max-width:360px;
        padding:0 var(--space-3);border:1px solid var(--border-default);border-radius:var(--radius-md);
        color:var(--text-tertiary);">{icon("search",16)}<span style="font-size:var(--text-sm);">actor, action, resource or correlation_id</span></div>
      {chip("7 of 41,208","accent")}
      <span style="margin-left:auto;font-size:var(--text-xs);color:var(--text-tertiary);">
        retained 7 years · partitioned monthly · immutable</span></div>
    <div style="display:flex;padding:var(--space-2) var(--space-5);background:var(--bg-sunken);
      border-top:1px solid var(--border-default);border-bottom:1px solid var(--border-default);gap:var(--space-3);">
      {"".join(f'<span class="th" style="width:{w}px;flex:none;">{n}</span>' for n,w in [("Time",76),("Action",170),("Actor",170),("Target",230)])}
      <span class="th" style="flex:1;">Detail</span><span style="width:15px;"></span></div>
    {rows}
    <div style="padding:var(--space-4) var(--space-5);display:flex;align-items:center;gap:var(--space-3);
      border-top:1px solid var(--border-subtle);">
      <span class="mono" style="font-size:var(--text-xs);color:var(--text-tertiary);">
        correlation_id links an API call to its jobs, events and cell writes</span>
      <div style="margin-left:auto;display:flex;gap:6px;">
        <button class="btn btn-secondary" style="height:var(--control-sm);">Previous</button>
        <button class="btn btn-secondary" style="height:var(--control-sm);">Next</button></div></div>
  </div>''')
write('Audit.dc.html', page(audit, theme="light"))

# ---------------- API & webhooks ----------------
HOOKS=[("Delivery status feed","https://hooks.northfield.co/opshub","row.updated.v1, row.created.v1","Healthy","success","99.8%","142ms"),
       ("Vendor sync","https://vendors.internal/ingest","vendor.approved.v1","Failing","danger","41.2%","timeout"),
       ("Slack relay","https://hooks.slack.com/services/…","comment.created.v1, mention.created.v1","Healthy","success","100%","88ms")]
hrows="".join(f'''<div style="display:flex;align-items:center;padding:var(--space-3) 0;
  border-bottom:1px solid var(--border-subtle);gap:var(--space-3);">
  <div style="width:200px;flex:none;"><div style="font-size:var(--text-sm);font-weight:600;">{n}</div>
    <div class="mono" style="font-size:11px;color:var(--text-tertiary);margin-top:2px;overflow:hidden;
      text-overflow:ellipsis;white-space:nowrap;">{u}</div></div>
  <div style="flex:1;display:flex;gap:5px;flex-wrap:wrap;">
    {"".join(f'<span class="chip" style="background:var(--bg-sunken);color:var(--text-secondary);border:1px solid var(--border-subtle);">{e.strip()}</span>' for e in ev.split(","))}</div>
  <div style="width:110px;flex:none;">{chip(s,k)}</div>
  <div class="mono" style="width:80px;flex:none;text-align:right;font-size:var(--text-sm);">{d}</div>
  <div class="mono" style="width:90px;flex:none;text-align:right;font-size:var(--text-sm);
    color:var(--{"danger" if l=="timeout" else "text"}-{"fg" if l=="timeout" else "secondary"});">{l}</div>
</div>''' for n,u,ev,s,k,d,l in HOOKS)

api = adminshell("API & webhooks", chip("3 applications","accent"),
  ["Applications","Webhooks","Reference","Rate limits"],"Webhooks",
  BTN("Delivery log","ghost","doc")+BTN("Replay failed","secondary","clock")+BTN("New webhook","primary","plus"),
  f'''<div style="flex:1;padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-5);overflow:hidden;">
    <div style="display:flex;flex-direction:column;gap:var(--space-2);">
      <div style="display:flex;padding-bottom:6px;border-bottom:1px solid var(--border-default);gap:var(--space-3);">
        <span class="th" style="width:200px;flex:none;">Endpoint</span>
        <span class="th" style="flex:1;">Events</span>
        <span class="th" style="width:110px;flex:none;">Status</span>
        <span class="th" style="width:80px;flex:none;text-align:right;">Success</span>
        <span class="th" style="width:90px;flex:none;text-align:right;">p95</span></div>
      {hrows}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);">
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span class="th">Signature verification</span>
        <div class="mono" style="padding:var(--space-3);background:var(--bg-sunken);border-radius:var(--radius-md);
          font-size:11px;line-height:18px;color:var(--text-secondary);border:1px solid var(--border-subtle);">
          X-OpsHub-Signature: t=1772…,v1=5d41…<br>
          X-OpsHub-Event: row.updated.v1<br>
          X-OpsHub-Delivery: 018f2c…<br>
          X-OpsHub-Attempt: 1</div>
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);line-height:17px;">
          HMAC-SHA256 over <span class="mono">t.body</span>, 300s skew, two-secret rotation. Retries
          1/2/4/8/16 min, then dead-letter with replay.</div></div>
      <div class="card" style="padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3);">
        <span class="th">Failing endpoint · Vendor sync</span>
        <div style="padding:var(--space-3);border-radius:var(--radius-md);background:var(--danger-bg);
          border:1px solid var(--danger-border);">
          <div style="display:flex;align-items:center;gap:8px;color:var(--danger-fg);">{icon("warn",16)}
            <span style="font-size:var(--text-sm);font-weight:600;">128 deliveries dead-lettered</span></div>
          <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:6px;line-height:17px;">
            Connection timeout after 10s on every attempt since 09:14. Endpoint auto-paused after 3
            consecutive failures; nothing was dropped.</div>
          <div style="display:flex;gap:6px;margin-top:var(--space-3);">
            <button class="btn btn-secondary" style="height:var(--control-sm);font-size:var(--text-xs);">Test endpoint</button>
            <button class="btn btn-primary" style="height:var(--control-sm);font-size:var(--text-xs);">Replay 128</button></div>
        </div></div>
    </div>
  </div>''')
write('Api.dc.html', page(api, theme="dark"))
print("Audit + Api written")
