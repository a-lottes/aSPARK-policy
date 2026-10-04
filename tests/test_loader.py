"""Loader unit tests (resolve-cli T2): safe loading, `!override`, string dates."""

import pytest
import yaml

from aspark_policy._loader import LoadError, Override, PolicyLoader, load_file, load_text


def test_override_on_a_list_becomes_an_override_marker():
    data = load_text("rules:\n  deps: !override [a, b]\n", "f.yaml")
    deps = data["rules"]["deps"]
    assert isinstance(deps, Override)
    assert deps == ["a", "b"]


def test_override_on_a_mapping_is_a_load_error():
    with pytest.raises(LoadError) as exc:
        load_text("rules: !override {a: 1}\n", "f.yaml")
    assert "only valid on a list" in exc.value.reason
    assert exc.value.file == "f.yaml"


def test_override_on_a_scalar_is_a_load_error():
    with pytest.raises(LoadError):
        load_text("rules:\n  a: !override 1\n", "f.yaml")


def test_python_object_tags_are_rejected():
    with pytest.raises(LoadError):
        load_text("x: !!python/object/apply:os.system ['true']\n", "f.yaml")


def test_unknown_tags_are_rejected():
    with pytest.raises(LoadError):
        load_text("x: !custom 1\n", "f.yaml")


def test_dates_stay_strings():
    data = load_text("released: 2026-10-01\nwhen: 2026-10-01 10:00:00\n", "f.yaml")
    assert data == {"released": "2026-10-01", "when": "2026-10-01 10:00:00"}


def test_non_string_keys_name_file_and_key_path():
    with pytest.raises(LoadError) as exc:
        load_text("rules:\n  a:\n    1: x\n", "f.yaml")
    assert exc.value.file == "f.yaml"
    assert exc.value.key == "rules.a"
    assert "non-string" in exc.value.reason


def test_malformed_yaml_reports_file_and_line():
    with pytest.raises(LoadError) as exc:
        load_text("a: [1, 2\nb: 3\n", "f.yaml")
    assert exc.value.file == "f.yaml"
    assert exc.value.key == "-"
    assert exc.value.reason.startswith("line ")


def test_missing_file_is_a_load_error(tmp_path):
    with pytest.raises(LoadError) as exc:
        load_file(tmp_path / "nope.yaml", "nope.yaml")
    assert "cannot read" in exc.value.reason


def test_loader_is_the_pure_python_safe_loader():
    # AC-3.2 / NFR-2: never the C parser, never an unsafe loader.
    assert issubclass(PolicyLoader, yaml.SafeLoader)
    assert not issubclass(PolicyLoader, yaml.CSafeLoader)
    assert not issubclass(PolicyLoader, (yaml.FullLoader, yaml.UnsafeLoader))
