"""The dependency-free schema checker must agree with `jsonschema` (dev only)."""

import copy
import functools
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from aspark_policy import _schema

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures" / "format"
SCHEMA_NAMES = list(_schema.SCHEMA_FILES)


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@functools.cache
def _reference_validator(name: str) -> Draft202012Validator:
    schema = json.loads((_schema.SCHEMAS_DIR / _schema.SCHEMA_FILES[name]).read_text())
    return Draft202012Validator(schema)


def _reference_valid(instance, name: str) -> bool:
    return _reference_validator(name).is_valid(instance)


def _instances():
    for path in sorted(FIXTURES.glob("*.yaml")):
        yield path.name, _load(path)
    for path in sorted((REPO_ROOT / "packs").glob("*/*/*.yaml")):
        yield path.relative_to(REPO_ROOT).as_posix(), _load(path)


def _mutations(instance):
    """Systematic mutations of a good instance (top-level and one level down)."""
    if not isinstance(instance, dict):
        return
    junk = [123, "x", None, [], {}, True, ["a"], {"a": 1}]
    for key in list(instance):
        mutated = copy.deepcopy(instance)
        del mutated[key]
        yield mutated
        for value in junk:
            mutated = copy.deepcopy(instance)
            mutated[key] = value
            yield mutated
        if isinstance(instance[key], dict):
            for sub in list(instance[key]):
                for value in junk:
                    mutated = copy.deepcopy(instance)
                    mutated[key][sub] = value
                    yield mutated
        if isinstance(instance[key], list):
            for value in junk:
                mutated = copy.deepcopy(instance)
                mutated[key] = instance[key] + [value]
                yield mutated
    mutated = copy.deepcopy(instance)
    mutated["zzz_unknown"] = 1
    yield mutated


@pytest.mark.parametrize("schema_name", SCHEMA_NAMES)
def test_checker_agrees_with_jsonschema_on_fixtures_and_all_packs(schema_name):
    for label, instance in _instances():
        ours = _schema.check(instance, schema_name) == []
        assert ours == _reference_valid(instance, schema_name), (label, schema_name)


@pytest.mark.parametrize("schema_name", SCHEMA_NAMES)
def test_checker_agrees_with_jsonschema_on_mutations(schema_name):
    checked = 0
    for label, instance in _instances():
        for mutated in _mutations(instance):
            ours = _schema.check(mutated, schema_name) == []
            assert ours == _reference_valid(mutated, schema_name), (label, schema_name, mutated)
            checked += 1
    assert checked > 500


def test_checker_is_deterministic_and_attributes_errors():
    bad = _load(FIXTURES / "pack-bad.yaml")
    first = _schema.check(bad, "pack")
    assert first == _schema.check(bad, "pack")
    keys = [key for key, _ in first]
    assert "id" in keys and "category" in keys
    assert ("-", "missing required key `version`") in first


def test_error_for_root_type_uses_dash_key():
    assert _schema.check([], "pack")[0][0] == "-"


@pytest.mark.parametrize("schema_name", SCHEMA_NAMES)
def test_shipped_schemas_use_only_supported_keywords(schema_name):
    # If a schema ever adopts another keyword, this fails until _schema supports it.
    assert _schema.unsupported_keywords(_schema.load_schema(schema_name)) == set()


def test_unsupported_keyword_detector_works():
    assert _schema.unsupported_keywords({"type": "object", "oneOf": []}) == {"oneOf"}
