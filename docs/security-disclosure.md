# Security disclosure and testing

## Reporting a vulnerability

Report to **security@[DOMAIN]**, encrypted to the key published at `/.well-known/security.txt`. Tell
us what you found, how to reproduce it, and what you think it lets someone do. You do not need to
have exploited it, and a proof of concept is welcome but never required.

We commit to: acknowledging within **2 business days**, an initial assessment with a severity within
**5 business days**, and keeping you updated at least every 10 business days until it is closed.

Target time to fix, from confirmation: **Sev 1 — 7 days · Sev 2 — 30 days · Sev 3 — 90 days**, using
the severities in `docs/incident-management.md`. If we will miss one, we say so and why rather than
going quiet.

## Safe harbour

We will not pursue or support legal action against research conducted in good faith under this
policy: testing only against your own tenant or an account you were given, no access to another
tenant's data, no degradation of service for others, no social engineering of staff or customers, no
physical attacks, and giving us reasonable time to fix before publishing.

If you access another tenant's data by accident, stop, tell us, and delete it. Reporting that
honestly is treated as good faith; continuing to explore is not.

## `security.txt`

Served at `/.well-known/security.txt` and `/security.txt`:

```text
Contact: mailto:security@[DOMAIN]
Encryption: https://[DOMAIN]/.well-known/pgp-key.txt
Policy: https://[DOMAIN]/security
Preferred-Languages: en
Expires: [ISO 8601, refreshed annually]
```

`[DOMAIN]` and the expiry are filled in at deployment; the file is served by the platform, not the
tenant, and carries no tenant data.

## Testing programme

- **Continuous, automated**: dependency advisories and SBOM on every build (F001), the
  permission-negative and cross-tenant lanes in all 71 feature harnesses, the F040 prompt-injection
  corpus, and the F065 enumeration suite with its positive control.
- **Per release**: the security review in the M5 exit criteria — token handling, redaction,
  cross-tenant negatives, and every unauthenticated surface.
- **Annual third-party penetration test**, scoped to the trust boundaries in `docs/threat-model.md`
  section 2, with the authenticated API, the unauthenticated token surfaces, the MCP boundary and
  tenant isolation explicitly in scope. Findings enter the same severity and remediation timetable
  as reported vulnerabilities, and the report's date and scope are available to customers under NDA.
- **Before any first enterprise deployment**, a targeted test of tenant isolation specifically. It is
  the one failure with no recovery, and the one an automated suite is least likely to find.

## What we ask you not to do

Automated scanning that degrades service for other tenants, testing against tenants that are not
yours, and social engineering. Denial of service is out of scope: we know unbounded work is possible,
which is why the limits in `docs/threat-model.md` section 3.5 exist, and demonstrating it costs other
customers their service.
