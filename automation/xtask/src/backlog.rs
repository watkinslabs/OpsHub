use std::{collections::{HashMap, HashSet}, fs, path::Path};
use crate::policy::report;
use crate::support::{check_line_limits, front_value, item, list_field, slug, ticket_files, valid_id, work_files};

pub(crate) const REQUIRED: &[&str] = &["id:", "type:", "status:", "priority:", "owner:", "estimate:", "target_milestone:", "parent_epic:", "depends_on:", "blocks:", "conflicts_with:", "parallel_safe:", "owned_paths:", "feature_flag:", "flag_default:", "branch:", "started_at:", "finished_at:", "## 2. Requirement specification", "## 5. TDD and isolated test harness", "## 8. Entry criteria", "## 9. Exit criteria", "## 10. Release notes"];

pub(crate) struct PlanFeature {
    pub id: String,
    pub title: String,
    pub epic: String,
    pub stories: Vec<(String, String)>,
    pub tasks: Vec<(String, String)>,
    pub deps: Vec<String>,
}

pub(crate) struct Plan {
    pub epics: Vec<(String, String)>,
    pub features: Vec<PlanFeature>,
}

impl Plan {
    pub fn load() -> Result<Plan, String> {
        let text = fs::read_to_string("work/plan.md").map_err(|e| format!("work/plan.md: {e}"))?;
        let mut plan = Plan { epics: Vec::new(), features: Vec::new() };
        let mut epic = String::new();
        for line in text.lines() {
            if let Some(rest) = line.strip_prefix("## E") {
                let mut parts = format!("E{rest}").splitn(2, " — ").map(str::trim).map(str::to_owned).collect::<Vec<_>>().into_iter();
                let (id, title) = (parts.next().unwrap_or_default(), parts.next().unwrap_or_default());
                if valid_id(&id) { epic = id.clone(); plan.epics.push((id, title)); }
                continue;
            }
            if !line.starts_with("| F") { continue; }
            let cols = line.split('|').map(str::trim).collect::<Vec<_>>();
            if cols.len() < 6 { continue; }
            let Some((id, title)) = item(cols[1]) else { continue; };
            if !valid_id(&id) || !id.starts_with('F') { continue; }
            let parse = |cell: &str| cell.split(';').filter_map(item).filter(|(id, _)| valid_id(id)).collect::<Vec<_>>();
            let deps = cols[4].split(',').map(str::trim).filter(|x| valid_id(x)).map(str::to_owned).collect();
            plan.features.push(PlanFeature { id, title, epic: epic.clone(), stories: parse(cols[2]), tasks: parse(cols[3]), deps });
        }
        Ok(plan)
    }

    /// Expected file path for every planned item, keyed by ID.
    pub fn expected_paths(&self) -> HashMap<String, String> {
        let mut map = HashMap::new();
        for (id, title) in &self.epics { map.insert(id.clone(), format!("work/epics/{id}-{}.md", slug(title))); }
        for f in &self.features {
            map.insert(f.id.clone(), format!("work/tickets/{}-{}.md", f.id, slug(&f.title)));
            for (id, title) in &f.stories { map.insert(id.clone(), format!("work/stories/{id}-{}.md", slug(title))); }
            for (id, title) in &f.tasks { map.insert(id.clone(), format!("work/tasks/{id}-{}.md", slug(title))); }
        }
        map
    }

    pub fn feature(&self, id: &str) -> Option<&PlanFeature> { self.features.iter().find(|f| f.id == id) }

    pub fn feature_of(&self, id: &str) -> Option<&PlanFeature> {
        self.features.iter().find(|f| f.id == id || f.stories.iter().any(|(s, _)| s == id) || f.tasks.iter().any(|(t, _)| t == id))
    }
}

pub(crate) fn validate_decisions() -> Result<(), String> {
    let path = Path::new("docs/architecture-decisions.md");
    let text = fs::read_to_string(path).map_err(|e| format!("missing decisions: {e}"))?;
    for section in ["## 1. Runtime and repository", "## 2. Canonical data model", "## 3. API and events", "## 4. Identity and authorization", "## 5. Files, documents, and collaboration", "## 6. Web experience", "## 7. Jobs and integrations", "## 8. MCP", "## 9. Testing", "## 10. Ticket gate"] {
        if !text.contains(section) { return Err(format!("decision section missing: {section}")); }
    }
    if text.contains("Open decisions") || text.contains("TBD") || text.contains("to resolve") { return Err("unresolved architecture decision language".into()); }
    if !text.contains("PostgreSQL 18") { return Err("PostgreSQL version decision is not 18".into()); }
    if !Path::new("docs/product-capability-spec.md").exists() { return Err("product capability spec missing".into()); }
    println!("architecture decisions passed"); Ok(())
}

pub(crate) fn validate_plan() -> Result<(), String> {
    let plan = Plan::load()?;
    let expected = plan.expected_paths();
    let mut errors = Vec::new();
    let mut seen = HashSet::new();
    for id in expected.keys() { if !seen.insert(id.clone()) { errors.push(format!("plan lists {id} twice")); } }
    for f in &plan.features {
        if f.stories.len() != 2 || f.tasks.len() != 4 { errors.push(format!("{}: plan row must list 2 stories and 4 tasks", f.id)); }
        for dep in &f.deps { if plan.feature(dep).is_none() { errors.push(format!("{}: depends on unknown feature {dep}", f.id)); } }
    }
    let mut actual = HashMap::new();
    for path in work_files() {
        let text = fs::read_to_string(&path).unwrap_or_default();
        if let Some(id) = front_value(&text, "id:") { actual.insert(id, path.to_string_lossy().replace('\\', "/")); }
    }
    for (id, path) in &expected {
        match actual.get(id) {
            None => errors.push(format!("plan item missing file: {id} expected at {path}")),
            Some(found) if found != path && !found.starts_with("work/inprogress") && !found.starts_with("work/archived") => errors.push(format!("{id}: file {found} must be named {path}")),
            _ => {}
        }
    }
    for id in actual.keys() { if !expected.contains_key(id) { errors.push(format!("materialized item not in plan: {id}")); } }
    report(errors)?; println!("plan/file parity passed"); Ok(())
}

fn validate_ticket(path: &Path) -> Vec<String> {
    let name = path.file_stem().and_then(|x| x.to_str()).unwrap_or_default();
    let mut errors = Vec::new();
    let text = fs::read_to_string(path).unwrap_or_default();
    let label = path.display();
    if name.len() < 5 || !valid_id(&name[..4]) || !name[4..].starts_with('-') { errors.push(format!("{label}: invalid filename")); }
    for key in REQUIRED { if !text.contains(key) { errors.push(format!("{label}: missing {key}")); } }
    let id = front_value(&text, "id:").unwrap_or_default();
    let kind = front_value(&text, "type:").unwrap_or_default();
    if !valid_id(&id) { errors.push(format!("{label}: invalid id")); }
    if !["feature", "bug", "spike"].contains(&kind.as_str()) { errors.push(format!("{label}: type must be feature, bug, or spike")); }
    if valid_id(&id) && !name.starts_with(&id) { errors.push(format!("{label}: filename id mismatch")); }
    let branch = front_value(&text, "branch:").unwrap_or_default();
    if valid_id(&id) && !branch.starts_with(&format!("{}{}-", id[..1].to_ascii_lowercase(), &id[1..])) { errors.push(format!("{label}: invalid branch {branch}")); }
    if !["P0", "P1", "P2", "P3"].contains(&front_value(&text, "priority:").unwrap_or_default().as_str()) { errors.push(format!("{label}: priority must be P0-P3")); }
    if !["1", "2", "3", "5", "8", "13"].contains(&front_value(&text, "estimate:").unwrap_or_default().as_str()) { errors.push(format!("{label}: estimate must be 1/2/3/5/8/13")); }
    if front_value(&text, "flag_default:").as_deref() != Some("off") { errors.push(format!("{label}: flag_default must be off")); }
    if front_value(&text, "feature_flag:") != Some(format!("{id}_FEATURE")) { errors.push(format!("{label}: feature_flag must be {id}_FEATURE")); }
    if path.starts_with("work/inprogress") && text.contains("started_at: null") { errors.push(format!("{label}: started_at required")); }
    if path.starts_with("work/archived") && text.contains("finished_at: null") { errors.push(format!("{label}: finished_at required")); }
    errors
}

pub(crate) fn validate_tickets() -> Result<(), String> {
    let mut errors = ticket_files().iter().flat_map(|p| validate_ticket(p)).collect::<Vec<_>>();
    errors.extend(check_line_limits(Path::new(".")));
    report(errors)?; println!("ticket validation passed"); Ok(())
}

/// Structural checks for every epic, feature, story, and task file, followed by content checks.
pub(crate) fn validate_work() -> Result<(), String> {
    let plan = Plan::load()?;
    let mut errors = Vec::new();
    for shared in ["testing/harness", "testing/fixtures", "testing/config", "testing/evidence"] {
        if !Path::new(shared).join("README.md").exists() { errors.push(format!("missing shared testing directory: {shared}")); }
    }
    let files = work_files();
    let ids = files.iter().filter_map(|p| fs::read_to_string(p).ok()).filter_map(|t| front_value(&t, "id:")).collect::<Vec<_>>();
    let id_set = ids.iter().cloned().collect::<HashSet<_>>();
    if id_set.len() != ids.len() { errors.push("duplicate backlog id".into()); }
    for path in &files {
        let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
        let label = path.display().to_string();
        let name = path.file_stem().and_then(|x| x.to_str()).unwrap_or_default();
        let id = front_value(&text, "id:").unwrap_or_default();
        let kind = front_value(&text, "type:").unwrap_or_default();
        let expected = if path.starts_with("work/epics") { "epic" } else if path.starts_with("work/tickets") { "feature" } else if path.starts_with("work/stories") { "story" } else if path.starts_with("work/tasks") { "task" } else { "" };
        if !valid_id(&id) || !name.starts_with(&id) { errors.push(format!("{label}: invalid or mismatched id")); continue; }
        if !expected.is_empty() && kind != expected { errors.push(format!("{label}: expected type {expected}, found {kind}")); }
        let branch = front_value(&text, "branch:").unwrap_or_default();
        if !branch.starts_with(&format!("{}{}-", id[..1].to_ascii_lowercase(), &id[1..])) { errors.push(format!("{label}: invalid branch")); }
        if kind != "epic" && !text.contains("docs/architecture-decisions.md") { errors.push(format!("{label}: missing architecture decision link")); }
        for dep in list_field(&text, "depends_on:") { if !id_set.contains(&dep) { errors.push(format!("{label}: depends_on unknown item {dep}")); } }
        if kind == "feature" {
            let planned = plan.feature(&id).map(|f| f.deps.clone()).unwrap_or_default();
            let mut declared = list_field(&text, "depends_on:"); declared.sort();
            let mut planned_sorted = planned.clone(); planned_sorted.sort();
            if declared != planned_sorted { errors.push(format!("{label}: depends_on {declared:?} must match plan {planned:?}")); }
            if let Some(f) = plan.feature(&id) { if front_value(&text, "parent_epic:").as_deref() != Some(f.epic.as_str()) { errors.push(format!("{label}: parent_epic must be {}", f.epic)); } }
        }
        if kind == "story" || kind == "task" {
            if list_field(&text, "depends_on:").is_empty() { errors.push(format!("{label}: depends_on must not be empty")); }
            if let Some(f) = plan.feature_of(&id) { if front_value(&text, "parent_feature:").as_deref() != Some(f.id.as_str()) { errors.push(format!("{label}: parent_feature must be {}", f.id)); } }
        }
        if kind == "task" {
            let story = front_value(&text, "parent_story:").unwrap_or_default();
            let ok = plan.feature_of(&id).is_some_and(|f| f.tasks.iter().position(|(t, _)| *t == id).zip(f.stories.get(0).map(|_| ())).is_some_and(|(pos, _)| f.stories.get(pos / 2).is_some_and(|(s, _)| *s == story)));
            if !ok { errors.push(format!("{label}: parent_story {story} does not match plan ordering")); }
        }
        errors.extend(crate::content::check_file(&plan, path, &text, &kind));
    }
    errors.extend(crate::content::check_cross_file(&plan));
    errors.extend(check_line_limits(Path::new("work")));
    errors.extend(check_line_limits(Path::new("testing")));
    report(errors)?; println!("work validation passed: {} items", files.len()); Ok(())
}

/// Create missing item files and harness directories from templates. Never overwrites and never touches the contract catalog.
pub(crate) fn scaffold_plan() -> Result<(), String> {
    validate_decisions()?;
    let plan = Plan::load()?;
    let mut created = 0;
    for (id, path) in plan.expected_paths() {
        if Path::new(&path).exists() { continue; }
        let kind = match id.as_bytes()[0] { b'E' => "epic", b'F' => "ticket", b'S' => "story", _ => "task" };
        let template = fs::read_to_string(format!("work/templates/{kind}.md")).map_err(|e| format!("template {kind}: {e}"))?;
        let title = plan.expected_paths().get(&id).map(|p| p.rsplit('/').next().unwrap_or_default().trim_end_matches(".md")[5..].to_owned()).unwrap_or_default();
        let letter = id[..1].to_ascii_lowercase();
        let body = template.replace(&format!("{}___", &id[..1]), &id).replace(&format!("{letter}___-[slug]"), &format!("{letter}{}-{title}", &id[1..]));
        fs::write(&path, body).map_err(|e| format!("{path}: {e}"))?; created += 1;
    }
    for f in &plan.features {
        let dir = Path::new("testing/features").join(&f.id);
        for lane in ["requirements", "api", "database", "frontend", "e2e", "accessibility", "performance"] {
            let lane_dir = dir.join(lane);
            fs::create_dir_all(&lane_dir).map_err(|e| e.to_string())?;
            // Only cases.md. A per-lane README restates the id, flag, and title already carried by
            // the path, the feature README, and cases.md itself.
            let target = lane_dir.join("cases.md");
            let body = format!("# {} {lane} cases\n\n[testable cases for {}]\n", f.id, f.title);
            if !target.exists() { fs::write(&target, body).map_err(|e| e.to_string())?; created += 1; }
        }
        for (file, body) in [("README.md", format!("# {} — {} harness\n\n- Gate: `{}_FEATURE`\n- Targeted: `cargo xtask test-feature {}`\n- Full: `cargo xtask test-all`\n", f.id, f.title, f.id, f.id)), ("feature.toml", format!("feature = \"{}\"\nflag = \"{}_FEATURE\"\nfixture_scope = \"isolated-tenant\"\nparallel_safe = true\ntargeted_command = \"cargo xtask test-feature {}\"\nfull_command = \"cargo xtask test-all\"\n", f.id, f.id, f.id))] {
            let target = dir.join(file);
            if !target.exists() { fs::write(&target, body).map_err(|e| e.to_string())?; created += 1; }
        }
    }
    println!("scaffolded {created} missing file(s); fill placeholders before validate-work will pass"); Ok(())
}
