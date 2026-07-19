# Format Reference — `policy.yaml` and `pack.yaml`

> **This is the authoritative, human-readable definition of the two file
> formats** that aSPARK-policy uses. The README explains the *concepts*; this
> document is the *contract* every pack, the future JSON Schema, and the future
> `aspark-policy validate` CLI are built against.
>
> **Source of truth on conflict:** the [README](README.md) owns the *design*
> (what the fields mean); this file owns the *shape* (which keys exist and their
> value types). If the two ever disagree, that is a defect to fix, not a choice
> — see NFR-2 in the spec.
>
> This is a **prose** reference. The machine-readable JSON Schema is a separate,
> later increment; ready-made pass/fail fixtures already live in
> [`tests/fixtures/format/`](tests/fixtures/format/) so that increment has
> targets to validate against.

---

## 1. `policy.yaml`

The file a project or an organization level authors to **activate and configure**
standards. One per policy level (corporate, business-unit, project, …).

| Key | Required | Type / shape | Meaning |
|---|---|---|---|
| `schema_version` | **required** | integer | Version of the `policy.yaml` *format* itself (currently `1`). Not the package version — that is the Git tag of the policy repo. |
| `name` | **required** | string | Human-readable name of this policy, e.g. `"ACME Enterprise Policy"`. |
| `extends` | optional | string | The parent policy level this one inherits from (used in multi-level inheritance). Omitted at the root level. |
| `imports` | optional | list of import strings | Packs this policy pulls in. See [§3 Import namespaces](#3-import-namespaces). |
| `rules` | optional | mapping | The rule tree. Keys are rule domains (`review`, `security`, `architecture`, `code`, …); values are domain-specific settings. See [§1.1](#11-the-rules-tree). |

A `policy.yaml` with only `schema_version` + `name` is valid (it activates
nothing). At least one of `imports` or `rules` is expected in practice, but
neither is structurally required.

### 1.1 The `rules` tree

`rules` is an open mapping — its shape depends on the domains a policy uses.
Two structural conventions apply to **any** rule block:

- **`final: true`** — a boolean marker inside a rule block that **locks** it:
  lower inheritance levels may tighten it but never weaken or remove it. Only
  meaningful on a pack of `kind: universal` or an org-authored rule (see the
  README's inheritance semantics). A `baseline` pack's rules must **not** be
  `final`.
- **`!override`** — a YAML tag on a list value that **replaces** the inherited
  list instead of merging into it. Without it, lists merge across levels.

Scalar values on two levels resolve **more-specific-wins** (project beats
department beats corporate). This document defines the *shape*; the *resolution
semantics* are documented in the README and will be executed by a later
increment — `foundation` ships neither a resolver nor a validator.

#### Rule anatomy — optional, richer identification

A rule block may additionally carry four optional keys, siblings of `final`,
identifying and classifying the rule itself rather than its content:

| Key | Type / shape | Meaning |
|---|---|---|
| `id` | string | A stable rule identifier, e.g. `SEC-014`. Not required — a rule block with no `id` is still valid — but recommended once a rule is referenced elsewhere (an exception record, a gate override, an audit trail). |
| `severity` | enum: `info`, `warning`, `blocking` | How the violation should be treated. Only `blocking` is meant to stop a gate; `info`/`warning` are recorded but non-stopping. |
| `scope` | string, a glob pattern | Which files/paths the rule applies to, e.g. `"**/*"` or `"src/**"`. |
| `check` | enum: `static`, `artifact`, `graph-query` | The check class: `static` (patterns, linters, scanners over files), `artifact` (schema/content rules over `.spark` documents), or `graph-query` (structural queries over a knowledge graph). |

> **`check: graph-query` is structural only.** This repo can document and
> validate the *shape* of a `graph-query` check, but it cannot execute one —
> that requires querying a knowledge graph, which is aSPARK-graph's job, a
> separate repository. A rule with `check: graph-query` is a valid
> `policy.yaml`/`pack.yaml` document today; it becomes actually enforceable
> only once an aSPARK-graph integration exists.

Worked example:

```yaml
rules:
  security:
    id: SEC-014
    severity: blocking
    scope: "**/*"
    check: static
    final: true
```

None of these four keys are required — a rule block with only `final` (or with
none of the five) remains valid, exactly as it did before this section
existed. They add richer identification on top of the existing structural
conventions; they do not replace or constrain the domain-specific sub-keys a
rule block already carries — this document validates structure only, never
domain semantics.

---

## 2. `pack.yaml`

The metadata file at the root of every pack. Read by the Facilitator (during
`/charter`) to resolve an import into effective rules and lens activation.

| Key | Required | Type / shape | Meaning |
|---|---|---|---|
| `id` | **required** | string, kebab-case | The **flat** import id, e.g. `owasp`. Must equal the pack's directory name. Never contains the category. |
| `category` | **required** | string, one of the six | On-disk grouping only: `compliance`, `architecture`, `language`, `framework`, `cloud`, `platform`. **Metadata — never part of the id.** |
| `kind` | **required** | enum: `universal` \| `baseline` | `universal` = an external standard identical for every org (may be `final`). `baseline` = an opinionated default meant to be overridden (must not be `final`). |
| `version` | **required** | integer | Pack content version; bump on rule changes. |
| `maps_to_lens` | **required** | lens name or `null` | The existing aSPARK Core lens this pack activates, or `null` if none applies. Allowed: `seo`, `ux`, `api`, `cli`, `library`, `security`, `i18n`, `data`, or `null`. |
| `summary` | optional | string | One-paragraph description of what the pack covers and which agents consume it. |
| `references` | optional | list of strings (URLs) | External standard(s) the pack is based on. |

> **`maps_to_lens` and the lens gaps:** aSPARK Core today ships the lenses
> listed above. Concepts with no lens yet — cloud, architecture — set
> `maps_to_lens: null`; those packs apply as plain constitution constraints
> until the corresponding lens exists. This matches the README's "gaps" note.

### 2.1 Pack anatomy (recap)

Every pack is three files (see [`packs/README.md`](packs/README.md)):

```
<category>/<id>/
├── pack.yaml       # the metadata table above
├── <topic>.md      # the human-readable standard
└── policy.yaml     # the rule fragment the pack contributes (a bare `rules:` tree)
```

A pack's `policy.yaml` carries a `rules:` block only — no `schema_version` /
`name` / `imports`; those belong to a *project/org* `policy.yaml`, not a pack.

---

## 3. Import namespaces

`imports` entries name packs in one of three forms. **The category is never part
of the id** — that is the single most important rule here.

| Form | Meaning | Example |
|---|---|---|
| `aspark:<pack>` | a built-in pack shipped in this repo's `packs/` | `aspark:owasp` |
| `company:<pack>` | a pack defined in the same (company) policy repo | `company:acme-naming` |
| `git@<host>:<org>/<repo>.git#<tag>` | an external policy repo, pinned to a tag | `git@github.com:acme/policy.git#v2` |

**Flat-id rule — good vs. bad:**

```yaml
imports:
  - aspark:owasp                 # ✅ flat id
  - aspark:compliance/owasp      # ❌ category ("compliance/") must NOT appear in the id
```

---

## 4. Submodule mount (portability)

An organization's policy repo is mounted into a project as a Git submodule at
`.spark/policy/`. For discovery to work, the policy repo's **`policy.yaml` must
sit at its own root**, so that after mounting it resolves at:

```
<project>/.spark/policy/policy.yaml
```

This is the single path the Facilitator reads during `/charter`. A template
company policy repo (when one exists) must therefore keep `policy.yaml` at its
top level, not nested. (NFR-5.)

---

## 5. Worked examples & fixtures

One **known-good** and one **known-bad** fragment for each file live under
[`tests/fixtures/format/`](tests/fixtures/format/). The `*-bad` files carry
inline comments naming the exact rule each fragment breaks, so the future schema
and CLI have ready-made pass/fail targets.

| Fixture | What it demonstrates |
|---|---|
| [`policy-good.yaml`](tests/fixtures/format/policy-good.yaml) | a valid org-level `policy.yaml` |
| [`policy-bad.yaml`](tests/fixtures/format/policy-bad.yaml) | violations annotated inline |
| [`pack-good.yaml`](tests/fixtures/format/pack-good.yaml) | a valid `pack.yaml` (matches the shipped `owasp` pack) |
| [`pack-bad.yaml`](tests/fixtures/format/pack-bad.yaml) | violations annotated inline |

The shipped [`owasp` pack](packs/compliance/owasp/) is the live conformance
example: its `pack.yaml` and `policy.yaml` both satisfy this reference (verified
in the foundation increment, AC-3.3).
