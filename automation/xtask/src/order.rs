//! The build order, derived from the backlog rather than maintained beside it: a feature is
//! schedulable once every dependency is done and its own milestone has been reached. Four renderers
//! print the same waves — a table, Mermaid, Graphviz and a self-contained page — and `check_order`
//! holds the committed copies to what the tickets currently say.
use std::{collections::{HashMap, HashSet}, fs};
use crate::support::{front_value, ticket_files};

/// The build order is derived, never hand-maintained: a feature is schedulable once every
/// dependency is done and its own milestone has been reached. Printing it and checking the
/// committed copy against it keeps `docs/build-order.md` from drifting the moment a dependency moves.
fn compute_waves() -> Result<(Vec<(usize, Vec<String>)>, HashMap<String, (String, String, u32, Vec<String>)>), String> {
    let mut meta: HashMap<String, (String, String, u32, Vec<String>)> = HashMap::new();
    for path in ticket_files() {
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        let Some(id) = front_value(&text, "id:") else { continue; };
        let title = text.lines().find_map(|l| l.strip_prefix(&format!("# {id} — "))).unwrap_or("").to_owned();
        let milestone = front_value(&text, "target_milestone:").unwrap_or_default();
        let estimate = front_value(&text, "estimate:").and_then(|e| e.parse().ok()).unwrap_or(0);
        let deps = crate::support::list_field(&text, "depends_on:");
        meta.insert(id, (title, milestone, estimate, deps));
    }
    let mut wave: HashMap<String, usize> = HashMap::new();
    for _ in 0..meta.len() {
        for (id, (_, milestone, _, deps)) in &meta {
            let known = deps.iter().filter(|d| meta.contains_key(*d)).collect::<Vec<_>>();
            if known.iter().any(|d| !wave.contains_key(*d)) { continue; }
            let after = known.iter().filter_map(|d| wave.get(*d)).map(|w| w + 1).max().unwrap_or(0);
            let floor = milestone.trim_start_matches('M').parse::<usize>().unwrap_or(0);
            wave.insert(id.clone(), after.max(floor));
        }
    }
    if wave.len() != meta.len() { return Err("build order: a dependency cycle leaves features unplaceable".into()); }
    let mut grouped: HashMap<usize, Vec<String>> = HashMap::new();
    for (id, w) in &wave { grouped.entry(*w).or_default().push(id.clone()); }
    let mut waves = grouped.into_iter().map(|(w, mut ids)| { ids.sort(); (w, ids) }).collect::<Vec<_>>();
    waves.sort_by_key(|(w, _)| *w);
    Ok((waves, meta))
}

fn order_table() -> Result<String, String> {
    let (waves, meta) = compute_waves()?;
    let mut out = String::from("| Wave | Features | Points | Ready when |\n|---|---|---|---|\n");
    for (w, ids) in &waves {
        let points: u32 = ids.iter().map(|i| meta[i].2).sum();
        let listed = ids.iter().map(|i| format!("`{i}`")).collect::<Vec<_>>().join(" ");
        out.push_str(&format!("| {w} | {listed} | {points} | every dependency archived |\n"));
    }
    out.push_str("\n| Feature | Wave | Milestone | Points | Depends on | Title |\n|---|---|---|---|---|---|\n");
    let mut rows = meta.keys().cloned().collect::<Vec<_>>();
    let wave_of = |id: &str| waves.iter().find(|(_, ids)| ids.iter().any(|i| i == id)).map(|(w, _)| *w).unwrap_or(0);
    rows.sort_by_key(|id| (wave_of(id), id.clone()));
    for id in rows {
        let (title, milestone, estimate, deps) = &meta[&id];
        let deps = if deps.is_empty() { "—".to_owned() } else { deps.join(", ") };
        out.push_str(&format!("| {id} | {} | {milestone} | {estimate} | {deps} | {title} |\n", wave_of(&id)));
    }
    Ok(out)
}

pub(crate) fn build_order(format: Option<&str>) -> Result<(), String> {
    let rendered = match format {
        None | Some("--markdown") => order_table()?,
        Some("--mermaid") => order_mermaid()?,
        Some("--dot") => order_dot()?,
        Some("--html") => order_html()?,
        Some(other) => return Err(format!("unknown format {other}; use --markdown, --mermaid, --dot or --html")),
    };
    print!("{rendered}");
    Ok(())
}

pub(crate) fn check_order() -> Result<(), String> {
    let expected = order_table()?;
    let doc = fs::read_to_string("docs/build-order.md")
        .map_err(|e| format!("missing docs/build-order.md: {e}"))?;
    let missing = expected.lines().filter(|l| l.starts_with("| F") && !doc.contains(l.trim())).count();
    if missing > 0 {
        eprintln!("BLOCKED: order.stale docs/build-order.md: {missing} row(s) do not match the derived order");
        eprintln!("         regenerate with `cargo xtask build-order`");
        return Err(format!("build-order audit failed: {missing} finding(s)"));
    }
    // order.html is committed so it can be opened without a toolchain, which means it can go stale
    // the same way the markdown can. Same rule, same command.
    let chart = fs::read_to_string("order.html").map_err(|e| format!("missing order.html: {e}"))?;
    if chart.trim_end() != order_html()?.trim_end() {
        eprintln!("BLOCKED: order.stale order.html: the committed chart does not match the derived order");
        eprintln!("         regenerate with `cargo xtask build-order --html > order.html`");
        return Err("build-order audit failed: 1 finding(s)".into());
    }
    let placed = expected.lines().filter(|l| l.starts_with("| F") && !l.starts_with("| Feature")).count();
    println!("build order checks passed: {placed} features placed, doc and chart match");
    Ok(())
}

/// Mermaid renders inline on GitHub, so the graph is readable where the order is read.
fn order_mermaid() -> Result<String, String> {
    let (waves, meta) = compute_waves()?;
    let mut out = String::from("flowchart LR\n");
    for (w, ids) in &waves {
        out.push_str(&format!("  subgraph W{w}[\"wave {w}\"]\n    direction TB\n"));
        for id in ids { out.push_str(&format!("    {id}[\"{id}<br/>{}\"]\n", meta[id].0)); }
        out.push_str("  end\n");
    }
    // Sorted, so a regenerated graph diffs cleanly against the last one.
    let mut ids = meta.keys().cloned().collect::<Vec<_>>();
    ids.sort();
    for id in &ids {
        for dep in meta[id].3.iter().filter(|d| meta.contains_key(*d)) { out.push_str(&format!("  {dep} --> {id}\n")); }
    }
    Ok(out)
}

/// Graphviz for anyone who wants to lay it out properly.
fn order_dot() -> Result<String, String> {
    let (waves, meta) = compute_waves()?;
    let mut out = String::from("digraph opshub {\n  rankdir=LR;\n  node [shape=box style=rounded fontname=\"Helvetica\"];\n");
    for (w, ids) in &waves {
        out.push_str(&format!("  subgraph cluster_{w} {{\n    label=\"wave {w}\";\n"));
        for id in ids { out.push_str(&format!("    {id} [label=\"{id}\\n{}\"];\n", meta[id].0)); }
        out.push_str("  }\n");
    }
    // Sorted, so a regenerated graph diffs cleanly against the last one.
    let mut ids = meta.keys().cloned().collect::<Vec<_>>();
    ids.sort();
    for id in &ids {
        for dep in meta[id].3.iter().filter(|d| meta.contains_key(*d)) { out.push_str(&format!("  {dep} -> {id};\n")); }
    }
    out.push_str("}\n");
    Ok(out)
}

/// A self-contained page: no CDN, no build step, opens from the filesystem. Waves are columns and a
/// feature sits at the row of its index, so an edge that spans many columns is a long pole by eye.
fn order_html() -> Result<String, String> {
    let (waves, meta) = compute_waves()?;
    let (col, row_h, box_w, box_h, pad, head) = (300usize, 46usize, 210usize, 34usize, 40usize, 54usize);
    let mut at: HashMap<String, (usize, usize)> = HashMap::new();
    for (w, ids) in &waves {
        for (index, id) in ids.iter().enumerate() {
            at.insert(id.clone(), (pad + w * col, pad + head + index * row_h));
        }
    }
    let tallest = waves.iter().map(|(_, i)| i.len()).max().unwrap_or(1);
    let height = pad * 2 + head + tallest * row_h;
    let width = pad * 2 + waves.len() * col;

    // Reverse edges, so a node can say what it unblocks and not only what it waits for.
    // `meta` is a HashMap, so anything derived by iterating it is in a different order every run.
    // This file is committed and gate-checked, so every loop below walks the sorted id list instead.
    let ids_sorted = { let mut v = meta.keys().cloned().collect::<Vec<_>>(); v.sort(); v };
    let mut blocks: HashMap<&str, Vec<&str>> = HashMap::new();
    for id in &ids_sorted {
        for dep in meta[id].3.iter().filter(|d| meta.contains_key(*d)) {
            blocks.entry(dep.as_str()).or_default().push(id.as_str());
        }
    }

    // The long pole: the heaviest chain of dependencies by estimate. Shortening any feature off
    // this path buys nothing; this is the sequence that sets the floor on how long the build takes.
    let order = waves.iter().flat_map(|(_, ids)| ids.iter()).collect::<Vec<_>>();
    let (mut cost, mut prev): (HashMap<&str, u32>, HashMap<&str, &str>) = (HashMap::new(), HashMap::new());
    for id in &order {
        let (_, _, points, deps) = &meta[*id];
        let best = deps.iter().filter(|d| meta.contains_key(*d))
            .filter_map(|d| cost.get(d.as_str()).map(|c| (*c, d.as_str())))
            .max_by_key(|(c, d)| (*c, std::cmp::Reverse(*d)));
        if let Some((c, from)) = best { cost.insert(id, c + points); prev.insert(id, from); }
        else { cost.insert(id, *points); }
    }
    let mut tip = ids_sorted.iter().map(|s| s.as_str())
        .max_by_key(|id| (cost.get(id).copied().unwrap_or(0), std::cmp::Reverse(*id)))
        .unwrap_or("");
    let critical_points = cost.get(tip).copied().unwrap_or(0);
    let mut critical: Vec<&str> = Vec::new();
    while !tip.is_empty() { critical.push(tip); match prev.get(tip) { Some(p) => tip = p, None => break } }
    critical.reverse();
    let on_path: HashSet<&str> = critical.iter().copied().collect();

    // Milestone is the one attribute a reader scans for, so it is the colour rather than a label.
    const HUES: [(&str, &str, &str); 9] = [
        ("M0", "#eceef1", "#5b636f"), ("M1", "#e8effb", "#3b6fd4"), ("M2", "#e6f4ee", "#2f8f66"),
        ("M3", "#fdf0e0", "#b3701a"), ("M4", "#fbe9f1", "#b34a7d"), ("M5", "#eeeafb", "#6a52c9"),
        ("M6", "#e3f3f5", "#1d7f8c"), ("M7", "#f6ecdf", "#8a6224"), ("M8", "#f0e9f5", "#7a4a92"),
    ];
    let hue = |m: &str| HUES.iter().find(|(name, _, _)| *name == m).map(|(_, bg, fg)| (*bg, *fg)).unwrap_or(("#ffffff", "#5b636f"));

    let mut edges = String::new();
    for id in &ids_sorted {
        let Some(&(x2, y2)) = at.get(id) else { continue };
        for dep in meta[id].3.iter().filter(|d| meta.contains_key(*d)) {
            let Some(&(x1, y1)) = at.get(dep) else { continue };
            let (sx, sy) = (x1 + box_w, y1 + box_h / 2);
            let (ex, ey) = (x2, y2 + box_h / 2);
            let mid = (sx + ex) / 2;
            let hot = on_path.contains(id.as_str()) && on_path.contains(dep.as_str());
            let (stroke, w) = if hot { ("#d4453b", "2") } else { ("#c2c9d2", "1.2") };
            edges.push_str(&format!(
                "<path class=\"e\" data-a=\"{dep}\" data-b=\"{id}\" d=\"M{sx},{sy} C{mid},{sy} {mid},{ey} {ex},{ey}\" \
                 fill=\"none\" stroke=\"{stroke}\" stroke-width=\"{w}\"><title>{dep} blocks {id}</title></path>"));
        }
    }

    let mut nodes = String::new();
    for (w, ids) in &waves {
        let x = pad + w * col;
        let points: u32 = ids.iter().map(|id| meta[id].2).sum();
        nodes.push_str(&format!(
            "<text x=\"{x}\" y=\"{}\" font-size=\"12\" font-weight=\"700\" fill=\"#14171c\" font-family=\"system-ui\">WAVE {w}</text>\
             <text x=\"{x}\" y=\"{}\" font-size=\"10\" fill=\"#8c94a1\" font-family=\"system-ui\">{} features · {points} pts</text>",
            pad + 22, pad + 38, ids.len()));
        for id in ids {
            let (nx, ny) = at[id];
            let (title, milestone, points, deps) = &meta[id];
            let (bg, fg) = hue(milestone);
            let short: String = if title.chars().count() > 32 { title.chars().take(31).chain("…".chars()).collect() } else { title.clone() };
            let blocked = blocks.get(id.as_str()).map(|v| v.len()).unwrap_or(0);
            let ring = if on_path.contains(id.as_str()) { "#d4453b" } else { "#dee2e8" };
            let sw = if on_path.contains(id.as_str()) { "2" } else { "1" };
            nodes.push_str(&format!(
                "<g class=\"n\" data-id=\"{id}\"><title>{id} — {title}\n{milestone} · {points} pts · waits on {} · unblocks {blocked}</title>\
                 <rect x=\"{nx}\" y=\"{ny}\" width=\"{box_w}\" height=\"{box_h}\" rx=\"6\" fill=\"{bg}\" stroke=\"{ring}\" stroke-width=\"{sw}\"/>\
                 <text x=\"{}\" y=\"{}\" font-size=\"11\" font-weight=\"700\" fill=\"#14171c\" font-family=\"ui-monospace,monospace\">{id}</text>\
                 <text x=\"{}\" y=\"{}\" font-size=\"9\" font-weight=\"700\" fill=\"{fg}\" font-family=\"ui-monospace,monospace\" text-anchor=\"end\">{milestone} · {points} pts</text>\
                 <text x=\"{}\" y=\"{}\" font-size=\"10\" fill=\"#5b636f\" font-family=\"system-ui\">{short}</text></g>",
                deps.iter().filter(|d| meta.contains_key(*d)).count(),
                nx + 8, ny + 14, nx + box_w - 8, ny + 14, nx + 8, ny + 27));
        }
    }

    let mut legend = String::new();
    for (m, bg, fg) in HUES {
        let n = meta.values().filter(|(_, mi, _, _)| mi == m).count();
        if n == 0 { continue }
        let pts: u32 = meta.values().filter(|(_, mi, _, _)| mi == m).map(|(_, _, p, _)| p).sum();
        legend.push_str(&format!(
            "<span class=\"chip\" style=\"background:{bg};color:{fg}\">{m} · {n} features · {pts} pts</span>"));
    }

    let mut rows = String::new();
    for (w, ids) in &waves {
        for id in ids {
            let (title, milestone, points, deps) = &meta[id];
            let waits = deps.iter().filter(|d| meta.contains_key(*d)).cloned().collect::<Vec<_>>().join(", ");
            let unblocks = blocks.get(id.as_str()).map(|v| v.join(", ")).unwrap_or_default();
            let (bg, fg) = hue(milestone);
            let mark = if on_path.contains(id.as_str()) { " ●" } else { "" };
            rows.push_str(&format!(
                "<tr><td class=\"m\">{w}</td><td class=\"m b\">{id}{mark}</td><td>{title}</td>\
                 <td><span class=\"chip\" style=\"background:{bg};color:{fg}\">{milestone}</span></td>\
                 <td class=\"m r\">{points}</td><td class=\"m d\">{}</td><td class=\"m d\">{}</td></tr>",
                if waits.is_empty() { "—".into() } else { waits },
                if unblocks.is_empty() { "—".into() } else { unblocks }));
        }
    }

    let total_points: u32 = meta.values().map(|(_, _, p, _)| p).sum();
    let edge_count = meta.values().map(|(_, _, _, d)| d.iter().filter(|x| meta.contains_key(*x)).count()).sum::<usize>();
    let path_text = critical.join(" → ");

    Ok(format!("<!doctype html><meta charset=\"utf-8\"><title>OpsHub build order</title>\
<style>\
body{{margin:0;background:#f6f7f9;font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#14171c}}\
.wrap{{padding:24px 40px}}h1{{margin:0;font-size:20px}}\
p.lede{{margin:6px 0 0;font-size:13px;color:#5b636f;max-width:78ch;line-height:1.5}}\
.chips{{margin:16px 0 0;display:flex;flex-wrap:wrap;gap:6px}}\
.chip{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;font-family:ui-monospace,monospace}}\
.stats{{margin:14px 0 0;display:flex;flex-wrap:wrap;gap:24px;font-size:13px}}\
.stats b{{display:block;font-size:22px;font-weight:700;line-height:1.2}}\
.stats span{{color:#5b636f;font-size:11px;text-transform:uppercase;letter-spacing:.04em}}\
.pole{{margin:16px 40px 0;padding:12px 16px;background:#fff5f4;border:1px solid #f2cfcb;border-radius:8px;font-size:12px;line-height:1.6}}\
.pole b{{color:#d4453b}}.pole code{{font-family:ui-monospace,monospace;font-size:11px;color:#14171c}}\
.scroll{{margin:16px 0 0;overflow-x:auto;background:#fff;border-top:1px solid #e5e8ec;border-bottom:1px solid #e5e8ec}}\
svg .n{{cursor:default}}svg.dim .e{{opacity:.12}}svg.dim .e.on{{opacity:1}}svg.dim .n{{opacity:.3}}svg.dim .n.on{{opacity:1}}\
table{{border-collapse:collapse;width:100%;font-size:12px;background:#fff}}\
th{{position:sticky;top:0;background:#eef0f3;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#5b636f;border-bottom:1px solid #dee2e8}}\
td{{padding:7px 10px;border-bottom:1px solid #eef0f3;vertical-align:top}}\
tr:hover td{{background:#f8f9fb}}.m{{font-family:ui-monospace,monospace}}.b{{font-weight:700}}.r{{text-align:right}}\
.d{{color:#5b636f;font-size:11px;max-width:26ch}}\
</style>\
<body><div class=\"wrap\"><h1>OpsHub build order</h1>\
<p class=\"lede\">Derived from every ticket's <code>depends_on</code> and <code>target_milestone</code> by \
<code>cargo xtask build-order --html</code> — not maintained by hand, so it cannot drift from the backlog. \
A feature is schedulable when every dependency to its left is finished and its milestone has been reached. \
Everything in one wave can be built at the same time. Hover a box to isolate what it waits on and what it unblocks; \
red marks the long pole.</p>\
<div class=\"stats\">\
<div><b>{}</b><span>features</span></div><div><b>{}</b><span>waves</span></div>\
<div><b>{total_points}</b><span>points</span></div><div><b>{edge_count}</b><span>dependency edges</span></div>\
<div><b>{critical_points}</b><span>points on the long pole</span></div></div>\
<div class=\"chips\">{legend}</div></div>\
<div class=\"pole\"><b>Long pole ({} features, {critical_points} of {total_points} points).</b> \
This is the heaviest chain of dependencies in the backlog: no amount of parallelism finishes the product faster than \
building these in sequence, and shortening anything off this path buys nothing.<br><code>{path_text}</code></div>\
<div class=\"scroll\"><svg id=\"g\" width=\"{width}\" height=\"{height}\" xmlns=\"http://www.w3.org/2000/svg\">{edges}{nodes}</svg></div>\
<table><thead><tr><th>Wave</th><th>ID</th><th>Feature</th><th>Milestone</th><th>Pts</th><th>Waits on</th><th>Unblocks</th></tr></thead>\
<tbody>{rows}</tbody></table>\
<script>\
var g=document.getElementById('g');\
g.addEventListener('mouseover',function(e){{var n=e.target.closest('.n');if(!n)return;var id=n.dataset.id;var keep={{}};keep[id]=1;\
g.querySelectorAll('.e').forEach(function(p){{var on=p.dataset.a===id||p.dataset.b===id;p.classList.toggle('on',on);if(on){{keep[p.dataset.a]=1;keep[p.dataset.b]=1}}}});\
g.querySelectorAll('.n').forEach(function(m){{m.classList.toggle('on',!!keep[m.dataset.id])}});g.classList.add('dim')}});\
g.addEventListener('mouseleave',function(){{g.classList.remove('dim')}});\
</script></body>",
        meta.len(), waves.len(), critical.len()))
}
