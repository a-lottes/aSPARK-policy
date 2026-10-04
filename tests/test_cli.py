"""CLI surface tests (resolve-cli): in-process via main(argv), plus subprocess
runs for the two entry points."""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import aspark_policy

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_resolve_imports_prints_one_json_document_with_format_version(run_cli):
    # AC-1.2, AC-1.8
    result = run_cli("resolve", "--imports", "aspark:owasp")
    assert result.code == 0
    assert result.err == b""
    doc = json.loads(result.out)
    assert doc["resolve_format"] == "1.0.0"
    assert "security" in doc["rules"]
    assert doc["layers"][0]["pack"] == "aspark:owasp"


def test_entry_points_work_as_subprocesses():
    # T1 DoD: console script and `python -m` both run.
    for cmd in (
        [sys.executable, "-m", "aspark_policy", "resolve", "--imports", "aspark:owasp"],
    ):
        proc = subprocess.run(cmd, capture_output=True, cwd=REPO_ROOT, check=False)
        assert proc.returncode == 0, proc.stderr
        assert json.loads(proc.stdout)["resolve_format"] == "1.0.0"


def test_version_matches_pyproject():
    # The scaffold's stale `0.0.1` must never drift from the package metadata.
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    assert aspark_policy.__version__ == pyproject["project"]["version"]


def test_no_public_python_api_beyond_version():
    # NFR-7: modules are private; nothing is exported but __version__.
    public = [n for n in dir(aspark_policy) if not n.startswith("_")]
    assert public == []


# --- T8: output and error contract ------------------------------------------

import re

LAYERED = REPO_ROOT / "tests" / "fixtures" / "resolve" / "layered"
ERROR_LINE = re.compile(rb"^error: \S+: \S+: ")


def test_resolve_dir_prints_one_json_document_with_the_documented_shape(make_project, run_cli):
    # AC-1.1, AC-1.6, AC-1.8
    root = make_project(LAYERED)
    result = run_cli("resolve", str(root))
    assert result.code == 0 and result.err == b""
    doc = json.loads(result.out)
    assert set(doc) == {"resolve_format", "input", "layers", "rules", "origins", "ordered"}
    assert doc["resolve_format"] == "1.0.0"
    assert doc["input"] == {
        "policy": ".spark/policy/policy.yaml",
        "imports": ["aspark:owasp", "aspark:iso27001", "aspark:java", "company:acme-naming"],
    }
    assert [layer["level"] for layer in doc["layers"]] == list(range(7))
    assert doc["layers"][-1] == {
        "level": 6,
        "kind": "policy",
        "name": "Project",
        "pack": "none",
        "file": ".spark/policy/policy.yaml",
    }
    assert doc["rules"]["review"] == {"minimum_reviewers": 3, "required": True}
    assert doc["rules"]["naming"] == {"branches": "kebab-case"}
    by_key = {o["key"]: o for o in doc["origins"]}
    assert by_key["rules.review.minimum_reviewers"]["level"] == 6
    assert by_key["rules.review.required"] == {
        "key": "rules.review.required",
        "level": 4,
        "pack": "none",
        "file": ".spark/policy/levels/corporate/policy.yaml",
    }


def test_output_is_canonical_json_ending_in_one_newline(run_cli):
    out = run_cli("resolve", "--imports", "aspark:owasp").out
    assert out.endswith(b"}\n") and not out.endswith(b"\n\n")
    assert b"\r" not in out
    text = out.decode("ascii")  # ensure_ascii: pure ASCII on every platform
    assert json.dumps(json.loads(text), sort_keys=True, ensure_ascii=True, indent=2) + "\n" == text


def test_stderr_lines_match_the_error_format_and_carry_no_ansi(make_project, run_cli, monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    cases = [
        run_cli("resolve", "--imports", "aspark:nope"),
        run_cli("resolve", str(make_project(files={"policy.yaml": "name: [oops\n"}))),
        run_cli("resolve", str(make_project(files={"policy.yaml": "name: x\n"}))),
    ]
    for result in cases:
        assert result.code in (1, 2) and result.out == b""
        lines = result.err.splitlines()
        assert lines and all(ERROR_LINE.match(line) for line in lines)
        assert b"\x1b" not in result.err


def test_every_exit_path_is_0_1_or_2(make_project, run_cli):
    codes = {
        run_cli("resolve", "--imports", "aspark:owasp").code,
        run_cli("resolve", "--imports", "aspark:nope").code,
        run_cli("resolve", str(make_project(files={"policy.yaml": "name: x\n"}))).code,
        run_cli("resolve").code,
        run_cli("resolve", "--nope").code,
    }
    assert codes == {0, 1, 2}


def test_usage_errors_exit_2_with_usage_on_stderr_and_empty_stdout(run_cli):
    for argv in (["resolve"], ["bogus"], ["resolve", "--nope"], []):
        result = run_cli(*argv)
        assert result.code == 2 and result.out == b""
        assert b"usage:" in result.err


# --- T12: help, version, usage errors -----------------------------------------


def test_help_for_every_command_lists_flags_arguments_and_an_example(run_cli):
    # AC-5.1
    expected = {
        (): ["--version", "resolve", "validate", "Example:", "Exit codes"],
        ("resolve",): ["directory", "--imports", "--json", "Example:"],
        ("validate",): ["path", "--json", "Example:"],
    }
    for command, needles in expected.items():
        result = run_cli(*command, "--help")
        assert result.code == 0 and result.err == b""
        text = result.out.decode()
        for needle in needles:
            assert needle in text, (command, needle)


def test_version_prints_the_package_version(run_cli):
    # AC-5.2
    result = run_cli("--version")
    assert result.code == 0
    assert result.out == f"aspark-policy {aspark_policy.__version__}\n".encode()


def test_unknown_subcommand_or_flag_prints_usage_to_stderr_and_exits_2(run_cli):
    # AC-5.4
    for argv in (["frobnicate"], ["resolve", "--frobnicate"], ["validate", "--frobnicate"], ["--frobnicate"]):
        result = run_cli(*argv)
        assert result.code == 2 and result.out == b""
        assert result.err.startswith(b"usage: aspark-policy")


def test_no_output_carries_ansi_even_with_force_color(run_cli, monkeypatch):
    # NFR-3 (Python 3.14 colours argparse by default)
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    for argv in (["--help"], ["resolve", "--help"], ["validate", "--help"], ["--version"], ["bogus"], ["resolve"]):
        result = run_cli(*argv)
        assert b"\x1b" not in result.out + result.err, argv


def test_flags_are_kebab_case_and_json_means_the_same_in_both_subcommands(run_cli):
    flags = set()
    for command in ("resolve", "validate"):
        text = run_cli(command, "--help").out.decode()
        flags |= set(re.findall(r"(?<![\w-])--[a-z][\w-]*", text))
    assert all(re.fullmatch(r"--[a-z]+(-[a-z]+)*", flag) for flag in flags), flags
    assert "--json" in run_cli("resolve", "--help").out.decode()
    assert "--json" in run_cli("validate", "--help").out.decode()
