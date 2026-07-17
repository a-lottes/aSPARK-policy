# Spring Framework — Framework Baseline

> **Pack:** `aspark:spring` · **Category:** framework · **Kind:** baseline
> **Activates lens:** none — binds to the Developer via `rules.code.spring`.

> This is a **baseline** scaffold, not a universal mandate. Spring
> conventions vary widely by organization and team; this pack is a credible
> starting point, not a rule every project must accept unchanged. Override
> any of it in your own `.spark/policy/policy.yaml`.

## Conventions

| Area | Rule | Rationale / reference |
|---|---|---|
| Layering | Controller → Service → Repository; a controller never calls a repository directly. | Keeps business logic out of controllers and testable independent of HTTP; standard [Spring layered architecture](https://docs.spring.io/spring-framework/reference/). |
| Dependency injection | Prefer constructor injection over field injection. | Makes dependencies explicit and required at construction, enabling immutability and easier testing. |
| Configuration & secrets | Externalize configuration via Spring Config or a secrets manager; never commit secrets to `application.yml`. | Prevents credential leakage into version control. |
| Transaction boundaries | `@Transactional` lives on service methods, not controllers or repositories. | Keeps the transaction scope aligned with the business operation, not the HTTP request or the data-access call. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/increment` | Developer | Structures code along the controller/service/repository layering and applies constructor injection. |
| `/peer-review` | Reviewer | Checks the diff for layering violations, field injection, and committed secrets. |

## Overriding

This is a `baseline` scaffold — override its specifics in your own
`.spark/policy/policy.yaml`. This pack's own `policy.yaml` never sets
`final: true` on itself.
