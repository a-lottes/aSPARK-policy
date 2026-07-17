# Repository Conventions

> The canonical map of this repository: where everything lives and why. Every
> top-level path is listed here, and every path listed here exists (NFR-1). If
> you add a top-level path, add a row here in the same change.
>
> This document owns *layout*; [`FORMAT-REFERENCE.md`](FORMAT-REFERENCE.md) owns
> the *file formats*; the [`README.md`](README.md) owns the *design*.

## Top-level layout

| Path | Purpose |
|---|---|
| [`README.md`](README.md) | The design & concept of aSPARK-policy — the design source of truth. |
| [`CONVENTIONS.md`](CONVENTIONS.md) | This file: the canonical repository layout. |
| [`FORMAT-REFERENCE.md`](FORMAT-REFERENCE.md) | Authoritative reference for the `policy.yaml` and `pack.yaml` formats. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute — chiefly, how to add a pack. |
| [`LICENSE`](LICENSE) | MIT license. |
| [`packs/`](packs/) | The built-in `aspark:` pack catalog, grouped into the six category directories. |
| `src/aspark_policy/` | The Python package — the code home for tooling (see below). |
| `tests/` | The test suite and format fixtures (`tests/fixtures/format/`). |
| `pyproject.toml` | Project + build config (Python ≥3.11, uv, hatchling, pytest). |
| `uv.lock` | Committed lockfile — deterministic `uv sync` (NFR-6). |
| `.gitignore` | Excludes OS/editor cruft and Python/uv artifacts. |
| `.spark/` | The aSPARK delivery trail (spec, plan, review, qa, release) for each feature. |

**Not documented as content paths:** `.git/` is Git's own internal directory,
not project content. **Git-ignored, not part of the committed structure:**
`.venv/`, `.pytest_cache/`, `__pycache__/`, `build/`, `dist/` and similar are
created by tooling and excluded by [`.gitignore`](.gitignore); they are not
repository paths.

## The code home

Tooling code lives in **`src/aspark_policy/`** (src-layout, package name
`aspark_policy`), with tests in **`tests/`**. Today the package is an **empty
scaffold** — it installs and imports but ships no logic (spec §6). The future
**JSON Schema** and the **`aspark-policy validate` CLI** are added here in later
increments; no other location is introduced for them.

## Where a pack goes

A pack lives at `packs/<category>/<id>/` and is three files
(`pack.yaml`, one `*.md`, `policy.yaml`) — see [`packs/README.md`](packs/README.md).
The **category is metadata only, never part of the import id** (`aspark:<id>`).

**Worked example:** the built-in OWASP pack has `id: owasp` and
`category: compliance`, so by this rule it lives at
**`packs/compliance/owasp/`** — which is exactly where it is.

The six categories: `compliance`, `architecture`, `language`, `framework`,
`cloud`, `platform`.

## Roadmap item → home mapping

Every open roadmap item from the README already has a documented home here, so
the layout absorbs them without a later restructure (NFR-4):

| Roadmap item | Home |
|---|---|
| JSON Schema for `policy.yaml` / `pack.yaml` | `src/aspark_policy/` (+ fixtures already in `tests/fixtures/format/`) |
| `aspark-policy validate` CLI | `src/aspark_policy/` (a `[project.scripts]` entry added in `pyproject.toml` then) |
| Fill the built-in catalog (`iso27001`, `java`, `spring`, `react`, `aws`, `azure`, `sap`, `clean-architecture`) | `packs/<category>/<id>/` (category dirs already exist) |
| Template company policy repo | `examples/` (deferred; `policy.yaml` at its root per the submodule-mount rule) |
| Facilitator / `/charter` integration | lives in aSPARK Core, not this repo; consumes `.spark/policy/policy.yaml` |
| `cloud` / `architecture` lenses | live in aSPARK Core; unblock `maps_to_lens` for the cloud/architecture packs |
| Per-phase policy enforcement in the remaining seven skills | lives in aSPARK Core, not this repo; each skill reads the constitution the Facilitator already bound |
| `Policy` / `PolicyViolation` node types + `gate_health` extension | lives in aspark-graph, not this repo; extends its existing artifact node types |
