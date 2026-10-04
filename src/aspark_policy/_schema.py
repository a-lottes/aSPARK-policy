"""A small, dependency-free JSON Schema checker for the three shipped schemas.

Runtime code may only depend on PyYAML (constitution §3), so `jsonschema` is
not available here. The shipped schemas use a fixed keyword set; this module
implements exactly that set, and a test fails if a schema ever uses another
keyword (see `unsupported_keywords`).
"""

import json
import re
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"

SCHEMA_FILES = {
    "pack": "pack.schema.json",
    "project-policy": "project-policy.schema.json",
    "pack-policy": "pack-policy.schema.json",
}

# Keywords that assert something and are implemented below.
SUPPORTED_KEYWORDS = frozenset(
    {
        "type",
        "required",
        "properties",
        "additionalProperties",
        "enum",
        "pattern",
        "items",
        "$ref",
        "$defs",
    }
)
# Keywords that only annotate and are safe to ignore.
ANNOTATION_KEYWORDS = frozenset({"$schema", "title", "description"})

_TYPE_NAMES = {
    "object": "an object",
    "array": "a list",
    "string": "a string",
    "integer": "an integer",
    "boolean": "a boolean",
}


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / SCHEMA_FILES[name]).read_text(encoding="utf-8"))


def unsupported_keywords(schema: dict) -> set[str]:
    """Every keyword in `schema` that is neither supported nor an annotation."""
    found: set[str] = set()

    def walk(node: object) -> None:
        if not isinstance(node, dict):
            return
        found.update(set(node) - SUPPORTED_KEYWORDS - ANNOTATION_KEYWORDS)
        for sub in node.get("properties", {}).values():
            walk(sub)
        for sub in node.get("$defs", {}).values():
            walk(sub)
        walk(node.get("items"))
        walk(node.get("additionalProperties"))

    walk(schema)
    return found


def _is_type(value: object, name: str) -> bool:
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    raise ValueError(f"unsupported type {name!r}")


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _walk(instance: object, schema: dict, root: dict, path: str, errors: list) -> None:
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"unsupported $ref {ref!r}")
        _walk(instance, root["$defs"][ref[len("#/$defs/") :]], root, path, errors)

    here = path or "-"
    if "type" in schema and not _is_type(instance, schema["type"]):
        errors.append((here, f"must be {_TYPE_NAMES[schema['type']]}"))
        return
    if "enum" in schema and not any(
        instance == option and type(instance) is type(option) for option in schema["enum"]
    ):
        allowed = ", ".join(json.dumps(o) for o in schema["enum"])
        errors.append((here, f"must be one of: {allowed}"))
    if "pattern" in schema and isinstance(instance, str):
        if re.search(schema["pattern"], instance) is None:
            errors.append((here, f"does not match pattern {schema['pattern']}"))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append((here, f"missing required key `{key}`"))
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, value in instance.items():
            child = _join(path, key)
            if key in properties:
                _walk(value, properties[key], root, child, errors)
            elif extra is False:
                errors.append((child, "additional property is not allowed"))
            elif isinstance(extra, dict):
                _walk(value, extra, root, child, errors)

    if isinstance(instance, list) and isinstance(schema.get("items"), dict):
        for index, value in enumerate(instance):
            _walk(value, schema["items"], root, f"{path}[{index}]", errors)


def check(instance: object, schema_name: str) -> list[tuple[str, str]]:
    """Return sorted `(key_path, reason)` pairs; an empty list means valid."""
    schema = load_schema(schema_name)
    errors: list[tuple[str, str]] = []
    _walk(instance, schema, schema, "", errors)
    return sorted(set(errors))
