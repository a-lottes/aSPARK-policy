# AWS — Cloud Baseline

> **Pack:** `aspark:aws` · **Category:** cloud · **Kind:** baseline
> **Activates lens:** none — aSPARK Core has no `cloud` lens yet. This pack's
> rules apply as **plain constitution constraints** on the Engineering
> Manager until one exists.

> This is a **baseline** scaffold, not a universal mandate. Cloud conventions
> vary by organization, workload, and compliance context; this pack is a
> credible starting point drawn from AWS's own published guidance, not a rule
> every project must accept unchanged. Override any of it in your own
> `.spark/policy/policy.yaml`.

## Conventions

| Area | Rule | Rationale / reference |
|---|---|---|
| Identity | IAM roles are scoped to the minimum permissions a service actually needs (least privilege). | Core [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/) security pillar practice; limits blast radius of a compromised credential. |
| Encryption at rest | Storage services (S3, EBS, RDS) have encryption enabled by default. | Protects data at rest without depending on every engineer remembering to enable it per-resource. |
| Tagging | Every resource carries an owner tag and a cost-center tag. | Enables cost attribution and makes an orphaned resource traceable to a team. |
| Network exposure | No security group is open to `0.0.0.0/0` on a non-public-facing port. | Prevents accidental exposure of internal services (databases, admin ports) to the public internet. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/sprint-plan` | Engineering Manager | Applies the identity, encryption, and network-exposure conventions when designing the cloud architecture. |

**Note:** since no `cloud` lens exists yet in aSPARK Core, these checks are
performed as direct constitution constraints by the Engineering Manager, not
through a lens — the same fallback the README already documents for this gap.

## Overriding

This is a `baseline` scaffold — override its specifics in your own
`.spark/policy/policy.yaml`. This pack's own `policy.yaml` never sets
`final: true` on itself.
