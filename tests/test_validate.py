"""`aspark-policy validate` tests (resolve-cli T11, spec US-4)."""

import json
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATE = Path(__file__).parent / "fixtures" / "validate"
PACK_YAML = "id: {id}\ncategory: platform\nkind: universal\nversion: 1\nmaps_to_lens: {lens}\n"


def copy_case(tmp_path: Path, case: str) -> Path:
    target = tmp_path / case
    shutil.copytree(VALIDATE / case, target)
    return target


def test_valid_pack_files_exit_0_with_exactly_one_stdout_line(run_cli):
    # AC-4.1
    for target in ("packs/compliance/owasp/pack.yaml", "packs/compliance/owasp/policy.yaml"):
        result = run_cli("validate", str(REPO_ROOT / target))
        assert result.code == 0 and result.err == b""
        assert result.out == b"ok: validated 1 file\n"


def test_valid_project_policy_file_exits_0(run_cli):
    result = run_cli("validate", str(Path(__file__).parent / "fixtures" / "format" / "policy-good.yaml"))
    # a policy-good.yaml is not named policy.yaml; validate refuses ambiguous names
    assert result.code == 2
    good = VALIDATE.parent / "resolve" / "layered" / "policy.yaml"
    result = run_cli("validate", str(good))
    assert result.code == 0 and result.out == b"ok: validated 1 file\n"


def test_schema_invalid_file_exits_1_with_file_key_and_reason_per_error(run_cli, tmp_path):
    # AC-4.2
    case = copy_case(tmp_path, "schema-invalid")
    result = run_cli("validate", str(case))
    assert result.code == 1 and result.out == b""
    lines = result.err.decode().splitlines()
    assert any(
        line.startswith("error: ") and "pack.yaml: category: must be one of" in line for line in lines
    )
    assert any("pack.yaml: version: must be an integer" in line for line in lines)
    assert all(line.count(": ") >= 2 for line in lines)


def test_pack_directory_that_deviates_from_the_layout_names_the_deviation(run_cli, tmp_path):
    # AC-4.3
    case = copy_case(tmp_path, "bad-layout")
    result = run_cli("validate", str(case))
    assert result.code == 1
    err = result.err.decode()
    assert "expected exactly one *.md file, found 0" in err
    assert "extra.txt: -: unexpected file in a pack" in err
    # a missing required file is named too
    (case / "policy.yaml").unlink()
    assert "missing policy.yaml" in run_cli("validate", str(case)).err.decode()


def test_dotfiles_and_pycache_are_ignored_in_the_layout_check(run_cli, tmp_path):
    case = copy_case(tmp_path, "good-pack")
    (case / ".DS_Store").write_text("x")
    (case / "__pycache__").mkdir()
    assert run_cli("validate", str(case)).code == 0


def test_id_that_differs_from_the_directory_name_is_exit_1(run_cli, tmp_path):
    # AC-4.4
    result = run_cli("validate", str(copy_case(tmp_path, "id-mismatch")))
    assert result.code == 1
    assert b"pack.yaml: id: id 'other-name' does not match the directory name 'id-mismatch'" in result.err


def test_baseline_pack_with_final_at_any_depth_is_exit_1(run_cli, tmp_path):
    # AC-4.5
    result = run_cli("validate", str(copy_case(tmp_path, "baseline-final")))
    assert result.code == 1
    assert b"policy.yaml: rules.code.java: a `baseline` pack must not mark a rule `final`" in result.err
    # the same file is fine in a universal pack
    case = copy_case(tmp_path, "good-pack")
    assert run_cli("validate", str(case)).code == 0


@pytest.mark.parametrize(
    "lens, code",
    [("cloud", 1), ("architecture", 1), ("nonsense", 1), ("null", 0), ("cli", 0), ("security", 0)],
)
def test_maps_to_lens_follows_the_schema_not_core(run_cli, tmp_path, lens, code):
    # AC-4.6: invalid per schema -> 1; null (BACKLOG P4) is valid -> 0.
    case = copy_case(tmp_path, "good-pack")
    (case / "pack.yaml").write_text(PACK_YAML.format(id="good-pack", lens=lens))
    assert run_cli("validate", str(case)).code == code


def test_validate_without_a_path_checks_the_whole_catalog(run_cli, monkeypatch):
    # AC-4.7
    monkeypatch.chdir(REPO_ROOT)
    result = run_cli("validate")
    assert result.code == 0 and result.err == b""
    assert result.out == b"ok: validated 22 files\n"


def test_validate_without_a_path_and_without_packs_is_a_usage_error(run_cli, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_cli("validate")
    assert result.code == 2 and result.out == b""
    assert b"no ./packs directory" in result.err


def test_missing_path_and_empty_directory_are_exit_2(run_cli, tmp_path):
    assert run_cli("validate", str(tmp_path / "nope")).code == 2
    assert run_cli("validate", str(tmp_path)).code == 2


def test_malformed_yaml_is_a_validation_error_not_a_traceback(run_cli, tmp_path):
    case = copy_case(tmp_path, "good-pack")
    (case / "policy.yaml").write_text("rules: [oops\n")
    result = run_cli("validate", str(case))
    assert result.code == 1 and b"Traceback" not in result.err
    assert b"policy.yaml: -: line " in result.err


def test_json_flag_emits_the_error_list_on_stdout(run_cli, tmp_path):
    case = copy_case(tmp_path, "id-mismatch")
    result = run_cli("validate", str(case), "--json")
    assert result.code == 1
    doc = json.loads(result.out)
    assert doc["resolve_format"] == "1.0.0"
    assert doc["errors"] == [
        {
            "file": f"{case.as_posix()}/pack.yaml",
            "key": "id",
            "reason": "id 'other-name' does not match the directory name 'id-mismatch'",
        }
    ]
    ok = json.loads(run_cli("validate", str(copy_case(tmp_path, "good-pack")), "--json").out)
    assert ok["errors"] == []


def test_validate_is_deterministic(run_cli, tmp_path):
    case = copy_case(tmp_path, "schema-invalid")
    assert run_cli("validate", str(case)).err == run_cli("validate", str(case)).err
