//! Enforces architecture decision 2 and 2.1 over the backlog: normalized schema, and one data
//! access class per object type. It reads the specifications, so it holds before any code exists.
use std::{collections::HashMap, fs};
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
