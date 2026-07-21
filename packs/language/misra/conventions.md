# MISRA — Safety-Critical C/C++ Coding Baseline

> **Pack:** `aspark:misra` · **Category:** language · **Kind:** baseline
> **Activates lens:** none — binds to the Developer/Reviewer via `rules.code.misra`.

> This is a **baseline** scaffold, not the standard. MISRA C:2012 / MISRA C++
> are **licensed** publications; this pack summarizes them at **principle
> level** and reproduces **no numbered MISRA rule text**. It is not a
> substitute for the licensed MISRA standard, and not a certified
> static-analysis toolchain. Every organization chooses its MISRA version, the
> rule subset in scope, and its permitted deviations — override any of this in
> your own `.spark/policy/policy.yaml`; this pack's own `policy.yaml` never sets
> `final: true` on itself.

> **Why `language`, not "automotive"?** MISRA is a C/C++ coding standard, so it
> lives on the `language` axis (next to `java`) — not in any industry bucket.
> That is the concrete reason aSPARK-policy has no "industry" category: an
> industry's footprint (automotive here) cuts *across* the technical axes.

## Conventions

Representative, non-verbatim safety-coding principles. These are aSPARK's own
summary of the *intent* of MISRA-style guidance — consult the licensed standard
for the actual numbered rules.

| Principle | Expectation | Rationale / reference |
|---|---|---|
| MISRA compliance | Safety-relevant C/C++ is written to a MISRA edition the org has adopted. | Establishes a defined, auditable coding-safety baseline; see [MISRA](https://misra.org.uk/). |
| Static analysis in CI | A MISRA-checking static analyser runs in the pipeline, not just on a developer's machine. | Makes conformance a gate, not a good intention; catches violations before merge. |
| No dynamic memory in safety-critical paths | Avoid `malloc`/`new` in code with safety requirements. | Removes a large class of non-deterministic failures (fragmentation, exhaustion) from critical paths. |
| No recursion | Safety-critical code demonstrates bounded stack usage; recursion is avoided. | Unbounded or hard-to-bound stack growth is unacceptable where memory is constrained and deterministic. |
| Defined behaviour only | No reliance on undefined, unspecified or implementation-defined behaviour. | The whole point of MISRA-style guidance: portable, predictable behaviour across toolchains. |
| Documented deviations | Any permitted departure from the standard is recorded with a justification. | Keeps the safety argument honest and auditable rather than silently eroded. |

## How each agent uses this pack

| Phase | Agent | Responsibility under this pack |
|---|---|---|
| `/increment` | Developer | Writes safety-relevant C/C++ to the adopted MISRA principles; wires the static analyser into CI. |
| `/peer-review` | Reviewer | Checks the diff for the principle violations above (dynamic memory / recursion in critical paths, undocumented deviations). |

## Overriding

This is a `baseline` scaffold — the org picks the MISRA version, the in-scope
rule subset, the analyser, and its permitted deviations, in its own
`.spark/policy/policy.yaml` using the licensed standard it holds. Do not mark
these rules `final: true` at the pack level; that lock is only ever applied by
a downstream org or project policy.
