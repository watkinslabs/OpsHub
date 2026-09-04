mod backlog;
mod content;
mod persistence;
mod policy;
mod release;
mod support;

use std::{env, process::ExitCode};

fn usage() -> Result<(), String> {
    eprintln!("cargo xtask <audit-staged|audit-message FILE|audit-range RANGE|audit-pr TITLE BODY|validate-tickets|validate-work|validate-plan|validate-decisions|check-contracts|check-persistence|check-roles|check-design|check-ownership|check-migrations|test-feature ID|test-all|self-test|scaffold-plan|install-hooks>");
    Err("invalid command".into())
}

fn main() -> ExitCode {
    let mut args = env::args().skip(1);
    let result = match args.next().as_deref() {
        Some("audit-staged") => policy::audit_staged(),
        Some("audit-message") => args.next().ok_or("message file required".into()).and_then(|p| policy::audit_file(&p)),
        Some("audit-range") => args.next().ok_or("range required".into()).and_then(|r| policy::audit_range(&r)),
        Some("audit-pr") => args.next().ok_or("title file required".into()).and_then(|t| args.next().ok_or("body file required".into()).and_then(|b| policy::audit_pr(&t, &b))),
        Some("validate-tickets") => backlog::validate_tickets(),
        Some("validate-work") => backlog::validate_work(),
        Some("validate-plan") => backlog::validate_plan(),
        Some("validate-decisions") => backlog::validate_decisions(),
        Some("check-contracts") => release::check_contracts(),
        Some("check-persistence") => persistence::check_persistence(),
        Some("check-roles") => persistence::check_roles(),
        Some("check-design") => persistence::check_design(),
        Some("check-ownership") => policy::check_ownership_command(),
        Some("check-migrations") => release::check_migrations(),
        Some("test-feature") => args.next().ok_or("feature id required".into()).and_then(|id| release::test_feature(&id)),
        Some("test-all") => release::test_all(),
        Some("self-test") => policy::self_test(),
        Some("scaffold-plan") => backlog::scaffold_plan(),
        Some("install-hooks") => policy::install_hooks(),
        _ => usage(),
    };
    match result { Ok(()) => ExitCode::SUCCESS, Err(error) => { eprintln!("{error}"); ExitCode::FAILURE } }
}
