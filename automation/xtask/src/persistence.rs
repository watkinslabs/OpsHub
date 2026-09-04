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
