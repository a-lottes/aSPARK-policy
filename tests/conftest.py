"""Shared helpers: run the CLI in-process and build project trees in tmp_path.

`.spark/` is gitignored at every depth, so fixture project trees are stored as
plain policy trees under tests/fixtures/ and materialised into
`<tmp>/.spark/policy/` by `make_project` — a committed `.spark/` would silently
not be committed.
"""

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from aspark_policy._cli import main


@pytest.fixture
def run_cli(capsysbinary):
    def run(*argv):
        code = main(list(argv))
        captured = capsysbinary.readouterr()
        return SimpleNamespace(code=code, out=captured.out, err=captured.err)

    return run


@pytest.fixture
def make_project(tmp_path):
    made = []

    def make(fixture_dir: Path | None = None, files: dict[str, str] | None = None) -> Path:
        """Return a project root with `.spark/policy/` filled from a fixture
        directory and/or an inline {relative path: text} mapping."""
        root = tmp_path / f"project{len(made)}"
        made.append(root)
        policy_dir = root / ".spark" / "policy"
        policy_dir.mkdir(parents=True)
        if fixture_dir is not None:
            shutil.copytree(fixture_dir, policy_dir, dirs_exist_ok=True)
        for rel, text in (files or {}).items():
            target = policy_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return root

    return make
