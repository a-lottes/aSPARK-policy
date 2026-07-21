# UN R155 — Vehicle Cyber Security Management System (WP.29)

> **Pack:** `aspark:un-r155` · **Category:** compliance · **Kind:** universal
> **Activates lens:** `security` — UN R155's CSMS is security-technical
> governance, so it switches on aSPARK Core's existing `security` lens.

> ⚠️ **Disclaimer — read before relying on this pack.** This pack is
> **aSPARK's own summary interpretation** of UN Regulation No. 155 (WP.29),
> written to make its Cyber Security Management System (CSMS) structure
> checkable inside the SPARK loop. It is **not a type-approval artifact**, has
> not been reviewed by a technical service or approval authority, and **does
> not substitute for a formal WP.29 assessment or vehicle type approval**. An
> organization seeking actual UN R155 type approval must engage the relevant
> approval authority and its own cyber security function.
>
> **Related standard, not reproduced:** ISO/SAE 21434 ("Road vehicles —
> Cybersecurity engineering") is the engineering standard commonly used to
> *implement* a CSMS. It is a **licensed** standard; this pack names it only as
> the related standard and reproduces **none** of its clause content. This pack
> is anchored deliberately on the **public** UN R155 regulation instead.

This pack is a **universal** regulation — the same for every organization
type-approving vehicles in an R155 market — so a corporate policy level may
lock it with `final: true`. Importing `aspark:un-r155` activates the `security`
lens; its rules (see [`policy.yaml`](policy.yaml)) are enforced by the agents
below.

## The controls

Each row maps to a real structural provision of UN R155's CSMS — the
regulation requires a managed cyber security process across the vehicle
lifecycle (development, production, post-production).

| R155 provision | Control | What the project must do |
|---|---|---|
| CSMS in place | A Cyber Security Management System governs the vehicle type | A defined, auditable process manages cyber security across the lifecycle, not ad hoc. |
| Risk identification | Cyber security risks are identified | Threats and risks to the vehicle and its systems are systematically identified. |
| Risk assessment & treatment | Risks are assessed and treated | Identified risks are assessed and either mitigated or explicitly accepted with justification. |
| Security by design | Treatment is applied in design | Risk treatments are designed into the vehicle and its systems, not bolted on later. |
| Supplier management | Suppliers' responsibilities are managed | Cyber security responsibilities of suppliers and third parties are defined and evidenced. |
| Monitoring & detection | Field monitoring exists | Attacks and newly discovered vulnerabilities are monitored and detected in the fleet. |
| Incident response | Response capability exists | A capability to respond to detected cyber attacks and incidents is maintained. |
| Post-production updates | Lifecycle vulnerability management | Vulnerabilities are managed and remediated after production, over the vehicle's life. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/charter` | Facilitator | Binds this pack into the constitution and activates the `security` lens for the project. |
| `/story-time` | Product Owner | Records the CSMS provisions (risk management, incident response, post-production updates) as non-functional requirements (`NFR-`). |
| `/sprint-plan` | Engineering Manager | Ensures the architecture reflects security-by-design and a monitoring/detection capability. |
| `/increment` | Developer | Implements the risk treatments and the update/patch mechanism in the code. |
| `/peer-review` | Reviewer | Enforces the diff-observable controls — security-by-design decisions, supplier-boundary handling, update integrity. |
| `/demo-day` | QA Tester | Verifies observable controls (update mechanism behaviour, monitoring hooks). |
| `/go-live` | Release Manager | Blocks release while a required control (e.g. `incident_response`, `post_production_updates`) is unmet. |

## Overriding

As a `universal` regulation pack, tightening is always allowed; a corporate
policy level may mark this block `final: true` to guarantee every vehicle
project carries these CSMS provisions (this pack's own `policy.yaml` never sets
`final` itself). A project may add the specific engineering controls its
ISO/SAE 21434 implementation demands — in its own `.spark/policy/policy.yaml`,
using the licensed standard it holds, not this summary.
