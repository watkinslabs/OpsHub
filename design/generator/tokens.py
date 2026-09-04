from _common import icon, chip, avatar, page, write

def sw(name, css, hexish, dark=False):
    return f'''<div style="display:flex;flex-direction:column;gap:6px;">
      <div style="height:52px;border-radius:var(--radius-md);background:{css};
        border:1px solid var(--border-default);"></div>
      <div class="mono" style="font-size:11px;font-weight:500;">{name}</div>
      <div class="mono" style="font-size:10px;color:var(--text-tertiary);">{hexish}</div></div>'''

def sect(title, note, body):
    return f'''<section style="display:flex;flex-direction:column;gap:var(--space-4);">
      <div style="display:flex;align-items:baseline;gap:var(--space-3);">
        <h2 style="margin:0;font-size:var(--text-lg);font-weight:700;letter-spacing:-.01em;">{title}</h2>
        <span style="font-size:var(--text-xs);color:var(--text-tertiary);">{note}</span></div>
      {body}</section>'''

SURF=[("--bg-canvas","#f6f7f9","#0c0e12"),("--bg-surface","#ffffff","#14171d"),("--bg-raised","#ffffff","#1a1e25"),
      ("--bg-sunken","#eff1f4","#0f1216"),("--bg-hover","#f1f3f6","#1e232b"),("--bg-active","#e6e9ee","#262c35")]
TEXT=[("--text-primary","#14171c","#eef1f5"),("--text-secondary","#5b636f","#a2abb8"),
      ("--text-tertiary","#8c94a1","#6f7885"),("--border-subtle","#edeff2","#1e232b"),
      ("--border-default","#dee2e8","#2a313a"),("--border-strong","#c2c9d2","#3d4650")]
INTENT=["accent","success","warning","danger"]

pal_light = "".join(sw(n, l, l) for n,l,d in SURF+TEXT)
pal_dark = "".join(f'''<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="height:52px;border-radius:var(--radius-md);background:{d};border:1px solid #2a313a;"></div>
  <div class="mono" style="font-size:11px;font-weight:500;color:#eef1f5;">{n}</div>
  <div class="mono" style="font-size:10px;color:#6f7885;">{d}</div></div>''' for n,l,d in SURF+TEXT)

intents = "".join(f'''<div style="display:flex;flex-direction:column;gap:8px;">
  <div class="mono" style="font-size:11px;font-weight:600;">--{k}-*</div>
  <div style="display:flex;gap:6px;">
    {"".join(f'<div style="flex:1;height:40px;border-radius:var(--radius-sm);background:var(--{k}-{v});border:1px solid var(--border-subtle);"></div>' for v in ["bg","border","fg","emphasis"])}
  </div>
  <div style="display:flex;gap:6px;">
    {"".join(f'<div class="mono" style="flex:1;font-size:9px;color:var(--text-tertiary);text-align:center;">{v}</div>' for v in ["bg","border","fg","emph"])}
  </div>
  <div>{chip("Sample", k)}</div></div>''' for k in INTENT)

TYPE=[("3xl","30px / 38px","700","Programme overview"),("2xl","24px / 32px","700","Cutover plan"),
      ("xl","20px / 28px","600","Delivery workstreams"),("lg","16px / 24px","600","Vendor security review"),
      ("base","14px / 20px","400","Body copy sets the default reading size across the product."),
      ("sm","13px / 18px","400","Grid cells, table rows and dense data surfaces."),
      ("xs","12px / 16px","500","Labels, metadata and helper text.")]
typ = "".join(f'''<div style="display:flex;align-items:baseline;gap:var(--space-5);
  padding:var(--space-3) 0;border-bottom:1px solid var(--border-subtle);">
  <span class="mono" style="width:96px;flex:none;font-size:11px;color:var(--text-tertiary);">--text-{k}</span>
  <span class="mono" style="width:110px;flex:none;font-size:11px;color:var(--text-tertiary);">{v}</span>
  <span class="mono" style="width:44px;flex:none;font-size:11px;color:var(--text-tertiary);">{w}</span>
  <span style="font-size:var(--text-{k});font-weight:{w};line-height:1.25;letter-spacing:{'-.02em' if k in ('3xl','2xl','xl') else '0'};">{s}</span>
</div>''' for k,v,w,s in TYPE)

SPACE=[("1","4"),("2","8"),("3","12"),("4","16"),("5","20"),("6","24"),("7","32"),("8","40"),("9","48"),("10","64")]
space = "".join(f'''<div style="display:flex;align-items:center;gap:var(--space-3);">
  <span class="mono" style="width:72px;font-size:11px;color:var(--text-tertiary);">--space-{k}</span>
  <span style="height:14px;width:{v}px;background:var(--brand);border-radius:2px;opacity:.85;"></span>
  <span class="mono" style="font-size:11px;color:var(--text-tertiary);">{v}px</span></div>''' for k,v in SPACE)

RAD=[("sm","4"),("md","6"),("lg","10"),("full","9999")]
rad = "".join(f'''<div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
  <div style="width:64px;height:48px;background:var(--bg-sunken);border:1px solid var(--border-default);
    border-radius:{v if v!='9999' else '99'}px;"></div>
  <span class="mono" style="font-size:10px;color:var(--text-tertiary);">{k} · {v}</span></div>''' for k,v in RAD)

ELEV = "".join(f'''<div style="display:flex;flex-direction:column;align-items:center;gap:8px;">
  <div style="width:110px;height:64px;background:var(--bg-surface);border-radius:var(--radius-lg);
    border:1px solid var(--border-subtle);box-shadow:{s};"></div>
  <span class="mono" style="font-size:10px;color:var(--text-tertiary);">{n}</span></div>'''
  for n,s in [("elevation-0","none"),("elevation-1","var(--shadow-1)"),("elevation-2","var(--shadow-2)"),("elevation-3","var(--shadow-3)")])

DENS = "".join(f'''<div style="display:flex;flex-direction:column;gap:var(--space-2);flex:1;">
  <div class="mono" style="font-size:11px;font-weight:600;">{n}</div>
  {"".join(f'<div style="display:flex;align-items:center;gap:var(--space-2);"><span class="mono" style="width:118px;font-size:10px;color:var(--text-tertiary);">{lbl}</span><span style="height:{h}px;padding:0 12px;display:inline-flex;align-items:center;border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--bg-surface);font-size:var(--text-sm);">{h}px</span></div>' for lbl,h in rows)}
</div>''' for n,rows in [("comfortable (default)",[("--control-sm",28),("--control-md",32),("--control-lg",40),("--row-h",36)]),
                        ("compact",[("--control-sm",24),("--control-md",28),("--control-lg",34),("--row-h",28)])])

body = f'''
  <div style="padding:var(--space-7);display:flex;flex-direction:column;gap:var(--space-7);
    background:var(--bg-canvas);height:100%;overflow:hidden;">
    <div style="display:flex;align-items:flex-end;gap:var(--space-5);">
      <div style="flex:1;">
        <h1 style="margin:0;font-size:var(--text-3xl);font-weight:700;letter-spacing:-.025em;">Design tokens</h1>
        <p style="margin:8px 0 0;font-size:var(--text-sm);color:var(--text-secondary);max-width:720px;">
          Every value the product may use. Components reference these names only — never a literal. The brand hue
          drives all accent tokens through <span class="mono" style="font-size:12px;">color-mix</span>, so rebranding
          is one variable. Type is Plus Jakarta Sans; numerics are JetBrains Mono.</p>
      </div>
      <div style="display:flex;gap:var(--space-3);">
        {"".join(f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;"><span style="width:44px;height:44px;border-radius:var(--radius-md);background:{c};box-shadow:var(--shadow-1);"></span><span class="mono" style="font-size:9px;color:var(--text-tertiary);">{n}</span></div>' for n,c in [("indigo","#5b5bd6"),("teal","#0e7c86"),("amber","#b4530a"),("blue","#1f6feb")])}
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-6);">
      {sect("Surface & text — light","semantic names, one definition per theme",
        f'<div style="display:grid;grid-template-columns:repeat(6, minmax(0,1fr));gap:var(--space-3);">{pal_light}</div>')}
      {sect("Surface & text — dark","identical names, parity enforced by test",
        f'<div style="display:grid;grid-template-columns:repeat(6, minmax(0,1fr));gap:var(--space-3);padding:var(--space-4);background:#0c0e12;border-radius:var(--radius-lg);">{pal_dark}</div>')}
    </div>
    {sect("Intent families","each carries bg / border / fg / emphasis in both themes",
      f'<div style="display:grid;grid-template-columns:repeat(4, minmax(0,1fr));gap:var(--space-5);">{intents}</div>')}
    <div style="display:grid;grid-template-columns:1.4fr 1fr;gap:var(--space-6);">
      {sect("Type scale","Plus Jakarta Sans · 400 / 500 / 600 / 700", f'<div>{typ}</div>')}
      {sect("Spacing · 4px base", "radius · elevation",
        f'''<div style="display:flex;flex-direction:column;gap:var(--space-5);">
          <div style="display:flex;flex-direction:column;gap:8px;">{space}</div>
          <div style="display:flex;gap:var(--space-4);">{rad}</div>
          <div style="display:flex;gap:var(--space-4);">{ELEV}</div></div>''')}
    </div>
    {sect("Density","one token set, two modes — every control derives its height from these",
      f'<div style="display:flex;gap:var(--space-7);max-width:760px;">{DENS}</div>')}
  </div>'''
write('Tokens.dc.html', page(body, theme="light", size=(1440,1560)))
