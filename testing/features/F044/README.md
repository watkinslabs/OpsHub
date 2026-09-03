# F044 — Contract/release control harness

Feature-gated tests for `F044`. Keep test code in this directory.

- Gate: `F044_FEATURE`
- Targeted: `cargo test --features F044_FEATURE F044`
- Full: `cargo test --all-features`
- Required: contract, negative, authorization, integration, accessibility, and performance cases applicable to the feature.
