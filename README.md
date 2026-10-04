# aSPARK-policy

> **Enterprise Policy-as-Code for the aSPARK Product Family**
>
> Turn your engineering standards from PDFs and wiki pages into an executable
> policy layer that every aSPARK agent follows — consistently, automatically and
> auditable.

> **Project status: shipped at `v0.3.0` — as a format, a catalog and a
> deterministic resolver, not yet as an enforcement engine.** You can adopt it today: a documented format
> (`FORMAT-REFERENCE.md`), a tested JSON Schema, an installable Python package,
> and 11 real catalog packs including the industry anchors `pci-dss`, `un-r155`
> and `misra` — pulled in as one Git submodule, no Python and no tooling to run
> (see [Install](#install) and [Project Status](#project-status) for the honest
> roadmap). The `aspark-policy` CLI can now **validate** policy files and
> **resolve** the effective policy deterministically — but no agent calls it
> yet: what's still missing is the Facilitator integration in aSPARK Core.
> Until that lands, the policy is readable, inheritable and auditable — but no
> agent picks it up automatically.
> The sibling
> projects [aSPARK](https://github.com/a-lottes/aSPARK) (the delivery loop) and
> [aspark-graph](https://github.com/a-lottes/aSPARK-graph) (the traceability
> graph) exist and work today.

---

## The Problem

Large enterprises rarely fail for lack of talented developers. They fail because
engineering standards are **inconsistently applied** across projects, teams and
technologies.

Every organization already has the documentation:

- Architecture Guidelines
- Secure Coding Standards
- Naming Conventions
- Cloud Standards
- Release Processes
- Compliance Rules
- Review Checklists

But these live as PDFs, wikis or Confluence pages. They are **read occasionally,
interpreted differently and almost never enforced automatically.**

## The Idea

**aSPARK-policy** transforms those documents into an executable policy layer.

The goal is not to replace your engineering standards — it is to make them
**machine-readable, reusable and enforceable.**

- Markdown files **explain** the standards.
- A `policy.yaml` file **activates** them.
- Every aSPARK agent **consumes** the same policy — no duplicated prompts, no
  custom agent modifications.

---

## Install

aSPARK-policy has two audiences, and they install different things — the same
split aSPARK Core makes between using the plugin and hacking on it.

### For projects adopting a policy (the enterprise path)

A policy is not a package you install — it is a **repository you mount**.
Your organization keeps its standards in its own policy repo; each project
pulls it in as a Git submodule at `.spark/policy`, next to the constitution
and the feature artifacts:

```bash
git submodule add \
  git@github.com:company/engineering-policy.git \
  .spark/policy
```

That is the whole install for a consuming project — no Python, no tooling,
nothing to run. See [Integration](#integration-repository-layer-not-another-plugin)
for the full layout and [How agents discover the policy](#how-agents-discover-the-policy)
for what happens next.

> **Honest limitation:** today this mounts the *content* (standards, rules,
> packs). The `aspark-policy` CLI can validate it and compute the effective
> policy (see [Resolving a policy](#resolving-a-policy)), but no agent calls it
> yet — the Facilitator/`/charter` binding in aSPARK Core is still an open
> roadmap item. Mounting now establishes the convention enforcement will
> attach to.

### For contributors (working on the format, schemas or packs)

Requires Python ≥3.11 and [uv](https://docs.astral.sh/uv/). Not yet published
to a package index — work from a checkout of this repository:

```bash
git clone https://github.com/a-lottes/aSPARK-policy.git
cd aSPARK-policy
uv sync --extra dev    # installs into a local .venv
uv run pytest          # 208 tests: schemas, fixtures, all 11 packs, the CLI
uv run aspark-policy validate packs/    # lint the catalog
uv run aspark-policy resolve --imports aspark:owasp,aspark:java
```

What this gets you: the documented format
([`FORMAT-REFERENCE.md`](FORMAT-REFERENCE.md)), three tested JSON Schemas
under `src/aspark_policy/schemas/` you can point any JSON-Schema-aware tool
at, the built-in `aspark:` pack catalog under `packs/`, and the `aspark-policy`
command line (`validate` and `resolve`, see [Resolving a
policy](#resolving-a-policy)). The only runtime dependency is PyYAML. See
[Project Status](#project-status) for what's still open, and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the pack-adding workflow.

> **One-line takeaway:** adopting a policy → one `git submodule add` into
> `.spark/policy`. Contributing to the format → clone + `uv sync`. ✅

---

## Position in the Product Family

```
                    aSPARK Enterprise
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   aSPARK-policy      aspark-graph        aSPARK-insights
    (this repo)                          (early development)
        │                   │                   │
        └───────────────────┼───────────────────┘
                        aSPARK Core
```

| Product              | Status              | Responsibility                                   |
| -------------------- | -------------------- | ------------------------------------------------ |
| **aSPARK Core**      | shipped, `v0.4.0`    | Delivery process, roles, gates, templates        |
| **aspark-graph**     | shipped, `v0.7.0` (on PyPI) | Traceability and engineering knowledge graph     |
| **aSPARK-policy**    | shipped, `v0.3.0` (format + catalog + resolver; enforcement open) | Enterprise engineering standards and governance  |
| **aSPARK-insights**  | early development, `v0.1.0` | Engineering metrics and management dashboards    |

### Separation of concerns

- aSPARK **Core** defines **how** software is built.
- aspark-**graph** knows **what** has been built.
- aSPARK **Policy** defines **which rules** every project must follow.

The core workflow never changes. Only the policy changes.

---

## How aSPARK-policy relates to the Constitution and Lenses

aSPARK already has two mechanisms that look similar to policies. They are not
replaced — they are the **integration points**:

| Mechanism | Scope | Decided by | Lives in |
|---|---|---|---|
| **Policy** (this repo) | organization / business unit | the organization, inherited | `.spark/policy/` (submodule) |
| **Constitution** | one project | the user, via `/charter` | `.spark/constitution.md` |
| **Lenses** | one concern (`security`, `api`, …) | activated by the constitution profile | `lenses/` in aSPARK Core |

The rules of engagement:

1. **The constitution stays the single source of truth for a project.** aSPARK's
   design demands that no phase reads configuration from anywhere else — and
   aSPARK-policy respects that. The policy is not a second source of truth; it
   is an **input to the constitution**.
2. **The Facilitator binds the policy during `/charter`.** If
   `.spark/policy/policy.yaml` exists, the Facilitator reads it, records the
   binding (policy name + pinned version) in `constitution.md`, and translates
   policy rules into constitution principles and constraints. From that moment
   every phase inherits them the normal way — no new plumbing.
3. **Policies can activate lenses.** A policy import like `aspark:security`
   does not duplicate the security lens — it *switches it on* in the project
   profile, exactly as if the user had confirmed it during `/charter`. Policy
   rules that go beyond a lens (e.g. `minimum_reviewers: 2`) become
   constitution constraints.
4. **The user sees every binding.** `/charter` shows what the policy activates
   and where it constrains the project. Organization rules marked `final`
   (see [Inheritance](#policy-inheritance)) cannot be overridden locally; all
   others can be tightened per project.

This keeps the layering clean: **Policy = what the organization requires.
Constitution = what this project decided. Lenses = how a concern is checked.**

---

## How It Works

Instead of writing engineering standards only as documentation, organizations
define them as reusable policy packages.

```
company-engineering-policy/
├── architecture.md
├── security.md
├── testing.md
├── release.md
├── naming.md
├── cloud.md
└── policy.yaml        # activates the standards above
```

### Example `policy.yaml`

```yaml
schema_version: 1          # version of the policy.yaml format itself
                           # (the package version is the Git tag of this repo)

name: ACME Enterprise Policy

imports:
  - aspark:security        # built-in packs use the aspark: prefix
  - aspark:api
  - aspark:library

rules:
  review:
    minimum_reviewers: 2

  qa:
    browser_testing: required

  release:
    requires_qa: true

  architecture:
    adr_required: true

  security:
    id: SEC-014             # stable rule identifier
    severity: blocking      # info | warning | blocking — only blocking stops a gate
    scope: "**/*"           # glob: which files/paths this rule applies to
    check: static           # static | artifact | graph-query
    owasp_top10: true
    final: true             # locked — lower levels cannot weaken this block

  code:
    java:
      version: 21
    typescript:
      strict: true
    python:
      formatter: ruff
```

Every aSPARK agent receives exactly the same policy configuration.

### Import namespaces

| Form | Meaning |
|---|---|
| `aspark:<pack>` | a built-in pack shipped with aSPARK-policy (e.g. `aspark:security`) |
| `company:<pack>` | a pack defined inside the same policy repository |
| `git@github.com:org/repo.git#<tag>` | an external policy repository, pinned to a tag |

---

## Integration: Repository Layer, not another Plugin

aSPARK-policy is deliberately **not** built as another plugin next to aSPARK.
It is a **repository layer** that each project optionally includes — the same
idea behind Maven BOMs, Terraform modules and GitHub Actions: the core stays
small, and organizations ship their own standards.

### Recommended: Git Submodule

Keep policies in their own repository and pull them into each project under
`.spark/policy` — inside the `.spark/` tree that aSPARK already owns, next to
the constitution and the feature artifacts:

```
my-project/
├── src/
├── tests/
└── .spark/
    ├── constitution.md        ← written by /charter, binds the policy
    ├── policy/                ← git submodule → company policy repo
    │   ├── architecture.md
    │   ├── security.md
    │   ├── review.md
    │   └── policy.yaml
    └── <feature-name>/
        ├── spec.md
        └── ...
```

```bash
git submodule add \
  git@github.com:company/engineering-policy.git \
  .spark/policy
```

**Advantages**

- Versionable — the submodule pins an exact commit; upgrades are deliberate
- Changes flow through pull requests
- Rollback possible
- Multiple projects share the same policy

The policy repository becomes the **single source of truth for the
organization's standards** — while each project's constitution remains the
single source of truth for what that project runs with.

```
Project A
Project B   ──►   company-engineering-policy
Project C
```

> aSPARK itself should never contain company-specific knowledge. Organizations
> own their engineering standards.

### How agents discover the policy

There is exactly one discovery path, and it runs through the constitution:

1. `/charter` checks for `.spark/policy/policy.yaml`.
2. If present, the Facilitator resolves imports and inheritance, shows the
   effective rule set to the user, and records the binding in
   `constitution.md`.
3. Every other phase reads the constitution — as it already does today. No
   skill or agent gains a second configuration source.
4. If the submodule commit changes (policy upgrade), the next `/charter` run
   re-binds and shows the diff; until then the constitution honestly reflects
   the version the project was chartered against.

---

## Policy Inheritance

Large organizations rarely have one global standard — they have layers.

```
aSPARK Default
      │
Corporate Standard   →   Contoso
      │
Business Unit        →   Financial Services
      │
Department           →   Payments
      │
Project              →   Payment API
```

### Merge semantics

Predictable rules instead of interpretation:

| Case | Behavior |
|---|---|
| Scalar set on two levels | the **more specific level wins** (project beats department beats corporate) |
| Lists (e.g. approved dependencies) | **merged** across levels; a level may replace instead with `!override` |
| Block marked `final: true` | **locked** — lower levels may add new keys and tighten what a pack declares as *ordered*, never weaken, change or remove anything else (details below) |
| Rule only on one level | inherited unchanged |

Example — corporate locks security, the project tightens review:

```yaml
# corporate/policy.yaml
rules:
  security:
    owasp_top10: true
    final: true            # no BU, department or project can turn this off
  review:
    minimum_reviewers: 1

# payment-api/policy.yaml  (the corporate file sits in the corporate/ subdirectory)
extends: corporate         # a path relative to this file; see "Resolving a policy"
rules:
  review:
    minimum_reviewers: 2   # tightening is always allowed
```

`final` exists for the compliance case: a regulated organization must be able
to guarantee that a rule holds in *every* project, without auditing each one.


### Resolving a policy

`aspark-policy resolve` turns the rules above into code. It is deterministic
and offline: no network, no language model, and the same input always produces
the same bytes. It does not run any check and no agent calls it yet — it
computes the **effective policy** and says where every value came from.

```bash
aspark-policy resolve ./payment-api                          # a project directory
aspark-policy resolve --imports aspark:owasp,aspark:java     # or just some packs
aspark-policy validate packs/                                # schemas + pack integrity
```

**Where it looks.** `resolve <dir>` reads `<dir>/.spark/policy/policy.yaml`,
else `<dir>/policy.yaml`. `<dir>` and `--imports` cannot be combined.

**Layer order** (general to specific; a later layer wins):

1. the imported packs, in listed order — the imports of the whole `extends`
   chain, the most general ancestor's first, de-duplicated by first occurrence;
2. each `extends` ancestor, from the most general to the most specific;
3. the project's own `policy.yaml`, last.

`extends` is a path **relative to the extending file** — a directory holding a
`policy.yaml`, or a `.yaml` file — and must stay inside the project root.
`company:<id>` packs are read from `<policy dir>/packs/<category>/<id>/`.
`aspark:` and `company:` imports resolve; `git@…#tag` imports are **not supported
offline** (exit 2, naming the import).

**Merging.** A scalar (or any other pair that is not mapping+mapping or
list+list) is replaced by the more specific layer. Mappings merge key by key.
Lists concatenate general to specific, keep the **first occurrence** of an
element and drop duplicates by whole-value equality (`true` is not `1`);
`!override` on a list keeps only the more specific list.

**`final`.** `final: true` on any mapping under `rules` locks its whole subtree
for every more specific layer. A more specific layer may

- **add** a key that did not exist, and
- **tighten** a scalar that a *pack* declared as ordered
  (`ordered: {strict_mode: higher-is-stricter}` in the pack's `policy.yaml`;
  `true` is higher than `false`). Only a pack imported by the locking file (or an
  earlier one) counts; a pack that a more specific file imports cannot open its
  own escape.

Everything else at a locked path is a violation — changing or removing a value,
setting `final: false`, replacing the block, appending to a locked list — and the
locked value is kept. All violations are reported in one run. A `baseline` pack
that sets `final` is an error too.

**Output.** One JSON document with sorted keys on stdout. `resolve_format`
(currently **`1.0.0`**) versions its shape; a change to the shape bumps it by
semver. `origins` lists, for every leaf value and every list element, the layer
(`level`, 0 = most general), `pack` (`none` for a local file) and `file` that
supplied it, plus the key path. File paths are relative to the project root (or
to the catalog for `aspark:` packs), so the output does not depend on where the
project lives. Example (the files are in `tests/fixtures/resolve/example/`; the
corporate level is the `corporate/` subdirectory):

<!-- example:resolve:start -->
```json
{
  "input": {
    "imports": [],
    "policy": ".spark/policy/policy.yaml"
  },
  "layers": [
    {
      "file": ".spark/policy/corporate/policy.yaml",
      "kind": "policy",
      "level": 0,
      "name": "Corporate",
      "pack": "none"
    },
    {
      "file": ".spark/policy/policy.yaml",
      "kind": "policy",
      "level": 1,
      "name": "Payment API",
      "pack": "none"
    }
  ],
  "ordered": [],
  "origins": [
    {
      "file": ".spark/policy/policy.yaml",
      "key": "rules.review.minimum_reviewers",
      "level": 1,
      "pack": "none"
    },
    {
      "file": ".spark/policy/corporate/policy.yaml",
      "key": "rules.security.final",
      "level": 0,
      "pack": "none"
    },
    {
      "file": ".spark/policy/corporate/policy.yaml",
      "key": "rules.security.owasp_top10",
      "level": 0,
      "pack": "none"
    }
  ],
  "resolve_format": "1.0.0",
  "rules": {
    "review": {
      "minimum_reviewers": 2
    },
    "security": {
      "final": true,
      "owasp_top10": true
    }
  }
}
```
<!-- example:resolve:end -->

A violation prints nothing on stdout (with `--json`, only the violations) and
one line per violation on stderr: the file that violated, the locked key, and
the file that locked it.

`--json` entries always have `key`, `locked_by`, `violated_by` and `reason`.
For a `final` violation `reason` is one of `removed`, `changed`, `weakened`,
`baseline-final` or `ordered-invalid` and `locked_by` is the locking file. For a
schema error in an input file (also exit 1) `locked_by` is `null`, `key` is the
file-local key (`-` for the file itself) and `reason` is the schema message, so
branch on `locked_by` before switching on `reason`.

<!-- example:violation:start -->
```text
error: .spark/policy/policy.yaml: rules.security.owasp_top10: final lock violated: changed (locked by .spark/policy/corporate/policy.yaml)
```
<!-- example:violation:end -->

`validate` checks a `pack.yaml`, a `policy.yaml`, a pack directory or a whole
tree against the JSON Schemas and checks pack integrity: exactly `pack.yaml`,
one `*.md` and `policy.yaml`; `id` equal to the directory name; no `final` in a
`baseline` pack. Without a path it validates `./packs`.

<!-- example:validate:start -->
```text
$ aspark-policy validate packs/
ok: validated 22 files
```
<!-- example:validate:end -->

**Exit codes and streams.** Results go to stdout, diagnostics to stderr as
`error: <file>: <key>: <reason>`; output never contains colour codes.

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | a policy or validation violation: a `final` lock, a schema error in any loaded file, a broken pack |
| `2` | usage or IO error: a bad flag, a missing file, malformed YAML in `resolve`, an unresolvable import, `extends` outside the root or cyclic |

`resolve` and `validate` are the only public surface of the Python package: the
flags, the exit codes, the `resolve_format` shape, the pack ids and the
`aspark:` namespace and the schemas. The Python modules are private.

---

## Policy Packs

Reusable bundles simplify adoption. A project **combines packs across several
axes** — compliance, architecture, language, framework, cloud, platform — and
no custom agents are required. aSPARK-policy ships a catalog of built-in packs
(the `aspark:` namespace); organizations add their own (`company:`).

### The built-in catalog

Packs are grouped **by category on disk** (for maintainers), but every import
id stays **flat** (for users): `aspark:owasp`, not `aspark:compliance/owasp`.

```
packs/
├── compliance/     iso27001 · owasp · pci-dss · un-r155
├── architecture/   clean-architecture
├── language/       java · misra
├── framework/      spring · react
├── cloud/          aws · azure
└── platform/       (empty — sap is planned, not authored)
```

```yaml
imports:
  - aspark:owasp       # compliance/security
  - aspark:java        # language baseline
  - aspark:spring      # framework baseline
  - aspark:aws         # cloud baseline
  - company:acme-naming
```

### Two kinds of pack

The distinction matters because it decides what may be locked:

| Kind | Meaning | May be `final`? | Examples |
|---|---|---|---|
| **universal** | the same for every organization — an external standard | yes | `owasp`, `iso27001`, `pci-dss`, `un-r155` |
| **baseline** | an opinionated starting point, meant to be overridden per org | no | `java`, `misra`, `spring`, `react`, `aws`, `azure`, `clean-architecture` |

A universal pack (OWASP Top 10) is a fact of the industry, so a corporate level
may lock it. A baseline pack that pins *Java 21* is a **default, not a
standard** — every organization has its own conventions, so a baseline is a
scaffold to tighten, never a `final` constraint.

### What each pack binds to

Some packs switch on an existing aSPARK lens; some are plain rule-sets that feed
an existing agent directly:

| Pack | Category | Kind | Binds to |
|---|---|---|---|
| **owasp** | compliance | universal | existing `security` lens |
| **iso27001** | compliance | universal | Product Owner compliance + several lenses |
| **clean-architecture** | architecture | baseline | Engineering Manager / Reviewer — *no lens today* |
| **java** | language | baseline | Developer (`code.java`) |
| **spring** | framework | baseline | Developer |
| **react** | framework | baseline | Developer + existing `ux` lens |
| **aws** | cloud | baseline | Engineering Manager — *no lens today* |
| **azure** | cloud | baseline | Engineering Manager — *no lens today* |
| **sap** | platform | baseline | Engineering Manager / Developer — *planned, not authored yet* |
| **pci-dss** | compliance | universal | Product Owner compliance + existing `security` lens |
| **un-r155** | compliance | universal | Product Owner compliance + existing `security` lens |
| **misra** | language | baseline | Developer (`code.misra`) |

> **This catalog reveals two gaps in aSPARK Core:** there is no `cloud` lens and
> no `architecture` lens yet. Until they exist, `aws`/`azure`/`clean-architecture`
> apply as plain constitution constraints on the existing agents. Adding those
> two lenses to aSPARK Core is the natural follow-up (tracked in
> [Project Status](#project-status)).

### Anatomy of a pack

```
packs/compliance/owasp/
├── pack.yaml       # metadata: id, category, kind, version, maps_to_lens, summary, references
├── security.md     # the human-readable standard
└── policy.yaml     # the rule fragment this pack contributes
```

When two packs set the same key (two frameworks, two clouds), the
[merge and `final` semantics](#merge-semantics) resolve it deterministically —
so `pack.yaml` makes each pack's category and kind explicit rather than leaving
conflicts to interpretation.

---

## Agent Integration

The policy engine does not create new roles. All **seven** existing aSPARK
agents consume the same policies, each in the phase they own:

| Command | Agent | Uses the policy to … |
|---|---|---|
| `/charter` | 📜 **Facilitator** | Bind the policy into the constitution; resolve imports, inheritance and lens activation; show the user the effective rule set |
| `/story-time` | 🧭 **Product Owner** | Check mandatory NFRs, compliance, legal and privacy requirements |
| `/look-and-feel` | 🎨 **Designer** | Apply accessibility standards, design-system and UX policies |
| `/sprint-plan` | 🏗️ **Engineering Manager** | Check architecture principles, approved frameworks, dependency & cloud rules |
| `/increment` | 💻 **Developer** | Apply coding conventions, language standards, testing & documentation rules |
| `/peer-review` | 🔍 **Reviewer** | Enforce architecture, security, dependency restrictions, clean code |
| `/demo-day` | 🧪 **QA Tester** | Verify regulatory, accessibility, security and operational requirements |
| `/go-live` | 🚀 **Release Manager** | Block releases when required policies are missing |

### Release gate example

```
Release blocked

✔ Review complete
✔ QA passed
✘ Security approval missing            (policy: ACME Enterprise → security)
✘ Architecture Decision Record missing (policy: ACME Enterprise → architecture.adr_required)
```

### Policy violations become explicit

```
Policy Violations

✘ Architecture Decision Record missing
✘ Public API not versioned
✘ Logging standard violated
✘ Naming convention violated
✘ Required NFR missing
✘ Dependency not approved
```

Policies become quality gates instead of advisory documents — and every
violation names the policy and rule it comes from, which is what makes the
trail auditable.

---

## Relationship with aspark-graph (planned)

[aspark-graph](https://github.com/a-lottes/aSPARK-graph) today models code
(`File`, `Class`, `Function`) and delivery artifacts (`Feature`, `Story`,
`AcceptanceCriterion`, `Task`, `Finding`, `QACheck`) — **it has no policy
layer yet**. Extending it is the natural next step, not a current capability:

- A `Policy` / `PolicyViolation` node type would let violations join the graph
  the same way review findings (`Finding`) already do.
- `gate_health` — the existing query that answers *"are this feature's ACs
  covered and passing?"* — is the natural anchor point for policy gates.

Once that exists, the two together can answer:

- Which stories violate architecture policy?
- Which NFRs required by policy are missing?
- Which release is blocked by governance, and by exactly which rule?
- Which code changes require additional approvals?

The policy engine defines the rules; the graph verifies traceability.

---

## Benefits for Enterprises

| Benefit               | What it means                                              |
| --------------------- | ---------------------------------------------------------- |
| **Consistency**       | Every project follows the same engineering standards       |
| **Reuse**             | Engineering knowledge is written once, reused everywhere   |
| **Compliance**        | Policies become enforceable instead of advisory            |
| **Lower onboarding**  | New teams automatically inherit company standards          |
| **Auditability**      | Every decision traces back to an explicit policy           |
| **Scalability**       | Thousands of projects can share one engineering standard   |

---

## Project Status

aSPARK-policy is **shipped at `v0.3.0` as a format, a catalog and a deterministic
resolver**; agent enforcement is the open half. Not yet on PyPI — adoption is by Git submodule, which is the
intended path anyway. This README is the design document; it always reflects the
current state honestly.

- [x] Vision, positioning in the product family, separation of concerns
- [x] Integration design: repository layer via Git submodule at `.spark/policy`
- [x] Constitution binding designed — `/charter` as the single discovery path,
      no second source of truth
- [x] Inheritance semantics defined — specific-wins, list merging, `final` lock
      — and now executable: `aspark-policy resolve` implements them
      deterministically (see [Resolving a policy](#resolving-a-policy))
- [x] Pack catalog designed — categories, universal vs. baseline, per-pack
      lens binding; `owasp` scaffolded under `packs/` as the reference pack
- [x] `policy.yaml` / `pack.yaml` schema (JSON Schema, draft 2020-12) —
      formal, validatable definition under `src/aspark_policy/schemas/`;
      validates all four format fixtures and all 11 shipped packs clean
- [x] Rule anatomy — optional `id`/`severity`/`scope`/`check` on any rule
      block, aligned with the aSPARK Enterprise Architecture Handbook's
      vision; `check: graph-query` is structural only until aSPARK-graph
      integrates
- [x] `aspark-policy validate` and `aspark-policy resolve` CLI — lint a policy
      repo standalone and in CI, and compute the effective policy with the origin
      of every value. This is a deterministic resolver, **not** an enforcement
      engine: it runs no checks, and no agent calls it yet
- [ ] Facilitator/`/charter` integration in aSPARK Core — read, resolve and
      bind `.spark/policy/policy.yaml`
- [ ] Fill the built-in catalog — 11 packs are authored: `owasp`, `iso27001`,
      `pci-dss`, `un-r155`, `clean-architecture`, `java`, `misra`, `spring`,
      `react`, `aws`, `azure`. Only `sap` remains (excluded so far: no verified
      SAP source material to author credibly), so the `platform/` axis is
      currently empty
- [ ] New lenses in aSPARK Core — `cloud` and `architecture`, so `aws`/`azure`/
      `clean-architecture` bind to a lens instead of plain constraints
- [ ] Per-phase policy enforcement wired into the remaining seven skills
- [ ] Policy node types in aspark-graph (`Policy`, `PolicyViolation`) +
      `gate_health` extension
- [ ] Reference policy repository as a template (`company-engineering-policy`)

## Changelog

### 0.3.0

- **Added** the `aspark-policy` command line: `resolve` computes the effective
  policy of a project directory or an import list as byte-stable JSON
  (`resolve_format` `1.0.0`) with the origin of every value, and fails with exit
  code 1 on a `final` violation; `validate` checks schema conformance and pack
  integrity.
- **Added** `ordered` — a reserved, pack-only rule key declaring which direction
  is stricter for a scalar, so a `final` value can be tightened.
- **Added** the pack catalog as package data in the wheel, and a CI workflow that
  runs the tests on Linux, macOS and Windows.
- **Changed** the runtime now depends on PyYAML (`>=6.0`). The schemas, all pack
  ids and all pack content are unchanged.
- **Documented** what the earlier text left open: layer order, what tighten and
  weaken mean, list de-duplication, how `extends` and `company:` imports find
  their files. `extends` is a path relative to the extending file; `git@…#tag`
  imports are not supported offline.

### 0.2.0

- **Added** the `pci-dss`, `un-r155` and `misra` packs (11 packs in the catalog).

### 0.1.0

- First release: the documented format, three JSON Schemas and the first catalog
  packs.

## Future Extensions

Enterprise modules can be independently versioned and maintained:

- ISO 27001 Policy Pack
- OWASP Policy Pack
- NIST Policy Pack
- Automotive SPICE Pack
- Medical Device Pack
- GDPR Pack
- Internal Corporate Packs

---

## Vision

aSPARK-policy transforms engineering governance from static documentation into
executable organizational knowledge. Instead of teaching every engineer and
every AI agent how a company develops software, organizations publish their
standards once as reusable policy packages.

Every project, every repository and every aSPARK agent then follows the same
rules automatically — a scalable, deterministic and auditable software
engineering platform that combines delivery process, knowledge management and
enterprise governance while minimizing operational overhead, reducing costs and
consistently delivering high-quality software.

---

## License

[MIT](LICENSE) © 2026 Andreas Lottes. Part of the aSPARK product family.
