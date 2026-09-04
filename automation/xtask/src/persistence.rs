//! Enforces architecture decision 2 and 2.1 over the backlog: normalized schema, and one data
//! access class per object type. It reads the specifications, so it holds before any code exists.
use std::{collections::{HashMap, HashSet}, fs};
use crate::support::{backtick_tokens, front_value, ticket_files};

/// `jsonb` is permitted only for genuinely schema-less payloads. A ticket keeping one must say so
/// with one of these words near it, which is what decision 2 asks an author to justify.
const PAYLOAD_WORDS: &[&str] = &["payload", "schema-less", "user-defined", "snapshot", "diff", "settings", "definition"];

/// True for a line that is actually DDL rather than prose mentioning a type.
fn is_ddl_line(line: &str) -> bool {
    ["uuid pk", "not null", "creates `", "primary key", "references ", "default '"]
        .iter().any(|marker| line.contains(marker))
}

fn array_columns(text: &str) -> Vec<String> {
    let mut found = Vec::new();
    for line in text.lines().filter(|l| is_ddl_line(l)) {
        for (index, _) in line.match_indices("[]") {
            let head = &line[..index];
            let Some(start) = head.rfind(|c: char| c == ',' || c == '(') else { continue; };
            let decl = head[start + 1..].trim();
            let parts = decl.split_whitespace().collect::<Vec<_>>();
            if parts.len() != 2 { continue; }
            let (name, kind) = (parts[0], parts[1]);
            if !["text", "uuid", "int", "jsonb", "bigint"].contains(&kind) { continue; }
            if name.len() < 3 || !name.chars().all(|c| c.is_ascii_lowercase() || c == '_') { continue; }
            found.push(format!("{name} {kind}[]"));
        }
    }
    found.sort();
    found.dedup();
    found
}

/// Catalog tables per feature id, read from the persistence column of both catalog tables.
fn catalog_tables() -> HashMap<String, Vec<String>> {
    let mut map = HashMap::new();
    let Ok(catalog) = fs::read_to_string("docs/capability-contracts.md") else { return map; };
    for line in catalog.lines().filter(|l| l.starts_with("| F")) {
        let cols = line.split('|').map(str::trim).collect::<Vec<_>>();
        if cols.len() < 8 { continue; }
        let tables = backtick_tokens(cols[6]).into_iter()
            .filter(|t| t.chars().all(|c| c.is_ascii_lowercase() || c == '_') && t.len() > 2)
            .collect::<Vec<_>>();
        if !tables.is_empty() { map.insert(cols[1].to_owned(), tables); }
    }
    map
}

pub(crate) fn check_persistence() -> Result<(), String> {
    let mut errors = Vec::new();
    let tables = catalog_tables();
    for path in ticket_files() {
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        let id = front_value(&text, "id:").unwrap_or_default();
        let label = path.display().to_string();

        // Decision 2: an enumerable set is a child table, never an array column.
        for column in array_columns(&text) {
            errors.push(format!("persist.array_column {label}: {id} declares `{column}`; decision 2 requires a child table"));
        }

        // Decision 2: a kept jsonb column must be justified as a payload rather than queried structure.
        if text.contains("jsonb") && !PAYLOAD_WORDS.iter().any(|w| text.contains(w)) {
            errors.push(format!("persist.jsonb_unjustified {label}: {id} keeps a jsonb column with no payload justification"));
        }

        // Decision 2.1: a feature owning tables names the data access class reaching them.
        if tables.contains_key(&id) && !text.contains("Repository") {
            errors.push(format!("persist.table_unmapped {label}: {id} owns tables but names no repository class"));
        }
    }
    if errors.is_empty() {
        println!("persistence checks passed: {} tickets, {} table-owning features", ticket_files().len(), tables.len());
        return Ok(());
    }
    for error in &errors { eprintln!("BLOCKED: {error}"); }
    Err(format!("persistence audit failed: {} finding(s)", errors.len()))
}

/// Every role a catalog row or ticket authorizes against must be defined in the authorization model.
/// Without this, 68 tickets each invent their own vocabulary and F003 has nothing to seed.
pub(crate) fn check_roles() -> Result<(), String> {
    let model = fs::read_to_string("docs/authorization-model.md")
        .map_err(|e| format!("missing docs/authorization-model.md: {e}"))?;
    let defined = |role: &str| model.contains(&format!("`{role}`"));
    let mut errors = Vec::new();

    let catalog = fs::read_to_string("docs/capability-contracts.md").map_err(|e| e.to_string())?;
    let mut seen = 0usize;
    for line in catalog.lines().filter(|l| l.starts_with("| F")) {
        let cols = line.split('|').map(str::trim).collect::<Vec<_>>();
        if cols.len() < 9 { continue; }
        for role in cols[7].split([',', ';']).map(|r| r.trim().trim_matches('`')).filter(|r| !r.is_empty()) {
            seen += 1;
            if !defined(role) {
                errors.push(format!("role.undefined {}: catalog row uses `{role}`, absent from the authorization model", cols[1]));
            }
        }
    }
    if errors.is_empty() {
        println!("role checks passed: {seen} catalog role references, all defined");
        return Ok(());
    }
    errors.sort();
    errors.dedup();
    for error in &errors { eprintln!("BLOCKED: {error}"); }
    Err(format!("role audit failed: {} finding(s)", errors.len()))
}

/// A ticket names the artboard that draws it, or states plainly that it has no user surface.
/// Without this a section 3 can reference a screen nobody drew, which is how a specification
/// quietly becomes unbuildable.
pub(crate) fn check_design() -> Result<(), String> {
    let dir = std::path::Path::new("design/artboards");
    let available = fs::read_dir(dir)
        .map_err(|e| format!("missing design/artboards: {e}"))?
        .flatten()
        .filter_map(|entry| entry.file_name().into_string().ok())
        .filter(|name| name.ends_with(".dc.html"))
        .collect::<Vec<_>>();
    let mut errors = Vec::new();
    let (mut drawn, mut headless) = (0usize, 0usize);
    for path in ticket_files() {
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        let label = path.display().to_string();
        let named = text.match_indices("design/artboards/").map(|(index, _)| {
            text[index + "design/artboards/".len()..]
                .split(|c: char| c == '`' || c == ',' || c == ' ' || c == ')')
                .next().unwrap_or("").to_owned()
        }).collect::<Vec<_>>();
        if named.is_empty() {
            if text.contains("no user surface") { headless += 1; continue; }
            errors.push(format!("design.unreferenced {label}: names no artboard and does not state that it has no user surface"));
            continue;
        }
        drawn += 1;
        for artboard in named {
            if !available.contains(&artboard) {
                errors.push(format!("design.missing {label}: references `{artboard}`, which is not in design/artboards"));
            }
        }
    }
    if errors.is_empty() {
        println!("design checks passed: {drawn} tickets reference an artboard, {headless} have no user surface, {} artboards available", available.len());
        return Ok(());
    }
    errors.sort();
    for error in &errors { eprintln!("BLOCKED: {error}"); }
    Err(format!("design audit failed: {} finding(s)", errors.len()))
}

/// Tickets cite each other's requirements and each other's files. Nothing verified that those
/// references resolve, so a renumbered requirement or a moved document leaves a dangling citation
/// that reads as authoritative. This checks every cross-reference in the backlog and the docs.
pub(crate) fn check_references() -> Result<(), String> {
    use std::collections::{HashMap, HashSet};
    let mut declared: HashMap<String, HashSet<String>> = HashMap::new();
    for path in crate::support::work_files() {
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        let Some(id) = front_value(&text, "id:") else { continue; };
        for prefix in ["FR-", "NFR-", "SR-"] {
            let key = format!("{prefix}{id}-");
            let owned = crate::support::tagged_ids(&text, &key);
            if !owned.is_empty() { declared.entry(key).or_default().extend(owned); }
        }
    }
    let mut errors = Vec::new();
    let mut checked = 0usize;
    let scan = crate::support::work_files().into_iter()
        .chain(std::path::Path::new("docs").read_dir().into_iter().flatten().flatten().map(|e| e.path()))
        .filter(|p| p.extension().is_some_and(|x| x == "md"));
    for path in scan {
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        let label = path.display().to_string();
        for prefix in ["FR-", "NFR-", "SR-"] {
            for (index, _) in text.match_indices(prefix) {
                let tail = &text[index + prefix.len()..];
                let owner = tail.chars().take_while(|c| c.is_ascii_alphanumeric()).collect::<String>();
                if owner.len() != 4 || !crate::support::valid_id(&owner) { continue; }
                let rest = &tail[owner.len()..];
                if !rest.starts_with('-') { continue; }
                let digits = rest[1..].chars().take_while(char::is_ascii_digit).count();
                if digits == 0 { continue; }
                let reference = format!("{prefix}{owner}-{}", &rest[1..1 + digits]);
                checked += 1;
                let key = format!("{prefix}{owner}-");
                match declared.get(&key) {
                    Some(set) if set.contains(&reference) => {}
                    Some(_) => errors.push(format!("reference.unknown {label}: cites `{reference}`, which {owner} does not define")),
                    None => errors.push(format!("reference.no_owner {label}: cites `{reference}`, but {owner} declares no {prefix}ids")),
                }
            }
        }
        // Repository-relative paths a document points at must exist.
        for token in backtick_tokens(&text) {
            let candidate = token.split_whitespace().next().unwrap_or("");
            if !(candidate.starts_with("docs/") || candidate.starts_with("design/artboards/")) { continue; }
            if candidate.contains('*') || !candidate.ends_with(".md") && !candidate.ends_with(".html") { continue; }
            checked += 1;
            if !std::path::Path::new(candidate).exists() {
                errors.push(format!("reference.missing_file {label}: points at `{candidate}`, which does not exist"));
            }
        }
    }
    errors.sort();
    errors.dedup();
    if errors.is_empty() {
        println!("reference checks passed: {checked} cross-references resolve");
        return Ok(());
    }
    for error in errors.iter().take(40) { eprintln!("BLOCKED: {error}"); }
    Err(format!("reference audit failed: {} finding(s)", errors.len()))
}

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
    let placed = expected.lines().filter(|l| l.starts_with("| F") && !l.starts_with("| Feature")).count();
    println!("build order checks passed: {placed} features placed, doc matches");
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
    for (id, (_, _, _, deps)) in &meta {
        for dep in deps.iter().filter(|d| meta.contains_key(*d)) { out.push_str(&format!("  {dep} --> {id}\n")); }
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
    for (id, (_, _, _, deps)) in &meta {
        for dep in deps.iter().filter(|d| meta.contains_key(*d)) { out.push_str(&format!("  {dep} -> {id};\n")); }
    }
    out.push_str("}\n");
    Ok(out)
}

/// A self-contained page: no CDN, no build step, opens from the filesystem. Waves are columns and a
/// feature sits at the row of its index, so an edge that spans many columns is a long pole by eye.
fn order_html() -> Result<String, String> {
    let (waves, meta) = compute_waves()?;
    let (col, row_h, box_w, box_h, pad) = (300usize, 46usize, 210usize, 34usize, 40usize);
    let mut at: HashMap<String, (usize, usize)> = HashMap::new();
    for (w, ids) in &waves {
        for (index, id) in ids.iter().enumerate() {
            at.insert(id.clone(), (pad + w * col, pad + 40 + index * row_h));
        }
    }
    let height = pad * 2 + 60 + waves.iter().map(|(_, i)| i.len()).max().unwrap_or(1) * row_h;
    let width = pad * 2 + waves.len() * col;
    let mut edges = String::new();
    for (id, (_, _, _, deps)) in &meta {
        let Some(&(x2, y2)) = at.get(id) else { continue; };
        for dep in deps.iter().filter(|d| meta.contains_key(*d)) {
            let Some(&(x1, y1)) = at.get(dep) else { continue; };
            let (sx, sy) = (x1 + box_w, y1 + box_h / 2);
            let (ex, ey) = (x2, y2 + box_h / 2);
            let mid = (sx + ex) / 2;
            edges.push_str(&format!("<path d=\"M{sx},{sy} C{mid},{sy} {mid},{ey} {ex},{ey}\" fill=\"none\" stroke=\"#c2c9d2\" stroke-width=\"1.2\"/>"));
        }
    }
    let mut nodes = String::new();
    for (w, ids) in &waves {
        let x = pad + w * col;
        nodes.push_str(&format!("<text x=\"{x}\" y=\"{}\" font-size=\"12\" font-weight=\"700\" fill=\"#8c94a1\" font-family=\"system-ui\">WAVE {w}</text>", pad + 20));
        for id in ids {
            let (nx, ny) = at[id];
            let (title, milestone, points, _) = &meta[id];
            let short: String = title.chars().take(26).collect();
            nodes.push_str(&format!(
                "<g><rect x=\"{nx}\" y=\"{ny}\" width=\"{box_w}\" height=\"{box_h}\" rx=\"6\" fill=\"#ffffff\" stroke=\"#dee2e8\"/>\
                 <text x=\"{}\" y=\"{}\" font-size=\"11\" font-weight=\"700\" fill=\"#14171c\" font-family=\"ui-monospace,monospace\">{id}</text>\
                 <text x=\"{}\" y=\"{}\" font-size=\"10\" fill=\"#5b636f\" font-family=\"system-ui\">{short}</text>\
                 <text x=\"{}\" y=\"{}\" font-size=\"9\" fill=\"#8c94a1\" font-family=\"ui-monospace,monospace\" text-anchor=\"end\">{milestone} · {points}</text></g>",
                nx + 8, ny + 14, nx + 8, ny + 27, nx + box_w - 8, ny + 14));
        }
    }
    Ok(format!("<!doctype html><meta charset=\"utf-8\"><title>OpsHub build order</title>\
<body style=\"margin:0;background:#f6f7f9;font-family:system-ui\">\
<div style=\"padding:24px 40px\"><h1 style=\"margin:0;font-size:20px\">OpsHub build order</h1>\
<p style=\"margin:6px 0 0;font-size:13px;color:#5b636f\">Generated by <code>cargo xtask build-order --html</code>. \
A feature is schedulable when every dependency to its left is archived and its milestone has been reached. \
An edge crossing many columns is a long pole.</p></div>\
<svg width=\"{width}\" height=\"{height}\" xmlns=\"http://www.w3.org/2000/svg\">{edges}{nodes}</svg></body>"))
}

/// Completeness: a ticket must define what it builds, not gesture at it. Two implementers reading
/// the same ticket have to produce the same tables, the same JSON and the same function signatures.
/// This measures that mechanically; what it cannot measure is stated in the ticket-writing rules.
pub(crate) fn check_completeness() -> Result<(), String> {
    let mut errors = Vec::new();
    let (mut complete, mut total) = (0usize, 0usize);
    for path in ticket_files() {
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        let id = front_value(&text, "id:").unwrap_or_default();
        let label = path.display().to_string();
        if text.contains("no user surface") && !text.contains("### Interface") && !text.contains("/api/v1") {
            continue; // tooling features carry no HTTP or data surface
        }
        total += 1;
        let mut gaps = Vec::new();

        // Every route the ticket names needs a defined payload, not a named type.
        let routes = text.matches("/api/v1").count();
        if routes > 0 && !text.contains("### Interface") {
            gaps.push("no `### Interface` section defining request and response shapes".to_owned());
        }
        // A named DTO with no field list is the gap that lets two people build different JSON.
        let named: HashSet<String> = crate::support::backtick_tokens(&text).into_iter()
            .filter(|t| (t.ends_with("Request") || t.ends_with("Response")) && t.chars().next().is_some_and(|c| c.is_uppercase()))
            .collect();
        let defined = text.matches("| Field | Type |").count() + text.matches("| Field | Type | Required |").count();
        if !named.is_empty() && defined == 0 {
            gaps.push(format!("{} request/response types named, none with a field table", named.len()));
        }
        // Use cases must carry signatures, not just names.
        if text.contains("- Use cases") && !text.contains("fn ") {
            gaps.push("use cases named without signatures".to_owned());
        }
        // Multi-table writes need their transaction boundary stated.
        if text.contains("Migration `") && !text.contains("UnitOfWork") {
            gaps.push("owns tables but names no transaction boundary".to_owned());
        }
        if gaps.is_empty() { complete += 1; } else {
            for gap in gaps { errors.push(format!("incomplete {label}: {id} {gap}")); }
        }
    }
    if errors.is_empty() {
        println!("completeness checks passed: {complete}/{total} tickets fully specified");
        return Ok(());
    }
    errors.sort();
    for error in errors.iter().take(30) { eprintln!("BLOCKED: {error}"); }
    Err(format!("completeness audit failed: {complete}/{total} complete, {} gap(s)", errors.len()))
}
