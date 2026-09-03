# F061 api lane

Rust integration tests for the four authenticated `/api/v1/update-requests` routes and the two unauthenticated `/public/update-requests` routes: scope validation, per-recipient token hashing, drafts and partial submission, row-version conflicts, reminder claiming and dedupe, cancellation, audit correlation, rate limits, and cross-tenant negatives. Gate `F061_FEATURE`; one schema per worker.
