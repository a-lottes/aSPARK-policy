"""Input discovery: from a project directory or an import list to an ordered
list of layers, general to specific (spec AC-1.9).

Layer order: imported packs (ancestors' imports first, then the entry file's,
in listed order, de-duplicated by first occurrence), then each `extends`
ancestor from most general to most specific, then the entry file itself.
All file I/O of `resolve` lives here, so merging stays a pure function.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import _schema
from ._loader import LoadError, load_file

PACKAGE_DATA = Path(__file__).resolve().parent / "packs"
CHECKOUT_PACKS = Path(__file__).resolve().parents[2] / "packs"

_IMPORT_RE = re.compile(r"^(aspark|company):([a-z0-9]+(-[a-z0-9]+)*)$")
_GIT_RE = re.compile(r"^git@")

Items = list[tuple[str, str, str]]  # (file, key path, reason)


class ResolveError(Exception):
    """Resolution cannot continue. `code` is the CLI exit code (1 or 2)."""

    def __init__(self, code: int, items: Items):
        super().__init__("; ".join(f"{f}: {k}: {r}" for f, k, r in items))
        self.code = code
        self.items = items


@dataclass
class Layer:
    kind: str  # "pack" | "policy"
    name: str  # pack id, or the policy's own `name`
    pack: str  # "aspark:<id>" | "company:<id>" | "none"
    file: str  # POSIX display path
    rules: dict
    pack_kind: str | None = None  # "universal" | "baseline" for packs
    final_declared: bool = field(default=False)
    imported_by: int | None = None  # packs: ordinal of the policy file that first imported it


@dataclass
class Discovery:
    layers: list[Layer]
    policy: str | None  # display path of the entry policy, None for --imports
    imports: list[str]  # effective, de-duplicated import list


def catalog_root() -> Path:
    """The pack catalog: package data in a wheel, else the source checkout."""
    return PACKAGE_DATA if PACKAGE_DATA.is_dir() else CHECKOUT_PACKS


def _fail(code: int, file: str, key: str, reason: str) -> ResolveError:
    return ResolveError(code, [(file, key, reason)])


def _schema_items(file: str, errors: list[tuple[str, str]]) -> Items:
    return [(file, key, reason) for key, reason in errors]


def _load_pack(
    ref: str,
    pack_dir: Path,
    display_dir: str,
    schema_errors: Items,
) -> Layer:
    pack_id = pack_dir.name
    meta_file = f"{display_dir}/pack.yaml"
    policy_file = f"{display_dir}/policy.yaml"
    try:
        meta = load_file(pack_dir / "pack.yaml", meta_file)
        data = load_file(pack_dir / "policy.yaml", policy_file)
    except LoadError as exc:
        raise _fail(2, exc.file, exc.key, exc.reason) from exc
    if isinstance(meta, dict) and isinstance(meta.get("id"), str) and meta["id"] != pack_id:
        raise _fail(2, meta_file, "id", f"id {meta['id']!r} does not match the directory name {pack_id!r}")
    schema_errors += _schema_items(meta_file, _schema.check(meta, "pack"))
    schema_errors += _schema_items(policy_file, _schema.check(data, "pack-policy"))
    pack_kind = meta.get("kind") if isinstance(meta, dict) else None
    rules = data.get("rules") if isinstance(data, dict) else None
    return Layer(
        kind="pack",
        name=pack_id,
        pack=ref,
        file=policy_file,
        rules=rules if isinstance(rules, dict) else {},
        pack_kind=pack_kind if isinstance(pack_kind, str) else None,
    )


def _find_pack_dir(base: Path, pattern: str) -> Path | None:
    for candidate in sorted(base.glob(pattern)):
        if (candidate / "pack.yaml").is_file() and (candidate / "policy.yaml").is_file():
            return candidate
    return None


def _resolve_import(
    ref: str,
    where_file: str,
    where_key: str,
    policy_root: Path | None,
    root: Path | None,
    schema_errors: Items,
) -> Layer:
    if _GIT_RE.match(ref):
        raise _fail(2, where_file, where_key, f"{ref}: git imports are not supported offline")
    match = _IMPORT_RE.match(ref)
    if match is None:
        raise _fail(2, where_file, where_key, f"{ref}: unsupported import form")
    namespace, pack_id = match.group(1), match.group(2)
    if namespace == "aspark":
        base = catalog_root()
        pack_dir = _find_pack_dir(base, f"*/{pack_id}")
        if pack_dir is None:
            raise _fail(2, where_file, where_key, f"{ref}: no such pack in the catalog")
        display = f"packs/{pack_dir.parent.name}/{pack_id}"
        return _load_pack(ref, pack_dir, display, schema_errors)
    if policy_root is None or root is None:
        raise _fail(
            2, where_file, where_key, f"{ref}: company packs need a policy directory (not --imports)"
        )
    pack_dir = _find_pack_dir(policy_root, f"packs/*/{pack_id}")
    if pack_dir is None:
        raise _fail(2, where_file, where_key, f"{ref}: pack not found under {policy_root.name}/packs/")
    display = pack_dir.relative_to(root).as_posix()
    return _load_pack(ref, pack_dir, display, schema_errors)


def _split_imports(value: str) -> list[str]:
    return [part.strip() for part in value.split(",")]


def discover_imports(imports_arg: str) -> Discovery:
    """`resolve --imports a,b`: packs only, in the given order."""
    refs = _split_imports(imports_arg)
    layers: list[Layer] = []
    schema_errors: Items = []
    seen: list[str] = []
    for index, ref in enumerate(refs):
        if ref in seen:
            continue
        seen.append(ref)
        layers.append(_resolve_import(ref, "--imports", f"imports[{index}]", None, None, schema_errors))
    if schema_errors:
        raise ResolveError(1, sorted(schema_errors))
    return Discovery(layers=layers, policy=None, imports=seen)


def _entry_policy(root: Path) -> Path:
    for candidate in (root / ".spark" / "policy" / "policy.yaml", root / "policy.yaml"):
        if candidate.is_file():
            return candidate
    raise _fail(2, root.name or "-", "-", "no policy file (.spark/policy/policy.yaml or policy.yaml)")


def _resolve_extends(base_file: Path, value: str, root: Path, display: str) -> Path:
    target = (base_file.parent / value).resolve()
    if target.is_dir():
        target = target / "policy.yaml"
    try:
        target.relative_to(root)
    except ValueError:
        raise _fail(2, display, "extends", f"{value}: resolves outside the project root") from None
    if not target.is_file():
        raise _fail(2, display, "extends", f"{value}: no such policy file")
    return target


def discover_project(directory: Path) -> Discovery:
    """`resolve <dir>`: the entry policy, its `extends` chain and all imports."""
    root = directory.resolve()
    if not root.is_dir():
        raise _fail(2, directory.as_posix(), "-", "not a directory")
    entry = _entry_policy(root)
    policy_root = entry.parent

    schema_errors: Items = []
    chain: list[tuple[Path, str, dict]] = []  # entry first, then ancestors
    visited: set[Path] = set()
    current: Path | None = entry
    while current is not None:
        resolved = current.resolve()
        display = resolved.relative_to(root).as_posix()
        if resolved in visited:
            raise _fail(2, display, "extends", "cycle in the extends chain")
        visited.add(resolved)
        try:
            data = load_file(resolved, display)
        except LoadError as exc:
            raise _fail(2, exc.file, exc.key, exc.reason) from exc
        errors = _schema.check(data, "project-policy")
        schema_errors += _schema_items(display, errors)
        if errors or not isinstance(data, dict):
            chain.append((resolved, display, {}))
            break
        chain.append((resolved, display, data))
        extends = data.get("extends")
        current = _resolve_extends(resolved, extends, root, display) if extends else None

    general_first = list(reversed(chain))
    imports: list[str] = []
    pack_layers: list[Layer] = []
    for ordinal, (_, display, data) in enumerate(general_first):
        for index, ref in enumerate(data.get("imports", [])):
            if ref in imports:
                continue
            imports.append(ref)
            pack = _resolve_import(ref, display, f"imports[{index}]", policy_root, root, schema_errors)
            pack.imported_by = ordinal
            pack_layers.append(pack)

    policy_layers = [
        Layer(
            kind="policy",
            name=data.get("name", display),
            pack="none",
            file=display,
            rules=data.get("rules") or {},
        )
        for _, display, data in general_first
    ]
    if schema_errors:
        raise ResolveError(1, sorted(schema_errors))
    return Discovery(
        layers=pack_layers + policy_layers,
        policy=chain[0][1],
        imports=imports,
    )
