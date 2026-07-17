# React — Framework Baseline

> **Pack:** `aspark:react` · **Category:** framework · **Kind:** baseline
> **Activates lens:** `ux` — the one baseline pack that binds to an existing
> aSPARK Core lens, since React's accessibility and interaction-state
> concerns are exactly what the `ux` lens already checks.

> This is a **baseline** scaffold, not a universal mandate. Front-end
> conventions are especially contested across organizations; this pack is a
> credible starting point covering component structure, state management,
> and the accessibility/state expectations that feed the `ux` lens — not a
> rule every project must accept unchanged. Override any of it in your own
> `.spark/policy/policy.yaml`.

## Conventions

| Area | Rule | Rationale / reference |
|---|---|---|
| Component structure | One component per file; co-locate its styles and tests. | Keeps a component and everything that verifies or styles it discoverable in one place; see the [React docs](https://react.dev/learn). |
| State management | Local component state by default; lift state to a shared store only once 2+ components need it. | Avoids premature global state, which is harder to trace and test than local state. |
| Accessibility | Every interactive element has a discernible accessible name (label, `aria-label`, or visible text). | Directly feeds the `ux` lens's accessibility checks — an unlabeled interactive element fails both this pack and that lens. |
| Loading / error states | Every view backed by async data has an explicit loading, empty, and error state — never a blank screen. | Directly feeds the `ux` lens's "every empty/loading/error state" check (see the aSPARK README's lens table). |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/increment` | Developer | Structures components per-file and applies the state-management and accessibility conventions. |
| `/look-and-feel` | Designer | Uses the `ux` lens (activated by this pack) to check accessibility and empty/loading/error states against the spec. |
| `/demo-day` | QA Tester | Verifies the `ux`-lens-observable behaviors (accessible names, empty/loading/error states) in the running app. |
| `/peer-review` | Reviewer | Checks the diff for component-structure and state-management convention adherence. |

## Overriding

This is a `baseline` scaffold — override its specifics in your own
`.spark/policy/policy.yaml`. This pack's own `policy.yaml` never sets
`final: true` on itself.
