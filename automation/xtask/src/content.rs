//! Content-quality gates: a backlog file passes only when it carries real, feature-specific specification.
use std::{collections::{HashMap, HashSet}, fs, path::Path};
use crate::backlog::Plan;
use crate::support::{backtick_tokens, list_field, path_covered, tagged_ids};

const PLACEHOLDERS: &[&str] = &["UNRESOLVED", "TBD", "TODO", "[detail", "[testable", "[list]", "[persona]", "[name", "[team", "[paths]", "[flag", "[command", "[behavior]", "[IDs", "[target]", "[outcome]", "[outcome.]", "[capability]", "[capabilities]", "[Feature title]", "[Story title]", "[Task title]", "[Epic title]", "F___", "S___", "T___", "E___", "M___", "Define exact", "unassigned", "owned_paths: []", "defined by child", "specified by the child", "has a defined contract, production call path", "[area]", "[link", "[cases]", "[modules]", "[strategy]", "[services]", "[location]", "[routes/actions]", "[numbered steps]"];

const FEATURE_SECTIONS: &[&str] = &["## 1. Identity and dates", "## 2. Requirement specification", "### Problem and user outcome", "### Functional requirements", "### Non-functional requirements", "### Scope", "## 3. UX specification", "## 4. Technical specification", "### Rust backend", "### PostgreSQL/SQLx", "### React/TypeScript", "## 5. TDD and isolated test harness", "### Fast fanout configuration", "## 6. Acceptance criteria", "## 7. Dependencies and risks", "## 7.1 Agent handoff", "## 8. Entry criteria", "## 9. Exit criteria", "## 10. Release notes"];
const STORY_SECTIONS: &[&str] = &["## Identity", "## Vertical slice", "## Requirements", "## Surfaces", "## TDD harness", "## Exit criteria"];
const TASK_SECTIONS: &[&str] = &["## Identity", "## Objective", "## Specification", "## TDD", "## Exit criteria"];
const EPIC_SECTIONS: &[&str] = &["## Outcome", "## Scope", "## Child features", "## Exit criteria"];
const LANES: &[(&str, usize)] = &[("requirements", 8), ("api", 4), ("database", 3), ("frontend", 2), ("e2e", 3), ("accessibility", 3), ("performance", 3)];
// Non-module roots: CI config plus the fanout runtime and evidence directories F043/F044 own.
// FR-F041-08 scopes the catch-all rule to source-tree roots, so these are exempt from the
// interim segment-count heuristic below.
const CATCH_ALL_EXEMPT: &[&str] = &[".github/workflows/**", ".githooks/**", "infra/**", "openapi/**", ".lanes/**", ".worktrees/**", ".agent-target/**", "testing/evidence/**"];

fn catch_all(path: &str) -> bool {
    let segments = path.split('/').collect::<Vec<_>>();
    path.ends_with("/**") && segments.len() <= 3 && !CATCH_ALL_EXEMPT.contains(&path)
}

fn feature_id(plan: &Plan, id: &str) -> Option<String> { plan.feature_of(id).map(|f| f.id.clone()) }

pub(crate) fn check_file(plan: &Plan, path: &Path, text: &str, kind: &str) -> Vec<String> {
    let label = path.display().to_string();
    let mut errors = Vec::new();
    for marker in PLACEHOLDERS { if text.contains(marker) { errors.push(format!("{label}: placeholder `{marker}`")); } }
    for token in backtick_tokens(text) { if token.ends_with(".changed") || (token.contains(".changed.") && !token.ends_with(".v1")) { errors.push(format!("{label}: synthetic event `{token}`")); } }
    let id = crate::support::front_value(text, "id:").unwrap_or_default();
    let sections: &[&str] = match kind { "feature" => FEATURE_SECTIONS, "story" => STORY_SECTIONS, "task" => TASK_SECTIONS, "epic" => EPIC_SECTIONS, _ => &[] };
    for section in sections { if !text.contains(section) { errors.push(format!("{label}: missing section `{section}`")); } }
    let owned = list_field(text, "owned_paths:");
    if kind != "epic" {
        if owned.is_empty() { errors.push(format!("{label}: owned_paths empty")); }
        for p in &owned { if catch_all(p) { errors.push(format!("{label}: catch-all owned path `{p}`")); } }
    }
    match kind {
        "feature" => {
            let fr = tagged_ids(text, &format!("FR-{id}-")).len();
            let nfr = tagged_ids(text, &format!("NFR-{id}-")).len();
            if fr < 8 { errors.push(format!("{label}: {fr} FR-{id}-NN requirements; need 8")); }
            if nfr < 4 { errors.push(format!("{label}: {nfr} NFR-{id}-NN requirements; need 4")); }
            if text.matches("Scenario:").count() < 3 { errors.push(format!("{label}: need at least 3 gherkin scenarios")); }
            if !owned.iter().any(|p| p == &format!("testing/features/{id}/**")) { errors.push(format!("{label}: owned_paths must include testing/features/{id}/**")); }
            if !text.contains(&format!("testing/features/{id}/")) { errors.push(format!("{label}: harness path testing/features/{id}/ not referenced")); }
        }
        "story" => {
            let sr = tagged_ids(text, &format!("SR-{id}-")).len();
            if sr < 5 { errors.push(format!("{label}: {sr} SR-{id}-NN requirements; need 5")); }
            let feature = feature_id(plan, &id).unwrap_or_default();
            if tagged_ids(text, &format!("FR-{feature}-")).is_empty() { errors.push(format!("{label}: must cite FR-{feature}-NN requirements")); }
            if !text.contains(&format!("testing/features/{feature}/")) { errors.push(format!("{label}: harness path testing/features/{feature}/ not referenced")); }
            let named = text.lines().find(|l| l.contains("First failing tests")).map(|l| backtick_tokens(l).len()).unwrap_or(0);
            if named < 4 { errors.push(format!("{label}: `First failing tests` must name at least 4 tests")); }
            errors.extend(subset_errors(plan, &label, &feature, &owned));
        }
        "task" => {
            let feature = feature_id(plan, &id).unwrap_or_default();
            if !text.contains(&format!("testing/features/{feature}/")) { errors.push(format!("{label}: harness path testing/features/{feature}/ not referenced")); }
            if text.matches("::").count() < 3 { errors.push(format!("{label}: name at least 3 failing tests (`file::test`)")); }
            if !text.contains("Targeted command:") || !text.contains("Full command:") { errors.push(format!("{label}: targeted and full commands required")); }
            errors.extend(subset_errors(plan, &label, &feature, &owned));
        }
        "epic" => {
            let features = plan.features.iter().filter(|f| f.epic == id).map(|f| f.id.clone()).collect::<Vec<_>>();
            for f in features { if !text.contains(&f) { errors.push(format!("{label}: child feature {f} not listed")); } }
        }
        _ => {}
    }
    errors
}

fn subset_errors(plan: &Plan, label: &str, feature: &str, owned: &[String]) -> Vec<String> {
    let Some(path) = plan.expected_paths().get(feature).cloned() else { return vec![format!("{label}: parent feature {feature} not in plan")]; };
    let parent = fs::read_to_string(&path).map(|t| list_field(&t, "owned_paths:")).unwrap_or_default();
    owned.iter().filter(|p| !parent.iter().any(|q| path_covered(q, p))).map(|p| format!("{label}: owned path `{p}` not covered by {feature} owned_paths")).collect()
}

/// Checks spanning files: duplicate bodies, overlapping ownership, and harness case quality.
pub(crate) fn check_cross_file(plan: &Plan) -> Vec<String> {
    let mut errors = Vec::new();
    let mut bodies: HashMap<String, String> = HashMap::new();
    let mut owned_by: HashMap<String, String> = HashMap::new();
    for f in &plan.features {
        let Some(path) = plan.expected_paths().get(&f.id).cloned() else { continue; };
        let Ok(text) = fs::read_to_string(&path) else { continue; };
        let body = text.replace(&f.id, "F###").replace(&f.title, "TITLE");
        let body = body.split("## 2. Requirement specification").nth(1).unwrap_or("").to_owned();
        if let Some(other) = bodies.insert(body.clone(), f.id.clone()) { if !body.is_empty() { errors.push(format!("{}: ticket body identical to {other}", f.id)); } }
        for p in list_field(&text, "owned_paths:") {
            if p.starts_with("testing/features/") { continue; }
            if let Some(other) = owned_by.insert(p.clone(), f.id.clone()) { errors.push(format!("{}: owned path `{p}` also owned by {other}", f.id)); }
        }
        errors.extend(check_harness(f, &text));
    }
    let mut lane_bodies: HashMap<(String, String), String> = HashMap::new();
    for f in &plan.features {
        for (lane, _) in LANES {
            let Ok(text) = fs::read_to_string(format!("testing/features/{}/{lane}/cases.md", f.id)) else { continue; };
            let key = (lane.to_string(), text.replace(&f.id, "F###").replace(&f.title, "TITLE"));
            if let Some(other) = lane_bodies.insert(key, f.id.clone()) { errors.push(format!("{}: {lane}/cases.md identical to {other}", f.id)); }
        }
    }
    errors
}

fn check_harness(f: &crate::backlog::PlanFeature, ticket: &str) -> Vec<String> {
    let mut errors = Vec::new();
    let dir = Path::new("testing/features").join(&f.id);
    if !dir.join("feature.toml").exists() || !dir.join("README.md").exists() { errors.push(format!("{}: harness README.md/feature.toml missing", f.id)); }
    let mut requirement_ids: HashSet<String> = tagged_ids(ticket, &format!("FR-{}-", f.id));
    requirement_ids.extend(tagged_ids(ticket, &format!("NFR-{}-", f.id)));
    for (lane, minimum) in LANES {
        let path = dir.join(lane).join("cases.md");
        let Ok(text) = fs::read_to_string(&path) else { errors.push(format!("{}: missing {lane}/cases.md", f.id)); continue; };
        for marker in PLACEHOLDERS { if text.contains(marker) { errors.push(format!("{}: placeholder `{marker}`", path.display())); } }
        let rows = text.lines().filter(|l| l.starts_with("- ") || (l.starts_with("| ") && !l.starts_with("| Case") && !l.starts_with("|---"))).count();
        if rows < *minimum { errors.push(format!("{}: {rows} cases; need {minimum}", path.display())); }
        if !text.contains(&format!("FR-{}-", f.id)) && !text.contains(&format!("NFR-{}-", f.id)) { errors.push(format!("{}: cases must cite FR/NFR ids", path.display())); }
        if *lane == "requirements" {
            for rid in &requirement_ids { if !text.contains(rid.as_str()) { errors.push(format!("{}: {rid} has no requirements case", path.display())); } }
        }
    }
    errors
}

/// Positive control: a boilerplate ticket must be rejected and the gold ticket must pass.
pub(crate) fn self_test() -> Result<(), String> {
    let plan = Plan::load()?;
    let gold = Path::new("work/tickets/F006-sheets-boards-items.md");
    let text = fs::read_to_string(gold).map_err(|e| format!("gold ticket: {e}"))?;
    let errors = check_file(&plan, gold, &text, "feature");
    if !errors.is_empty() { return Err(format!("gold ticket rejected: {errors:?}")); }
    let boilerplate = text.replace("FR-F006-", "FR-X-").replace("Scenario:", "Case:") + "\n`sheet.changed`\nUNRESOLVED\n";
    let errors = check_file(&plan, gold, &boilerplate, "feature");
    let expected = ["placeholder", "synthetic event", "FR-F006-NN", "gherkin"];
    for needle in expected { if !errors.iter().any(|e| e.contains(needle)) { return Err(format!("content positive control missed `{needle}`")); } }
    // Pins CATCH_ALL_EXEMPT: source-tree roots stay rejected, the fanout runtime and evidence
    // roots stay accepted. Widening the exemption to a source root fails here.
    let probe = text.replace("owned_paths: [", "owned_paths: [services/api/**, .lanes/**, .worktrees/**, .agent-target/**, testing/evidence/**, ");
    let errors = check_file(&plan, gold, &probe, "feature");
    if !errors.iter().any(|e| e.contains("catch-all owned path `services/api/**`")) { return Err("catch-all control missed a source-tree root".into()); }
    for exempt in [".lanes/**", ".worktrees/**", ".agent-target/**", "testing/evidence/**"] {
        if errors.iter().any(|e| e.contains(&format!("catch-all owned path `{exempt}`"))) { return Err(format!("exempt root `{exempt}` rejected as a catch-all")); }
    }
    println!("content self-test passed"); Ok(())
}
