# Java — Language Baseline

> **Pack:** `aspark:java` · **Category:** language · **Kind:** baseline
> **Activates lens:** none — binds to the Developer via `rules.code.java`.

> This is a **baseline** scaffold, not a universal mandate. Every organization
> has its own Java conventions; this pack exists to give a new project a
> credible starting point, not a rule every project must accept unchanged.
> Override any of it in your own `.spark/policy/policy.yaml` — this pack's own
> `policy.yaml` never sets `final: true` on itself.

## Conventions

| Area | Rule | Rationale / reference |
|---|---|---|
| Language version | Target Java 21 (LTS) as the baseline. | Java 21 is the current LTS release; override to your org's actual supported version. |
| Formatting | Use `google-java-format` (or an equivalent enforced formatter). | Removes formatting bikeshedding from review; [google-java-format](https://github.com/google/google-java-format). |
| Dependency management | Pick one of Maven or Gradle per project and be consistent within it. | Mixing build tools in one codebase adds onboarding cost with no benefit. |
| Null handling | Prefer `Optional<T>` over returning `null` from public APIs. | Makes "may be absent" explicit in the type signature; see the [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html). |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/increment` | Developer | Writes code against the pinned Java version and formatter. |
| `/peer-review` | Reviewer | Checks the diff for formatting and null-handling convention adherence. |

## Overriding

This is a `baseline` scaffold — override its specifics (the version, the
formatter, the build tool) in your own `.spark/policy/policy.yaml`. Do not mark
any of these rules `final: true` at the pack level; that lock is only ever
applied by a downstream org or project policy that has decided its own
convention should not be overridden further.
