use std::{collections::HashSet, fs, path::{Path, PathBuf}};

pub(crate) fn policy_file(path: &str) -> bool {
    path == "Claude.md" || path == "MANIFEST.md" || path == "automation/README.md" || path == "docs/design-canvas.md" || path == "work/templates/PROJECT_STRUCTURE.md" || path.starts_with("automation/xtask/") || path.starts_with(".githooks/")
}

pub(crate) fn check_line_limits(root: &Path) -> Vec<String> {
    let mut errors = Vec::new();
    let Ok(entries) = fs::read_dir(root) else { return errors; };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.file_name().is_some_and(|x| x == ".git" || x == "target" || x == ".agent-target" || x == "node_modules") { continue; }
        if path.is_dir() { errors.extend(check_line_limits(&path)); continue; }
        if let Ok(text) = fs::read_to_string(&path) {
            let lines = text.lines().count();
            if lines > 500 { errors.push(format!("{}: {lines} lines; limit is 500", path.display())); }
        }
    }
    errors
}

/// Glob match where `**` spans directories and `*` stays inside one segment.
pub(crate) fn glob_match(pattern: &str, path: &str) -> bool {
    fn go(p: &[u8], s: &[u8]) -> bool {
        match p.first() {
            None => s.is_empty(),
            Some(b'*') if p.get(1) == Some(&b'*') => {
                let rest = if p.get(2) == Some(&b'/') { &p[3..] } else { &p[2..] };
                (0..=s.len()).any(|i| go(rest, &s[i..]))
            }
            Some(b'*') => (0..=s.len()).take_while(|&i| i == 0 || s[i - 1] != b'/').any(|i| go(&p[1..], &s[i..])),
            Some(c) => s.first() == Some(c) && go(&p[1..], &s[1..]),
        }
    }
    go(pattern.as_bytes(), path.as_bytes())
}

/// `child` is covered by `parent` when equal, when `parent` ends in `/**` and `child` sits under it, or when the parent glob matches the child literally.
pub(crate) fn path_covered(parent: &str, child: &str) -> bool {
    if parent == child || glob_match(parent, child) { return true; }
    parent.strip_suffix("/**").is_some_and(|prefix| child.starts_with(prefix) && child[prefix.len()..].starts_with('/'))
}

pub(crate) fn list_field(text: &str, key: &str) -> Vec<String> {
    front_value(text, key).map(|value| value.trim_matches(['[', ']']).split(',').map(|x| x.trim().trim_matches('`').to_owned()).filter(|x| !x.is_empty()).collect()).unwrap_or_default()
}

pub(crate) fn check_ownership(paths: &[String]) -> Vec<String> {
    // Only real work-item files count as active. The lifecycle folder's README.md is not a ticket;
    // treating it as one yields an empty owned set and blocks every staged path.
    let active = fs::read_dir("work/inprogress").into_iter().flatten().flatten()
        .map(|x| x.path())
        .filter(|p| p.file_name().is_some_and(|x| x != "README.md"))
        .filter(|p| p.extension().is_some_and(|x| x == "md"))
        .filter_map(|p| fs::read_to_string(p).ok())
        .filter(|text| front_value(text, "id:").is_some_and(|id| valid_id(&id)))
        .collect::<Vec<_>>();
    if active.is_empty() { return Vec::new(); }
    let owned = active.iter().flat_map(|x| list_field(x, "owned_paths:")).collect::<Vec<_>>();
    paths.iter().filter(|path| !policy_file(path) && !owned.iter().any(|scope| path_covered(scope, path)))
        .map(|path| format!("{path}: outside active ticket owned_paths")).collect()
}

pub(crate) fn slug(value: &str) -> String {
    let mut out = String::new();
    for ch in value.chars() {
        if ch.is_ascii_alphanumeric() { out.push(ch.to_ascii_lowercase()); }
        else if !out.ends_with('-') { out.push('-'); }
    }
    out.trim_matches('-').to_owned()
}

pub(crate) fn item(value: &str) -> Option<(String, String)> {
    let mut words = value.split_whitespace();
    let id = words.next()?.to_owned();
    let title = words.collect::<Vec<_>>().join(" ");
    Some((id, title))
}

pub(crate) fn valid_id(value: &str) -> bool {
    let bytes = value.as_bytes(); bytes.len() == 4 && bytes[0].is_ascii_uppercase() && bytes[1..].iter().all(u8::is_ascii_digit)
}

pub(crate) fn front_value(text: &str, key: &str) -> Option<String> {
    let front = text.strip_prefix("---\n").and_then(|rest| rest.split("\n---").next()).unwrap_or(text);
    front.lines().find_map(|line| line.strip_prefix(key).map(|x| x.trim().trim_matches('`').to_owned()))
}

pub(crate) fn ticket_files() -> Vec<PathBuf> {
    md_files(&["work/tickets", "work/inprogress", "work/archived"])
}

pub(crate) fn work_files() -> Vec<PathBuf> {
    md_files(&["work/epics", "work/tickets", "work/stories", "work/tasks", "work/inprogress", "work/archived"])
}

fn md_files(dirs: &[&str]) -> Vec<PathBuf> {
    let mut files = dirs.iter().flat_map(|dir| fs::read_dir(dir).into_iter().flatten().flatten().map(|x| x.path()))
        .filter(|p| p.file_name().is_some_and(|x| x != "README.md"))
        .filter(|p| p.extension().is_some_and(|x| x == "md")).collect::<Vec<_>>();
    files.sort();
    files
}

/// Distinct identifiers of the form `{prefix}NN` found in `text`, e.g. `FR-F006-` → `FR-F006-01`.
pub(crate) fn tagged_ids(text: &str, prefix: &str) -> HashSet<String> {
    let mut found = HashSet::new();
    let mut rest = text;
    while let Some(pos) = rest.find(prefix) {
        let tail = &rest[pos + prefix.len()..];
        let digits = tail.chars().take_while(char::is_ascii_digit).count();
        if digits >= 1 { found.insert(format!("{prefix}{}", &tail[..digits])); }
        rest = &rest[pos + prefix.len()..];
    }
    found
}

pub(crate) fn backtick_tokens(text: &str) -> Vec<String> {
    text.split('`').skip(1).step_by(2).map(str::to_owned).collect()
}
