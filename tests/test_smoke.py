"""Smoke test: the scaffold installs, imports, and exposes a version.

This is the only code-testable slice of the `foundation` increment (spec §4).
It proves the harness runs — nothing about policy behaviour, which does not
exist yet (AC-6.5).
"""

import aspark_policy


def test_package_imports_and_has_version():
    assert isinstance(aspark_policy.__version__, str)
    assert aspark_policy.__version__
