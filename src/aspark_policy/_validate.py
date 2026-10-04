"""`aspark-policy validate`: schema conformance plus pack integrity (spec US-4).

Schema checks come from `_schema`; integrity adds what a schema cannot say: the
three-file pack layout, `id` equal to the directory name, and a `baseline` pack
never setting `final`. A broken or unreadable YAML file is reported as a
validation error (exit 1), so one run lists every problem.
"""

from dataclasses import dataclass, field
from pathlib import Path

from . import _schema
from ._final import find_final_paths, format_path
from ._loader import LoadError, load_file

Errors = list[tuple[str, str, str]]  # (file, key path, reason)


class ValidateInputError(Exception):
    """The path itself is unusable (exit 2)."""

    def __init__(self, file: str, reason: str):
        super().__init__(f"{file}: -: {reason}")
        self.file = file
        self.reason = reason


@dataclass
class Report:
    errors: Errors = field(default_factory=list)
    files: int = 0


def _skip(path: Path) -> bool:
    return path.name.startswith(".") or path.name == "__pycache__"


def _load(path: Path, display: str, report: Report) -> object | None:
    report.files += 1
    try:
        return load_file(path, display)
    except LoadError as exc:
        report.errors.append((exc.file, exc.key, exc.reason))
        return None


def _check_schema(data: object, schema: str, display: str, report: Report) -> None:
    report.errors += [(display, key, reason) for key, reason in _schema.check(data, schema)]


def _validate_pack_dir(pack_dir: Path, display_dir: str, report: Report) -> None:
    entries = sorted(p for p in pack_dir.iterdir() if not _skip(p))
    names = {p.name for p in entries}
    markdown = [p.name for p in entries if p.is_file() and p.suffix == ".md"]
    for required in ("pack.yaml", "policy.yaml"):
        if required not in names:
            report.errors.append((display_dir, "-", f"missing {required}"))
    if len(markdown) != 1:
        report.errors.append((display_dir, "-", f"expected exactly one *.md file, found {len(markdown)}"))
    allowed = {"pack.yaml", "policy.yaml", *markdown}
    for entry in entries:
        if entry.name not in allowed and not (entry.is_file() and entry.suffix == ".md"):
            report.errors.append((f"{display_dir}/{entry.name}", "-", "unexpected file in a pack"))

    meta = policy = None
    if "pack.yaml" in names:
        meta = _load(pack_dir / "pack.yaml", f"{display_dir}/pack.yaml", report)
        if meta is not None:
            _check_schema(meta, "pack", f"{display_dir}/pack.yaml", report)
            if isinstance(meta, dict) and meta.get("id") != pack_dir.name:
                report.errors.append(
                    (
                        f"{display_dir}/pack.yaml",
                        "id",
                        f"id {meta.get('id')!r} does not match the directory name {pack_dir.name!r}",
                    )
                )
    if "policy.yaml" in names:
        policy = _load(pack_dir / "policy.yaml", f"{display_dir}/policy.yaml", report)
        if policy is not None:
            _check_schema(policy, "pack-policy", f"{display_dir}/policy.yaml", report)
    if isinstance(meta, dict) and meta.get("kind") == "baseline" and isinstance(policy, dict):
        rules = policy.get("rules")
        for path in find_final_paths(rules, ("rules",)) if isinstance(rules, dict) else []:
            report.errors.append(
                (
                    f"{display_dir}/policy.yaml",
                    format_path(path),
                    "a `baseline` pack must not mark a rule `final`",
                )
            )


def _validate_file(path: Path, display: str, report: Report) -> None:
    if path.name == "pack.yaml":
        data = _load(path, display, report)
        if data is not None:
            _check_schema(data, "pack", display, report)
            if isinstance(data, dict) and data.get("id") != path.resolve().parent.name:
                report.errors.append((display, "id", "id does not match the directory name"))
    elif path.name == "policy.yaml":
        data = _load(path, display, report)
        if data is not None:
            is_pack_policy = (path.parent / "pack.yaml").is_file()
            _check_schema(data, "pack-policy" if is_pack_policy else "project-policy", display, report)
    else:
        raise ValidateInputError(display, "unknown file; validate takes pack.yaml, policy.yaml or a directory")


def _pack_dirs(root: Path) -> list[Path]:
    found = []
    candidates = [root, *sorted(p for p in root.rglob("*") if p.is_dir())]
    for candidate in candidates:
        relative = candidate.relative_to(root).parts
        if any(part.startswith(".") or part == "__pycache__" for part in relative):
            continue
        if (candidate / "pack.yaml").is_file():
            found.append(candidate)
    return found


def _project_policies(root: Path) -> list[Path]:
    """Policy files below the root that `resolve` can reach through `extends`."""
    found = []
    for candidate in sorted(root.rglob("policy.yaml")):
        parts = candidate.relative_to(root).parts[:-1]
        if not parts or (candidate.parent / "pack.yaml").is_file():
            continue  # the root file is checked separately; a pack policy is never a project policy
        if any(part == "__pycache__" or (part.startswith(".") and part != ".spark") for part in parts):
            continue
        found.append(candidate)
    return found


def validate(path: Path) -> Report:
    display = path.as_posix()
    if not path.exists():
        raise ValidateInputError(display, "no such file or directory")
    report = Report()
    if path.is_file():
        _validate_file(path, display, report)
        return report

    packs = _pack_dirs(path)
    has_policy = (path / "policy.yaml").is_file() and path not in packs
    if not packs and not has_policy:
        raise ValidateInputError(display, "nothing to validate (no pack.yaml or policy.yaml)")
    if has_policy:
        data = _load(path / "policy.yaml", f"{display}/policy.yaml", report)
        if data is not None:
            _check_schema(data, "project-policy", f"{display}/policy.yaml", report)
    for extra in _project_policies(path):
        display_extra = f"{display}/{extra.relative_to(path).as_posix()}"
        data = _load(extra, display_extra, report)
        if data is not None:
            _check_schema(data, "project-policy", display_extra, report)
    for pack_dir in packs:
        relative = pack_dir.relative_to(path).as_posix()
        _validate_pack_dir(pack_dir, display if relative == "." else f"{display}/{relative}", report)
    report.errors.sort()
    return report
