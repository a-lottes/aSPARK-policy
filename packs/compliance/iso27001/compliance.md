# ISO/IEC 27001 — Information Security Management Controls

> **Pack:** `aspark:iso27001` · **Category:** compliance · **Kind:** universal
> **Activates lens:** none — no existing aSPARK Core lens covers ISO 27001's
> full organizational/people/physical/technological breadth (see `pack.yaml`).
> Applies as Product-Owner-led constitution constraints instead.

> ⚠️ **Disclaimer — read before relying on this pack.** This pack is
> **aSPARK's own summary interpretation** of ISO/IEC 27001:2022 Annex A,
> written to make a subset of its controls checkable inside the SPARK loop.
> It is **not a certified compliance artifact**, has not been reviewed by a
> certified ISO 27001 lead auditor, and **does not substitute for a formal
> ISO 27001 audit or certification process**. An organization pursuing actual
> ISO 27001 certification must engage a qualified auditor and its own
> compliance function — this pack only helps a development team keep a subset
> of the standard's engineering-relevant controls from being silently missed.

This pack is a **universal** standard — the same for every organization — so a
corporate policy level may lock it with `final: true`. Importing
`aspark:iso27001` does not activate an existing lens (unlike `aspark:owasp`);
instead its rules (see [`policy.yaml`](policy.yaml)) apply as constitution
constraints that the Product Owner and other agents check directly.

## The controls

Each row maps to one real ISO/IEC 27001:2022 Annex A clause. Controls span all
four Annex A themes (Organizational A.5, People A.6, Physical A.7,
Technological A.8) to demonstrate the standard's actual breadth — this is a
representative subset (10 of 93 total Annex A controls), not the full standard.

| Clause | Control | What the project must do |
|---|---|---|
| A.5.1 | Policies for information security | An information security policy exists, is approved, and is recorded as a project NFR. |
| A.5.9 | Inventory of information and other associated assets | Information assets (data stores, credentials, third-party services) are identified and tracked. |
| A.5.15 | Access control | Access to systems and data is granted on a documented, need-based rule, not by default. |
| A.5.23 | Information security for use of cloud services | Cloud services used by the project have their security responsibilities and configuration explicitly owned. |
| A.5.31 | Legal, statutory, regulatory and contractual requirements | Applicable legal/regulatory/contractual security obligations are identified and tracked as NFRs. |
| A.6.3 | Information security awareness, education and training | Contributors have access to security awareness material relevant to their role in the project. |
| A.7.9 | Security of assets off-premises | Devices and data taken outside the primary work location (laptops, backups) have documented protection. |
| A.8.8 | Management of technical vulnerabilities | Known vulnerabilities in dependencies and infrastructure are tracked and remediated on a defined timeline. |
| A.8.24 | Use of cryptography | Cryptographic controls (encryption at rest/in transit, key management) are used where sensitive data requires them. |
| A.8.28 | Secure coding | Secure coding practices are applied and checked on the diff, not left to individual discretion. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/charter` | Facilitator | Binds this pack into the constitution as a compliance-scope constraint (no lens to activate). |
| `/story-time` | Product Owner | Records the applicable controls (A.5.1, A.5.31, and others relevant to the feature) as non-functional requirements (`NFR-`). |
| `/sprint-plan` | Engineering Manager | Ensures the architecture can satisfy access-control (A.5.15) and cloud-service-ownership (A.5.23) expectations. |
| `/increment` | Developer | Applies secure coding (A.8.28) and cryptography (A.8.24) controls in the code itself. |
| `/peer-review` | Reviewer | Enforces the controls that are diff-observable — access control, cryptography use, secure coding, vulnerability handling. |
| `/demo-day` | QA Tester | Verifies the controls that are observable in the running system (e.g. access control behavior). |
| `/go-live` | Release Manager | Blocks release while a required control (e.g. `vulnerability_management`) is unmet. |

## Overriding

As a `universal` pack, tightening is always allowed; a corporate policy level
may mark this block `final: true` to guarantee every project under it carries
these controls (this pack's own `policy.yaml` never sets `final` itself — only
a downstream org/project policy does). A project may add controls beyond this
representative subset in its own `.spark/policy/policy.yaml`.
