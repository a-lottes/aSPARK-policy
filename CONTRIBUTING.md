# Contributing to aSPARK-policy

Thanks for helping build the aSPARK policy layer. This repo is in its
**foundation** phase — the structure and file formats are settled; the schema
and `validate` CLI come in later increments.

Before you start, read the two reference docs:

- [`CONVENTIONS.md`](CONVENTIONS.md) — the repository layout: where everything lives.
- [`FORMAT-REFERENCE.md`](FORMAT-REFERENCE.md) — the `policy.yaml` / `pack.yaml` formats.

## Adding a built-in pack

A pack is the unit of the `aspark:` catalog. To add one:

1. **Pick the category.** One of `compliance`, `architecture`, `language`,
   `framework`, `cloud`, `platform` (see [`packs/README.md`](packs/README.md)).
   Create `packs/<category>/<id>/`, where `<id>` is a flat kebab-case name
   (e.g. `iso27001`). The category is **never** part of the import id.

2. **Create the three files** (the pack anatomy):
   - `pack.yaml` — metadata: `id`, `category`, `kind`, `version`,
     `maps_to_lens`, and optionally `summary` / `references`. See
     [`FORMAT-REFERENCE.md §2`](FORMAT-REFERENCE.md#2-packyaml).
   - `<topic>.md` — the human-readable standard.
   - `policy.yaml` — the rule fragment (a bare `rules:` tree).

3. **Set `kind` honestly.** `universal` only for an external standard identical
   for every organization (it may be locked with `final`). Otherwise `baseline`
   — an opinionated default meant to be overridden; a baseline's rules must
   **not** be `final`.

4. **Set `maps_to_lens`.** If the pack maps onto an existing aSPARK Core lens
   (`seo`, `ux`, `api`, `cli`, `library`, `security`, `i18n`, `data`), name it.
   If the concept has no lens yet (cloud, architecture), set `maps_to_lens: null`
   and note it — the pack applies as plain constitution constraints until the
   lens exists.

5. **Check conformance.** Hold your `pack.yaml` / `policy.yaml` against
   [`FORMAT-REFERENCE.md`](FORMAT-REFERENCE.md) and the pass/fail examples in
   [`tests/fixtures/format/`](tests/fixtures/format/). The shipped
   [`owasp` pack](packs/compliance/owasp/) is the reference to copy.

## Hygiene

- **No company-specific or secret content.** This repo ships only `aspark:`
  namespace content — public standards and generic docs. Company policies live
  in a company's own repo (`company:` / a Git submodule), never here.
- Changes flow through pull requests. Keep `LICENSE` intact.

## Working on the tooling

The Python scaffold uses **uv**:

```bash
uv sync --extra dev     # set up the environment
uv run pytest           # run the test suite
```

The package `src/aspark_policy/` is currently an empty scaffold by design
(no parsing/schema/CLI logic yet).
