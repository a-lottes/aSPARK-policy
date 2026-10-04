"""Safe YAML loading for policy.yaml / pack.yaml.

`PolicyLoader` subclasses the *pure-Python* `yaml.SafeLoader` on purpose: the C
parser (`CSafeLoader`) can differ per platform, which would endanger the
byte-identical output guarantee (spec AC-3.2).
"""

from pathlib import Path

import yaml


class LoadError(Exception):
    """A file could not be turned into plain data. Maps to exit code 2."""

    def __init__(self, file: str, key: str, reason: str):
        super().__init__(f"{file}: {key}: {reason}")
        self.file = file
        self.key = key
        self.reason = reason


class Override(list):
    """A list tagged `!override`: replaces the inherited list instead of merging."""


class PolicyLoader(yaml.SafeLoader):
    pass


# Dates must stay strings (a datetime is not JSON-serialisable and the
# constructor result would differ from what the author wrote).
PolicyLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _construct_override(loader: PolicyLoader, node: yaml.Node) -> Override:
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(
            None,
            None,
            "`!override` is only valid on a list",
            node.start_mark,
        )
    return Override(loader.construct_sequence(node, deep=True))


PolicyLoader.add_constructor("!override", _construct_override)


def _check_keys(value: object, path: str, file: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise LoadError(file, path or "-", f"non-string mapping key {key!r}")
            _check_keys(child, f"{path}.{key}" if path else key, file)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_keys(child, f"{path}[{index}]", file)


def load_text(text: str, file: str) -> object:
    """Parse YAML `text`; `file` is only used in error messages."""
    try:
        data = yaml.load(text, Loader=PolicyLoader)  # noqa: S506 - PolicyLoader is a SafeLoader
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        problem = (getattr(exc, "problem", None) or str(exc)).strip().replace("\n", " ")
        where = f"line {mark.line + 1}: " if mark is not None else ""
        raise LoadError(file, "-", f"{where}{problem}") from exc
    except RecursionError:  # a recursive alias builds a self-referencing structure
        raise LoadError(file, "-", "recursive YAML alias or nesting too deep") from None
    try:
        _check_keys(data, "", file)
    except RecursionError:
        raise LoadError(file, "-", "recursive YAML alias or nesting too deep") from None
    return data


def load_file(path: Path, display: str | None = None) -> object:
    """Read and parse `path` (UTF-8). IO problems become `LoadError` too."""
    name = display or path.as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise LoadError(name, "-", f"cannot read file: {exc}") from exc
    return load_text(text, name)
