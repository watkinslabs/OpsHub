import math
SER = ["var(--brand)","#0e9aa7","#e0930f","#d6558f","#5aa06b"]

def line(w,h,pts,color="var(--brand)",fill=True,sw=2):
    n=len(pts); mx=max(pts); mn=min(pts); rng=(mx-mn) or 1
    xs=[i*(w/(n-1)) for i in range(n)]
    ys=[h-8-((v-mn)/rng)*(h-20) for v in pts]
    d=" ".join(f"{'M' if i==0 else 'L'}{xs[i]:.1f},{ys[i]:.1f}" for i in range(n))
    area=f'<path d="{d} L{w},{h} L0,{h} Z" fill="{color}" opacity=".10"/>' if fill else ""
    dot=f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3.5" fill="{color}"/>'
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">{area}<path d="{d}" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>{dot}</svg>'

def bars(w,h,vals,color="var(--brand)",gap=8,labels=None):
    n=len(vals); mx=max(vals) or 1; bw=(w-gap*(n-1))/n
    out=[]
    for i,v in enumerate(vals):
        bh=max(2,(v/mx)*(h-18)); x=i*(bw+gap); y=h-18-bh
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{color}"/>')
        if labels: out.append(f'<text x="{x+bw/2:.1f}" y="{h-4}" text-anchor="middle" font-size="10" fill="var(--text-tertiary)" font-family="JetBrains Mono, monospace">{labels[i]}</text>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}</svg>'

def stacked(w,h,groups,colors=SER,gap=10,labels=None):
    n=len(groups); mx=max(sum(g) for g in groups) or 1; bw=(w-gap*(n-1))/n
    out=[]
    for i,g in enumerate(groups):
        y=h-18; x=i*(bw+gap)
        for j,v in enumerate(g):
            bh=(v/mx)*(h-24); y-=bh
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{colors[j%len(colors)]}" rx="2"/>')
        if labels: out.append(f'<text x="{x+bw/2:.1f}" y="{h-4}" text-anchor="middle" font-size="10" fill="var(--text-tertiary)" font-family="JetBrains Mono, monospace">{labels[i]}</text>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}</svg>'

def donut(size,vals,colors=SER,thick=16,center=""):
    r=(size-thick)/2; c=size/2; circ=2*math.pi*r; tot=sum(vals) or 1; off=0; out=[]
    for i,v in enumerate(vals):
        seg=circ*v/tot
        out.append(f'<circle cx="{c}" cy="{c}" r="{r:.1f}" fill="none" stroke="{colors[i%len(colors)]}" stroke-width="{thick}" stroke-dasharray="{seg-2:.1f} {circ-seg+2:.1f}" stroke-dashoffset="{-off:.1f}" transform="rotate(-90 {c} {c})" stroke-linecap="butt"/>')
        off+=seg
    txt=f'<text x="{c}" y="{c+2}" text-anchor="middle" dominant-baseline="middle" font-size="22" font-weight="700" fill="var(--text-primary)" font-family="Plus Jakarta Sans, sans-serif">{center}</text>' if center else ""
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(out)}{txt}</svg>'

def spark(w,h,pts,color="var(--brand)"):
    return line(w,h,pts,color,fill=False,sw=1.6)

def gauge(size,pct,color="var(--brand)"):
    r=(size-14)/2; c=size/2; circ=math.pi*r
    return (f'<svg width="{size}" height="{size/2+10}" viewBox="0 0 {size} {size/2+10}">'
      f'<path d="M7,{c} A{r},{r} 0 0 1 {size-7},{c}" fill="none" stroke="var(--bg-sunken)" stroke-width="12" stroke-linecap="round"/>'
      f'<path d="M7,{c} A{r},{r} 0 0 1 {size-7},{c}" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{circ*pct/100:.1f} {circ:.1f}"/>'
      f'<text x="{c}" y="{c-4}" text-anchor="middle" font-size="20" font-weight="700" fill="var(--text-primary)" font-family="Plus Jakarta Sans, sans-serif">{pct}%</text></svg>')
