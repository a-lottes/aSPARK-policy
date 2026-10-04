"""Determinism, offline and performance proofs (resolve-cli T9, spec US-3).

The SHA-256 constants pin the exact stdout bytes. Every OS in the CI matrix
(.github/workflows/test.yml) runs the same test, so equal constants mean equal
output across operating systems (AC-3.2). They are constants, not a golden
file, because git `autocrlf` on Windows would rewrite a checked-in golden file.
A pack edit changes the all-packs hash on purpose: effective-output changes
must be visible. On mismatch the assertion prints the full output for diffing.
"""

import hashlib
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LAYERED = Path(__file__).parent / "fixtures" / "resolve" / "layered"

ALL_PACKS = [
    "aws",
    "azure",
    "clean-architecture",
    "iso27001",
    "java",
    "misra",
    "owasp",
    "pci-dss",
    "react",
    "spring",
    "un-r155",
]
ALL_IMPORTS = ",".join(f"aspark:{pack}" for pack in ALL_PACKS)

LAYERED_SHA256 = "ea81cb59c0d92c84f3de041642e65a677408f495efd48202d7a4e8ab9112071a"
ALL_PACKS_SHA256 = "0c6cea8c949a8dd11e93b0cf5077ac1a3503bae7ef105a8d95c7701a2d87121e"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_hash(out: bytes, expected: str) -> None:
    assert sha(out) == expected, f"stdout changed (sha256 {sha(out)}); output was:\n{out.decode()}"


def test_two_runs_have_identical_bytes(make_project, run_cli):
    # AC-3.1
    root = make_project(LAYERED)
    assert run_cli("resolve", str(root)).out == run_cli("resolve", str(root)).out
    assert run_cli("resolve", "--imports", ALL_IMPORTS).out == run_cli("resolve", "--imports", ALL_IMPORTS).out


def test_stdout_matches_the_committed_hash_for_a_fixture_tree(make_project, run_cli):
    # AC-3.2 (a)
    result = run_cli("resolve", str(make_project(LAYERED)))
    assert result.code == 0
    assert_hash(result.out, LAYERED_SHA256)


def test_stdout_matches_the_committed_hash_for_all_eleven_packs(run_cli):
    # AC-3.2 (b)
    result = run_cli("resolve", "--imports", ALL_IMPORTS)
    assert result.code == 0
    assert_hash(result.out, ALL_PACKS_SHA256)


def test_output_is_independent_of_where_the_project_lives(make_project, run_cli, tmp_path):
    # AC-3.3: paths are relative to the given root, so a different location gives the same bytes.
    first = run_cli("resolve", str(make_project(LAYERED))).out
    elsewhere = tmp_path / "some" / "deeper" / "place"
    elsewhere.mkdir(parents=True)
    import shutil

    shutil.copytree(LAYERED, elsewhere / ".spark" / "policy")
    assert run_cli("resolve", str(elsewhere)).out == first


def test_output_leaks_no_absolute_path_hostname_or_backslash(make_project, run_cli, tmp_path):
    # AC-3.3
    root = make_project(LAYERED)
    out = run_cli("resolve", str(root)).out.decode()
    assert str(tmp_path) not in out
    assert str(REPO_ROOT) not in out
    assert socket.gethostname() not in out
    assert "\\\\" not in out and "/Users/" not in out
    doc = json.loads(out)
    for entry in doc["origins"] + doc["layers"]:
        assert not Path(entry["file"]).is_absolute()


def test_object_keys_are_sorted_everywhere(run_cli):
    out = run_cli("resolve", "--imports", ALL_IMPORTS).out

    def check(node):
        if isinstance(node, dict):
            assert list(node) == sorted(node)
            for child in node.values():
                check(child)
        elif isinstance(node, list):
            for child in node:
                check(child)

    check(json.loads(out, object_pairs_hook=lambda pairs: dict(pairs)))


def test_no_network_and_no_subprocess_are_used_and_results_are_unchanged(
    monkeypatch, make_project, run_cli
):
    # AC-3.4 / NFR-2
    root = make_project(LAYERED)
    baseline = run_cli("resolve", str(root)).out
    baseline_all = run_cli("resolve", "--imports", ALL_IMPORTS).out

    def boom(*args, **kwargs):
        raise AssertionError("network or subprocess used during resolve")

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    assert run_cli("resolve", str(root)).out == baseline
    assert run_cli("resolve", "--imports", ALL_IMPORTS).out == baseline_all
    assert run_cli("validate", str(REPO_ROOT / "packs")).code == 0


@pytest.mark.parametrize("pack", ALL_PACKS)
def test_every_shipped_pack_resolves_on_its_own(run_cli, pack):
    # US-3 / success signal: all 11 packs resolve.
    result = run_cli("resolve", "--imports", f"aspark:{pack}")
    assert result.code == 0, result.err
    assert json.loads(result.out)["layers"][0]["pack"] == f"aspark:{pack}"


def test_the_ac_1_2_pair_and_the_full_catalog_resolve(run_cli):
    for imports in ("aspark:owasp,aspark:java", ALL_IMPORTS):
        assert run_cli("resolve", "--imports", imports).code == 0


def test_cold_resolve_of_all_packs_takes_under_two_seconds():
    # NFR-1: subprocess, so interpreter start-up and imports are included.
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "aspark_policy", "resolve", "--imports", ALL_IMPORTS],
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    elapsed = time.perf_counter() - start
    assert proc.returncode == 0, proc.stderr
    assert elapsed < 2.0, f"cold resolve took {elapsed:.2f}s"
