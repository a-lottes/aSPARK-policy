# OWASP — Web Application Security Standard

> **Pack:** `aspark:owasp` · **Category:** compliance · **Kind:** universal
> **Activates lens:** `security`

This pack makes the [OWASP Top 10 (2021)](https://owasp.org/Top10/) an
enforceable part of the delivery loop. It is a **universal** standard — the same
for every organization — so a corporate policy level may lock it with
`final: true`.

Importing `aspark:owasp` switches on aSPARK Core's existing **`security` lens**;
it does not create a new role. The rules in [`policy.yaml`](policy.yaml) are
what the existing agents check, each in the phase they own.

## The controls

Each control maps to one OWASP Top 10 (2021) category.

| # | Category | What the project must do |
|---|---|---|
| A01 | Broken Access Control | Every endpoint and resource enforces authorization; deny by default. |
| A02 | Cryptographic Failures | Sensitive data encrypted in transit and at rest; no weak or home-grown crypto. |
| A03 | Injection | All untrusted input is parameterized/escaped; no string-built queries or commands. |
| A04 | Insecure Design | Security is considered at design time — threat model for sensitive flows. |
| A05 | Security Misconfiguration | Hardened defaults; no debug endpoints, default credentials or verbose errors in production. |
| A06 | Vulnerable & Outdated Components | Dependencies scanned; no shipped component with a known CVE. |
| A07 | Identification & Auth Failures | Strong authentication lifecycle — session handling, rate limiting, credential storage. |
| A08 | Software & Data Integrity Failures | Verify integrity of updates, CI artifacts and deserialized data. |
| A09 | Security Logging & Monitoring Failures | Security-relevant events are logged; logs are reviewable and free of secrets. |
| A10 | Server-Side Request Forgery | Outbound requests to user-supplied URLs are validated and restricted. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/story-time` | Product Owner | Records OWASP compliance as a non-functional requirement (`NFR-`). |
| `/sprint-plan` | Engineering Manager | Chooses an architecture that can satisfy the controls; flags risky flows. |
| `/increment` | Developer | Writes code that meets the controls — parameterized queries, no committed secrets. |
| `/peer-review` | Reviewer | Enforces the controls on the diff via the `security` lens. |
| `/demo-day` | QA Tester | Verifies the observable controls in the browser (auth, headers, error handling). |
| `/go-live` | Release Manager | Blocks release while `dependency_scanning` or any required control is unmet. |

## Overriding

As a universal pack, tightening is always allowed; weakening is not once a level
marks it `final`. A project may add stricter rules (e.g. a specific dependency
scanner or a shorter session lifetime) on top of this baseline in its own
`.spark/policy/policy.yaml`.
