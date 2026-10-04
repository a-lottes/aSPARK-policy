"""Docs and repo-hygiene checks (resolve-cli T10, T13)."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_ci_workflow_runs_the_suite_on_three_operating_systems():
    # AC-3.2: the "CI OS matrix" exists and is on `main`-push.
    doc = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "test.yml").read_text())
    triggers = doc.get("on", doc.get(True))  # PyYAML (YAML 1.1) reads a bare `on:` as True
    assert triggers["push"]["branches"] == ["main"]
    job = doc["jobs"]["pytest"]
    assert job["strategy"]["matrix"]["os"] == ["ubuntu-latest", "macos-latest", "windows-latest"]
    assert job["env"]["UV_PYTHON"] == "3.11"
    commands = [step["run"] for step in job["steps"] if "run" in step]
    assert commands == ["uv sync --extra dev", "uv run pytest"]


def test_conventions_lists_the_github_directory():
    conventions = (REPO_ROOT / "CONVENTIONS.md").read_text()
    assert "| `.github/` |" in conventions


# --- README honesty and examples (T13) -----------------------------------------

import json
import re

from aspark_policy._cli import RESOLVE_FORMAT

README = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
EXAMPLE = Path(__file__).parent / "fixtures" / "resolve" / "example"


def _block(name: str) -> str:
    match = re.search(
        rf"<!-- example:{name}:start -->\n```\w*\n(.*?)```\n<!-- example:{name}:end -->", README, re.S
    )
    assert match, f"README has no example:{name} block"
    return match.group(1)


def test_readme_documents_the_format_version_exit_codes_and_the_offline_limit():
    # AC-1.8, AC-5.3, NFR-10
    assert f"`{RESOLVE_FORMAT}`" in README
    for row in ("| `0` |", "| `1` |", "| `2` |"):
        assert row in README
    assert "not supported offline" in README
    assert "error: <file>: <key>: <reason>" in README
    for topic in ("**Layer order**", "**`final`.**", "**Merging.**", "**Output.**"):
        assert topic in README


def test_readme_resolve_example_equals_the_live_output(make_project, run_cli):
    # NFR-10: a stale example fails the build.
    result = run_cli("resolve", str(make_project(EXAMPLE)))
    assert result.code == 0
    assert _block("resolve") == result.out.decode()


def test_readme_violation_example_equals_the_live_stderr(make_project, run_cli):
    root = make_project(
        EXAMPLE, files={"policy.yaml": (EXAMPLE / "policy.yaml").read_text() + "  security:\n    owasp_top10: false\n"}
    )
    result = run_cli("resolve", str(root))
    assert result.code == 1
    assert _block("violation") == result.err.decode()


def test_readme_validate_example_equals_the_live_output(run_cli, monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    result = run_cli("validate", "packs/")
    assert _block("validate") == "$ aspark-policy validate packs/\n" + result.out.decode()


def test_readme_changelog_lists_this_release():
    # NFR-8
    assert "## Changelog" in README
    assert "### 0.3.0" in README


def test_readme_never_claims_that_agents_enforce_policy():
    # NFR-11 / constitution §6: the status section stays honest about enforcement.
    status = " ".join(README[README.index("## Project Status") :].split())  # unwrap lines
    assert "**not** an enforcement engine" in status
    assert "no agent calls it yet" in status
    assert "Facilitator/`/charter` integration in aSPARK Core" in status
