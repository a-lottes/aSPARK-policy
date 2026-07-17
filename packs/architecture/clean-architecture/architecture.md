# Clean Architecture — Architecture Baseline

> **Pack:** `aspark:clean-architecture` · **Category:** architecture · **Kind:** baseline
> **Activates lens:** none — aSPARK Core has no `architecture` lens yet. This
> pack's rules apply as **plain constitution constraints** on the Engineering
> Manager and Reviewer until one exists.

> This is a **baseline** scaffold, not a universal mandate. Architecture
> conventions vary by project and organization; this pack is a credible
> starting point based on Robert C. Martin's Clean Architecture principle
> set, not a rule every project must accept unchanged. Override any of it in
> your own `.spark/policy/policy.yaml`.

## Conventions

| Area | Rule | Rationale / reference |
|---|---|---|
| Dependency rule | Source-code dependencies point only inward, toward higher-level policy — never outward toward frameworks or infrastructure. | The core principle of [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html): business rules must not depend on delivery mechanisms. |
| Layering | Entities → Use Cases → Interface Adapters → Frameworks/Drivers. | Keeps business logic testable without a database, a UI, or a web framework present. |
| ADR requirement | Architecture decisions are recorded with their rejected alternatives, not just the chosen approach. | Mirrors aSPARK's own `/sprint-plan` mini-ADR practice — a decision without alternatives is a guess. |
| Framework isolation | Frameworks and drivers are plugins to the business rules, never the reverse. | Prevents a framework upgrade or swap from requiring a rewrite of business logic. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/sprint-plan` | Engineering Manager | Applies the dependency rule and layering when making the architecture decision; the ADR requirement is already aSPARK's own practice. |
| `/peer-review` | Reviewer | Checks the diff for dependency-rule violations (e.g. a use case importing a framework class directly). |

**Note:** since no `architecture` lens exists yet in aSPARK Core, these checks
are performed as direct constitution constraints by the agents above, not
through a lens — the same fallback the README already documents for this gap.

## Overriding

This is a `baseline` scaffold — override its specifics in your own
`.spark/policy/policy.yaml`. This pack's own `policy.yaml` never sets
`final: true` on itself.
