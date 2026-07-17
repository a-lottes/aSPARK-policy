# Built-in Policy Packs

This directory holds the **built-in catalog** shipped with aSPARK-policy — the
packs available under the `aspark:` import namespace. Organizations add their
own packs in their own policy repository under the `company:` namespace; nothing
company-specific lives here.

## Layout

Packs are grouped **by category on disk** (for maintainers). The category is
metadata — it is **not** part of the import id, which stays flat:

```
imports:
  - aspark:owasp      # ✅ flat id
  - aspark:compliance/owasp   # ❌ never — category is not part of the id
```

```
packs/
├── compliance/     iso27001 · owasp
├── architecture/   clean-architecture
├── language/       java
├── framework/      spring · react
├── cloud/          aws · azure
└── platform/       sap
```

## Two kinds of pack

| Kind | Meaning | May be `final`? |
|---|---|---|
| **universal** | the same for every organization — an external standard (OWASP, ISO 27001) | yes |
| **baseline** | an opinionated default, meant to be overridden per org (a Java version, a framework convention) | no |

A baseline pack is a **scaffold to tighten**, never a locked constraint.

## Anatomy of a pack

Every pack is three files:

```
<pack>/
├── pack.yaml       # metadata: id, category, kind, maps_to_lens, version
├── <topic>.md      # the human-readable standard
└── policy.yaml     # the rule fragment this pack contributes
```

- `pack.yaml` — machine-readable metadata. What the pack is, which category and
  kind it belongs to, and which existing aSPARK lens (if any) it activates.
- `*.md` — the standard in prose, the way a human reads and reviews it.
- `policy.yaml` — the `rules:` fragment merged into the effective policy when
  the pack is imported.

See [`compliance/owasp/`](compliance/owasp/) for the reference implementation.

## Adding a pack

1. Pick the category directory (or add one).
2. Create the three files above.
3. Set `kind: universal` only if the pack is an external standard identical for
   every organization; otherwise `kind: baseline`.
4. If it maps onto an existing lens (`seo`, `ux`, `api`, `cli`, `library`,
   `security`, `i18n`, `data`), set `maps_to_lens`. If the concept needs a lens that does
   not exist yet (today: `cloud`, `architecture`), leave `maps_to_lens: null`
   and note it — the pack applies as plain constitution constraints until the
   lens exists in aSPARK Core.
