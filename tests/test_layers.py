"""Layer discovery tests (resolve-cli T4): input forms, ordering, import errors."""

import json
from pathlib import Path

import pytest

from aspark_policy import _layers
from aspark_policy._layers import ResolveError, discover_imports, discover_project

FIXTURES = Path(__file__).parent / "fixtures" / "resolve"
MIN = "schema_version: 1\nname: {name}\n"


def _names(found):
    return [(layer.kind, layer.pack if layer.kind == "pack" else layer.name) for layer in found.layers]


def test_layer_order_is_imports_then_extends_chain_then_entry(make_project):
    # AC-1.9: ancestors' imports first, de-duplicated; then Corporate, Department, Project.
    root = make_project(FIXTURES / "layered")
    found = discover_project(root)
    assert _names(found) == [
        ("pack", "aspark:owasp"),
        ("pack", "aspark:iso27001"),
        ("pack", "aspark:java"),
        ("pack", "company:acme-naming"),
        ("policy", "Corporate"),
        ("policy", "Department"),
        ("policy", "Project"),
    ]
    assert found.imports == [
        "aspark:owasp",
        "aspark:iso27001",
        "aspark:java",
        "company:acme-naming",
    ]
    assert found.policy == ".spark/policy/policy.yaml"


def test_layer_files_are_posix_and_relative(make_project):
    root = make_project(FIXTURES / "layered")
    files = [layer.file for layer in discover_project(root).layers]
    assert files[0] == "packs/compliance/owasp/policy.yaml"
    assert files[3] == ".spark/policy/packs/platform/acme-naming/policy.yaml"
    assert files[4] == ".spark/policy/levels/corporate/policy.yaml"
    assert files[6] == ".spark/policy/policy.yaml"


def test_lookup_prefers_dot_spark_policy_then_directory_policy(tmp_path):
    (tmp_path / ".spark" / "policy").mkdir(parents=True)
    (tmp_path / ".spark" / "policy" / "policy.yaml").write_text(MIN.format(name="Nested"))
    (tmp_path / "policy.yaml").write_text(MIN.format(name="Flat"))
    assert discover_project(tmp_path).layers[-1].name == "Nested"
    (tmp_path / ".spark" / "policy" / "policy.yaml").unlink()
    assert discover_project(tmp_path).layers[-1].name == "Flat"


def test_missing_policy_file_is_exit_2(tmp_path):
    with pytest.raises(ResolveError) as exc:
        discover_project(tmp_path)
    assert exc.value.code == 2


def test_extends_outside_the_root_is_exit_2(make_project):
    root = make_project(files={"policy.yaml": MIN.format(name="P") + "extends: ../../../..\n"})
    with pytest.raises(ResolveError) as exc:
        discover_project(root)
    assert exc.value.code == 2
    assert "outside the project root" in exc.value.items[0][2]


def test_extends_missing_target_is_exit_2(make_project):
    root = make_project(files={"policy.yaml": MIN.format(name="P") + "extends: nope\n"})
    with pytest.raises(ResolveError) as exc:
        discover_project(root)
    assert exc.value.code == 2
    assert "no such policy file" in exc.value.items[0][2]


def test_extends_cycle_is_exit_2(make_project):
    root = make_project(
        files={
            "policy.yaml": MIN.format(name="A") + "extends: b\n",
            "b/policy.yaml": MIN.format(name="B") + "extends: ..\n",
        }
    )
    with pytest.raises(ResolveError) as exc:
        discover_project(root)
    assert exc.value.code == 2
    assert "cycle" in exc.value.items[0][2]


@pytest.mark.parametrize(
    "ref, reason",
    [
        ("aspark:does-not-exist", "no such pack"),
        ("company:missing", "pack not found"),
        ("git@github.com:org/policies.git#v1", "not supported offline"),
    ],
)
def test_unresolvable_imports_are_exit_2_naming_the_import(make_project, run_cli, ref, reason):
    # AC-1.7 through the CLI: stderr names import + reason, stdout empty, exit 2.
    root = make_project(files={"policy.yaml": MIN.format(name="P") + f"imports:\n  - {ref}\n"})
    result = run_cli("resolve", str(root))
    assert result.code == 2
    assert result.out == b""
    err = result.err.decode()
    assert ref in err and reason in err
    assert err.startswith("error: .spark/policy/policy.yaml: imports[0]: ")


def test_git_import_flag_form_and_company_under_imports_are_exit_2(run_cli):
    for ref, reason in [
        ("git@github.com:org/policies.git#v1", "not supported offline"),
        ("company:acme-naming", "company packs need a policy directory"),
        ("aspark:nope", "no such pack"),
        ("owasp", "unsupported import form"),
    ]:
        result = run_cli("resolve", "--imports", ref)
        assert result.code == 2, ref
        assert result.out == b""
        assert ref in result.err.decode() and reason in result.err.decode()


def test_schema_error_in_any_loaded_file_is_exit_1_with_file_and_key(make_project, run_cli):
    root = make_project(
        files={
            "policy.yaml": MIN.format(name="P") + "extends: org\n",
            "org/policy.yaml": "name: Org\n",  # missing schema_version
        }
    )
    result = run_cli("resolve", str(root))
    assert result.code == 1
    assert result.out == b""
    assert (
        b"error: .spark/policy/org/policy.yaml: -: missing required key `schema_version`"
        in result.err
    )


def test_malformed_yaml_is_exit_2_without_a_traceback(make_project, run_cli):
    root = make_project(files={"policy.yaml": "name: [oops\n"})
    result = run_cli("resolve", str(root))
    assert result.code == 2
    assert b"Traceback" not in result.err
    assert result.err.startswith(b"error: .spark/policy/policy.yaml: -: line ")


def test_aspark_packs_resolve_identically_from_package_data_and_checkout(tmp_path, monkeypatch):
    # D-e: the wheel ships packs as package data; lookup prefers it, falls back to the checkout.
    import shutil

    packaged = tmp_path / "pkg" / "packs"
    shutil.copytree(_layers.CHECKOUT_PACKS, packaged)
    from_checkout = discover_imports("aspark:owasp,aspark:java")

    monkeypatch.setattr(_layers, "PACKAGE_DATA", packaged)
    assert _layers.catalog_root() == packaged
    from_package = discover_imports("aspark:owasp,aspark:java")

    monkeypatch.setattr(_layers, "PACKAGE_DATA", tmp_path / "absent")
    assert _layers.catalog_root() == _layers.CHECKOUT_PACKS

    def view(found):
        return [(layer.pack, layer.file, layer.rules) for layer in found.layers]

    assert view(from_package) == view(from_checkout)
    assert from_package.layers[0].file == "packs/compliance/owasp/policy.yaml"


def test_empty_rules_and_zero_imports_resolve_to_an_empty_policy(make_project, run_cli):
    # NFR-4: defined result, never a traceback.
    root = make_project(files={"policy.yaml": MIN.format(name="P") + "rules: {}\n"})
    result = run_cli("resolve", str(root))
    assert result.code == 0
    assert json.loads(result.out)["rules"] == {}


def test_resolve_dir_and_imports_together_is_a_usage_error(make_project, run_cli):
    root = make_project(files={"policy.yaml": MIN.format(name="P")})
    result = run_cli("resolve", str(root), "--imports", "aspark:owasp")
    assert result.code == 2
    assert result.out == b""
    assert b"cannot be combined" in result.err
