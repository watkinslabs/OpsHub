# F061 e2e lane

Playwright flows across the whole loop: send a request, open the emailed link in a session-free context, save a draft, return and submit, fire a reminder asserted in Mailpit, hit a row-version conflict, and cancel to prove every link dies. Gate `F061_FEATURE`.
