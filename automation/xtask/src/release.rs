use std::{fs, path::Path};
use crate::backlog::{validate_decisions, validate_work, Plan};
use crate::policy::report;
use crate::support::{backtick_tokens, front_value, ticket_files, valid_id};

/// Every ticket must reproduce the routes and events of its catalog row, and every catalog row must have a ticket.
pub(crate) fn check_contracts() -> Result<(), String> {
    validate_decisions()?;
    validate_work()?;
    let catalog = fs::read_to_string("docs/capability-contracts.md").map_err(|e| e.to_string())?;
    if catalog.contains("UNRESOLVED") { return Err("unresolved capability contract".into()); }
    let plan = Plan::load()?;
    let mut errors = Vec::new();
    let mut catalog_ids = Vec::new();
    for line in catalog.lines().filter(|l| l.starts_with("| F")) {
        let cols = line.split('|').map(str::trim).collect::<Vec<_>>();
        if cols.len() < 8 || !valid_id(cols[1]) { continue; }
        catalog_ids.push(cols[1].to_owned());
        if plan.feature(cols[1]).is_none() { errors.push(format!("catalog row {} not in plan", cols[1])); }
    }
    for path in ticket_files() {
        let text = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let id = front_value(&text, "id:").unwrap_or_default();
        let label = path.display();
        if !text.contains("## 4. Technical specification") || !text.contains("docs/architecture-decisions.md") || !text.contains("docs/capability-contracts.md") { errors.push(format!("{label}: contract missing decision or catalog link")); }
        let Some(row) = catalog.lines().find(|l| l.starts_with(&format!("| {id} |"))) else { errors.push(format!("{label}: capability contract missing for {id}")); continue; };
        let cols = row.split('|').map(str::trim).collect::<Vec<_>>();
        if cols.len() < 8 { errors.push(format!("catalog row {id} malformed")); continue; }
        let (aggregate, module) = (cols[2].trim_matches('`'), cols[3].trim_matches('`'));
        if !text.contains(&format!("`{aggregate}`")) { errors.push(format!("{label}: aggregate `{aggregate}` not named")); }
        if !text.contains(module) { errors.push(format!("{label}: module slug `{module}` not used")); }
        for column in [4usize, 5] {
            for token in backtick_tokens(cols[column]) {
                let token = token.split(" (").next().unwrap_or(&token).to_owned();
                if token != "none" && !text.contains(&token) { errors.push(format!("{label}: contract token `{token}` missing from ticket")); }
            }
        }
        for table in backtick_tokens(cols[6]) { if !text.contains(&table) { errors.push(format!("{label}: table `{table}` not specified")); } }
        if !catalog_ids.contains(&id) { errors.push(format!("{label}: {id} missing from catalog")); }
    }
    errors.extend(undeclared_routes(&catalog));
    for f in &plan.features { if !catalog_ids.contains(&f.id) { errors.push(format!("plan feature {} missing from catalog", f.id)); } }
    report(errors)?; println!("contract checks passed: {} rows", catalog_ids.len()); Ok(())
}

pub(crate) fn test_feature(id: &str) -> Result<(), String> {
    if !valid_id(id) || !id.starts_with('F') { return Err(format!("invalid feature id: {id}")); }
    let dir = Path::new("testing/features").join(id);
    if !dir.join("README.md").exists() || !dir.join("feature.toml").exists() { return Err(format!("feature harness missing: {id}")); }
    for child in ["requirements", "api", "database", "frontend", "e2e", "accessibility", "performance"] {
        if !dir.join(child).join("cases.md").exists() { return Err(format!("harness cases missing: {id}/{child}")); }
    }
    if Path::new("Cargo.toml").exists() {
        let status = std::process::Command::new("cargo").args(["test", "--workspace", "--features", &format!("{id}_FEATURE"), "--", id]).status().map_err(|e| e.to_string())?;
        if !status.success() { return Err(format!("{id}: feature tests failed")); }
        println!("{id}: feature tests passed"); return Ok(());
    }
    println!("{id}: harness manifest valid; production test execution begins after implementation"); Ok(())
}

pub(crate) fn test_all() -> Result<(), String> {
    let plan = Plan::load()?;
    for f in &plan.features { test_feature(&f.id)?; }
    println!("all {} feature harnesses valid", plan.features.len()); Ok(())
}

pub(crate) fn check_migrations() -> Result<(), String> {
    let root = Path::new("services/api/migrations");
    if !root.exists() { println!("migration check passed: no migrations created"); return Ok(()); }
    let mut names = fs::read_dir(root).map_err(|e| e.to_string())?.filter_map(Result::ok).filter_map(|e| e.file_name().into_string().ok()).collect::<Vec<_>>();
    names.sort();
    let mut errors = Vec::new();
    for name in &names {
        let stem = name.trim_end_matches(".sql").trim_end_matches(".down");
        let mut parts = stem.splitn(2, '_');
        let version = parts.next().unwrap_or_default();
        let description = parts.next().unwrap_or_default();
        if !name.ends_with(".sql") || version.len() < 14 || !version.chars().all(|c| c.is_ascii_digit()) { errors.push(format!("invalid migration filename: {name}")); }
        if !description.contains('_') { errors.push(format!("migration {name} must be named <version>_<module>_<description>.sql")); }
        if name.ends_with(".sql") && !name.ends_with(".down.sql") && !names.contains(&format!("{stem}.down.sql")) { errors.push(format!("migration {name} has no .down.sql rollback")); }
    }
    report(errors)?; println!("migration check passed: {} files", names.len()); Ok(())
}

/// Routes are declared in the catalog and reproduced in tickets. The reverse also has to hold:
/// a route a ticket promises but the catalog never declares is a route nothing generates a handler
/// or an OpenAPI path for. F013 shipped such a link for weeks before this check existed.
fn route_paths(text: &str) -> Vec<String> {
    let mut found = Vec::new();
    for token in backtick_tokens(text) {
        for word in token.split_whitespace() {
            let path = word.trim_end_matches([',', ';', '.']);
            if !path.starts_with("/api/v1") && !path.starts_with("/public/") && !path.starts_with("/auth/")
                && !path.starts_with("/scim/") && !path.starts_with("/embed/") && !path.starts_with("/mcp") { continue; }
            if path.contains(".rs") || path.contains(".sql") || path.contains(".ts") || path.contains('*') || path.contains('?') { continue; }
            found.push(normalize_route(path));
        }
    }
    found.sort();
    found.dedup();
    found
}

/// Parameter names differ between a catalog row and a ticket; the shape is what must match.
fn normalize_route(path: &str) -> String {
    let mut out = String::new();
    let mut in_param = false;
    for ch in path.chars() {
        match ch {
            '{' => { in_param = true; out.push_str("{}"); }
            '}' => in_param = false,
            ':' if !in_param => { in_param = true; out.push_str("{}"); }
            '/' if in_param => { in_param = false; out.push('/'); }
            _ if in_param => {}
            _ => out.push(ch),
        }
    }
    out.trim_end_matches('/').to_owned()
}

fn undeclared_routes(catalog: &str) -> Vec<String> {
    let declared = route_paths(catalog);
    let mut errors = Vec::new();
    for path in ticket_files() {
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        for route in route_paths(&text) {
            // A ticket may name a base path (`/scim/v2`) or a deeper path under a declared route;
            // either direction of prefix means the catalog covers it. Only an unrelated path is a finding.
            if declared.iter().any(|d| *d == route
                || route.starts_with(&format!("{d}/"))
                || d.starts_with(&format!("{route}/"))) { continue; }
            errors.push(format!("{}: route `{route}` is not declared in the catalog", path.display()));
        }
    }
    errors
}
