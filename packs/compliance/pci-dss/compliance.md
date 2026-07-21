# PCI-DSS — Payment Card Industry Data Security Standard

> **Pack:** `aspark:pci-dss` · **Category:** compliance · **Kind:** universal
> **Activates lens:** `security` — PCI-DSS is a security-technical standard, so
> it switches on aSPARK Core's existing `security` lens (like `owasp`).

> ⚠️ **Disclaimer — read before relying on this pack.** This pack is
> **aSPARK's own summary interpretation** of PCI-DSS v4.0, written to make its
> 12 requirements checkable inside the SPARK loop. It is **not a certified PCI
> compliance artifact**, is **not a QSA (Qualified Security Assessor)
> assessment**, and **does not substitute for a formal PCI-DSS audit,
> Self-Assessment Questionnaire (SAQ) or Report on Compliance (RoC)**. An
> organization handling cardholder data and pursuing actual PCI-DSS compliance
> must engage a QSA and its own compliance function — this pack only helps a
> development team keep the standard's engineering-relevant requirements from
> being silently missed. It summarizes requirement titles and intent; it does
> not reproduce the licensed sub-requirement text of the standard.

This pack is a **universal** standard — the same for every organization
handling payment card data — so a corporate policy level may lock it with
`final: true`. Importing `aspark:pci-dss` activates the `security` lens; its
rules (see [`policy.yaml`](policy.yaml)) are enforced by the agents below.

## The controls

Each row maps to one real PCI-DSS v4.0 requirement. The standard is structured
as **12 requirements under 6 goals**; this pack cites all 12 at requirement
level (not the licensed sub-requirement detail).

| Req. | Control (goal) | What the project must do |
|---|---|---|
| Req. 1 | Install and maintain network security controls *(Build & Maintain a Secure Network)* | Network security controls (firewalls, equivalent) govern traffic to and from the cardholder data environment. |
| Req. 2 | Apply secure configurations to all system components *(Build & Maintain a Secure Network)* | No vendor defaults; systems are hardened to a documented secure configuration standard. |
| Req. 3 | Protect stored account data *(Protect Account Data)* | Stored account data is minimized, and what is stored is rendered unreadable (e.g. strong encryption, truncation). |
| Req. 4 | Protect cardholder data with strong cryptography during transmission *(Protect Account Data)* | Cardholder data is encrypted with strong cryptography whenever transmitted over open, public networks. |
| Req. 5 | Protect all systems and networks from malicious software *(Vulnerability Management)* | Anti-malware protection is deployed and kept current where applicable. |
| Req. 6 | Develop and maintain secure systems and software *(Vulnerability Management)* | Secure development practices are applied and known vulnerabilities are patched on a defined timeline. |
| Req. 7 | Restrict access by business need to know *(Access Control)* | Access to system components and cardholder data is granted only on a documented need-to-know basis, deny by default. |
| Req. 8 | Identify users and authenticate access *(Access Control)* | Every user is uniquely identified and strongly authenticated (including multi-factor where required). |
| Req. 9 | Restrict physical access to cardholder data *(Access Control)* | Physical access to systems and media holding cardholder data is controlled and logged. |
| Req. 10 | Log and monitor all access *(Monitor & Test)* | Access to system components and cardholder data is logged, and the logs are monitored and retained. |
| Req. 11 | Test security of systems and networks regularly *(Monitor & Test)* | Vulnerability scans and penetration tests are run on a defined cadence and findings are remediated. |
| Req. 12 | Support information security with organizational policies *(Security Policy)* | An information security policy and program exist, are maintained, and are communicated. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/charter` | Facilitator | Binds this pack into the constitution and activates the `security` lens for the project. |
| `/story-time` | Product Owner | Records the applicable requirements (esp. Req. 3, 4, 12) as non-functional requirements (`NFR-`). |
| `/sprint-plan` | Engineering Manager | Ensures the architecture satisfies network segmentation (Req. 1), secure configuration (Req. 2) and access control (Req. 7–8). |
| `/increment` | Developer | Applies secure software development (Req. 6), cryptography (Req. 3–4) and authentication (Req. 8) in the code. |
| `/peer-review` | Reviewer | Enforces the diff-observable requirements — stored-data protection, transmission encryption, secure coding, access control. |
| `/demo-day` | QA Tester | Verifies observable controls (authentication behaviour, transport encryption, logging). |
| `/go-live` | Release Manager | Blocks release while a required control (e.g. `test_security_regularly`, `log_and_monitor`) is unmet. |

## Overriding

As a `universal` pack, tightening is always allowed; a corporate policy level
may mark this block `final: true` to guarantee every project handling
cardholder data carries these requirements (this pack's own `policy.yaml` never
sets `final` itself). A project may add controls beyond this requirement-level
subset — down to the specific sub-requirements its SAQ/RoC scope demands — in
its own `.spark/policy/policy.yaml`.
