# F061 database lane

Migration and constraint tests for `update_requests`, `update_request_recipients`, `update_request_responses`, and `reminder_schedules`: status and array-length checks, unique `token_hash` and `(recipient_id, sequence)`, the response append-only trigger, cascade deletes, the partial index behind the reminder claim query, and the down migration. Gate `F061_FEATURE`.
