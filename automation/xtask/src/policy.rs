use std::{fs, process::Command};
use crate::support::{check_ownership, policy_file};

pub(crate) fn blocked_tokens() -> Vec<String> {
    vec![
        vec!['C','L','A','U','D','E'], vec!['C','O','W','O','R','K'],
        vec!['O','P','E','N','A','I'], vec!['C','H','A','T','G','P','T'], vec!['C','O','D','E','X'], vec!['C','O','P','I','L','O','T'],
    ].into_iter().map(|x| x.into_iter().collect()).collect()
}

pub(crate) fn git(args: &[&str]) -> Result<String, String> {
    let out = Command::new("git").args(args).output().map_err(|e| e.to_string())?;
    if !out.status.success() { return Err(String::from_utf8_lossy(&out.stderr).trim().into()); }
    Ok(String::from_utf8_lossy(&out.stdout).into())
}

pub(crate) fn findings(label: &str, text: &str) -> Vec<String> {
    let lower = text.to_ascii_lowercase();
    blocked_tokens().into_iter().filter(|x| lower.contains(&x.to_ascii_lowercase()))
        .map(|x| format!("{label}: forbidden token: {x}")).collect()
}

pub(crate) fn report(errors: Vec<String>) -> Result<(), String> {
    if errors.is_empty() { return Ok(()); }
    for error in &errors { eprintln!("BLOCKED: {error}"); }
    Err(format!("policy audit failed: {} finding(s)", errors.len()))
}

fn staged() -> Result<Vec<String>, String> {
    Ok(git(&["diff", "--cached", "--name-only", "-z"])?.split('\0')
        .filter(|x| !x.is_empty()).map(str::to_owned).collect())
}

pub(crate) fn audit_staged() -> Result<(), String> {
    let mut errors = Vec::new();
    for path in staged()? {
        if policy_file(&path) { continue; }
        errors.extend(findings(&format!("staged file {path}"), &git(&["show", &format!(":{path}")])?));
    }
    errors.extend(check_ownership(&staged()?));
    report(errors)
}

pub(crate) fn check_ownership_command() -> Result<(), String> {
    report(check_ownership(&staged()?))
}

pub(crate) fn audit_file(path: &str) -> Result<(), String> {
    report(findings(path, &fs::read_to_string(path).map_err(|e| e.to_string())?))
}

pub(crate) fn audit_range(range: &str) -> Result<(), String> {
    report(findings(&format!("commit range {range}"), &git(&["log", "--format=%H%n%B", range])?))
}

pub(crate) fn audit_pr(title: &str, body: &str) -> Result<(), String> {
    let mut errors = findings("PR title", &fs::read_to_string(title).map_err(|e| e.to_string())?);
    errors.extend(findings("PR body", &fs::read_to_string(body).map_err(|e| e.to_string())?));
    report(errors)
}

pub(crate) fn self_test() -> Result<(), String> {
    if !findings("clean", "normal implementation text").is_empty() { return Err("clean positive control failed".into()); }
    let blocked = blocked_tokens().join(" ");
    if findings("blocked", &blocked).len() != blocked_tokens().len() { return Err("blocked positive control failed".into()); }
    crate::content::self_test()?;
    println!("policy self-test passed"); Ok(())
}

pub(crate) fn install_hooks() -> Result<(), String> {
    git(&["config", "core.hooksPath", ".githooks"])?;
    #[cfg(unix)] for file in [".githooks/pre-commit", ".githooks/commit-msg", ".githooks/pre-push"] {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(file).map_err(|e| e.to_string())?.permissions(); perms.set_mode(0o755); fs::set_permissions(file, perms).map_err(|e| e.to_string())?;
    }
    println!("installed .githooks"); Ok(())
}
