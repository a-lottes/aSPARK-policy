"""Tests proving the three JSON Schemas encode FORMAT-REFERENCE.md faithfully.

Structure mirrors the schemas themselves: self-validity, fixture round-trips,
per-constraint rejection, the pack/pack-policy distinctness proof (AC-3.3),
the real-pack sweep (US-4), attributability (US-5), and cross-cutting
determinism/offline/footprint checks (T7).
"""

import json
import re
import time
import tomllib
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).parent.parent

SCHEMAS_DIR = Path(__file__).parent.parent / "src" / "aspark_policy" / "schemas"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "format"
PACKS_DIR = Path(__file__).parent.parent / "packs"


def _safe_load(path: Path) -> dict:
    """Load YAML via the safe loader only — the NFR-6 safe-loading floor."""
    with open(path) as f:
        return yaml.safe_load(f)


def _load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / name) as f:
        return yaml.safe_load(f)  # JSON is valid YAML; safe_load handles both


PACK_SCHEMA = _load_schema("pack.schema.json")


def test_pack_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(PACK_SCHEMA)


def test_pack_good_fixture_validates_clean():
    instance = _safe_load(FIXTURES_DIR / "pack-good.yaml")
    errors = list(Draft202012Validator(PACK_SCHEMA).iter_errors(instance))
    assert errors == []


def test_pack_bad_fixture_is_rejected():
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    errors = list(Draft202012Validator(PACK_SCHEMA).iter_errors(instance))
    assert len(errors) >= 1


# --- T2: per-constraint rejection, each targeting a specific pack-bad.yaml violation ---


def _pack_errors(instance: dict) -> list:
    return list(Draft202012Validator(PACK_SCHEMA).iter_errors(instance))


def test_pack_id_with_slash_is_rejected():
    # pack-bad.yaml: id: compliance/aws — AC-1.4, the flat-id rule.
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    assert instance["id"] == "compliance/aws"
    errors = _pack_errors(instance)
    assert any(e.validator == "pattern" and list(e.absolute_path) == ["id"] for e in errors)


def test_pack_category_not_in_enum_is_rejected():
    # pack-bad.yaml: category: infrastructure — AC-1.5.
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    assert instance["category"] == "infrastructure"
    errors = _pack_errors(instance)
    assert any(e.validator == "enum" and list(e.absolute_path) == ["category"] for e in errors)


def test_pack_kind_not_in_enum_is_rejected():
    # pack-bad.yaml: kind: standard — AC-1.6.
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    assert instance["kind"] == "standard"
    errors = _pack_errors(instance)
    assert any(e.validator == "enum" and list(e.absolute_path) == ["kind"] for e in errors)


def test_pack_missing_version_is_rejected():
    # pack-bad.yaml has no version key at all — AC-1.3.
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    assert "version" not in instance
    errors = _pack_errors(instance)
    assert any(e.validator == "required" and "version" in e.message for e in errors)


def test_pack_maps_to_lens_not_in_enum_is_rejected():
    # pack-bad.yaml: maps_to_lens: cloud (not an existing lens) — AC-1.7.
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    assert instance["maps_to_lens"] == "cloud"
    errors = _pack_errors(instance)
    assert any(e.validator == "enum" and list(e.absolute_path) == ["maps_to_lens"] for e in errors)


def test_pack_undocumented_top_level_key_is_rejected():
    # AC-1.8: no key beyond FORMAT-REFERENCE.md §2's documented set is accepted.
    instance = _safe_load(FIXTURES_DIR / "pack-good.yaml")
    instance["unexpected_typo_key"] = "surprise"
    errors = _pack_errors(instance)
    assert any(e.validator == "additionalProperties" for e in errors)


# --- T3: project/org-level policy.yaml schema (FORMAT-REFERENCE.md §1) ---

PROJECT_POLICY_SCHEMA = _load_schema("project-policy.schema.json")


def _project_policy_errors(instance: dict) -> list:
    return list(Draft202012Validator(PROJECT_POLICY_SCHEMA).iter_errors(instance))


def test_project_policy_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(PROJECT_POLICY_SCHEMA)


def test_policy_good_fixture_validates_clean():
    instance = _safe_load(FIXTURES_DIR / "policy-good.yaml")
    assert _project_policy_errors(instance) == []


def test_policy_bad_fixture_is_rejected():
    instance = _safe_load(FIXTURES_DIR / "policy-bad.yaml")
    assert len(_project_policy_errors(instance)) >= 1


def test_policy_minimal_schema_version_and_name_only_is_valid():
    # FORMAT-REFERENCE.md §1: "A policy.yaml with only schema_version + name
    # is valid (it activates nothing)." — AC-2.4.
    instance = {"schema_version": 1, "name": "x"}
    assert _project_policy_errors(instance) == []


def test_policy_missing_schema_version_is_rejected():
    # policy-bad.yaml has no schema_version — AC-2.3.
    instance = _safe_load(FIXTURES_DIR / "policy-bad.yaml")
    assert "schema_version" not in instance
    errors = _project_policy_errors(instance)
    assert any(e.validator == "required" and "schema_version" in e.message for e in errors)


def test_policy_import_missing_namespace_prefix_is_rejected():
    # policy-bad.yaml: `owasp` with no aspark:/company:/git@ prefix — AC-2.5.
    instance = _safe_load(FIXTURES_DIR / "policy-bad.yaml")
    assert "owasp" in instance["imports"]
    errors = _project_policy_errors(instance)
    assert any(e.validator == "pattern" and list(e.absolute_path)[:1] == ["imports"] for e in errors)


def test_policy_import_id_embeds_category_is_rejected():
    # policy-bad.yaml: `aspark:compliance/owasp` embeds the category — AC-2.6.
    instance = _safe_load(FIXTURES_DIR / "policy-bad.yaml")
    assert "aspark:compliance/owasp" in instance["imports"]
    errors = _project_policy_errors(instance)
    assert any(e.validator == "pattern" and list(e.absolute_path)[:1] == ["imports"] for e in errors)


def test_policy_rules_open_mapping_with_arbitrary_domain_key_is_valid():
    # AC-2.7: rules validates structure only — any domain key, only `final`
    # carries fixed meaning.
    instance = {
        "schema_version": 1,
        "name": "x",
        "rules": {"some_arbitrary_domain": {"final": True, "anything_else": 42}},
    }
    assert _project_policy_errors(instance) == []


# --- T4: a pack's own bare-rules policy.yaml fragment (FORMAT-REFERENCE.md §2.1) ---

PACK_POLICY_SCHEMA = _load_schema("pack-policy.schema.json")


def _pack_policy_errors(instance: dict) -> list:
    return list(Draft202012Validator(PACK_POLICY_SCHEMA).iter_errors(instance))


def test_pack_policy_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(PACK_POLICY_SCHEMA)


def test_owasp_policy_fragment_validates_clean():
    # AC-3.1: the shipped owasp pack's own policy.yaml.
    instance = _safe_load(PACKS_DIR / "compliance" / "owasp" / "policy.yaml")
    assert _pack_policy_errors(instance) == []


def test_pack_policy_fragment_with_project_level_keys_is_rejected():
    # AC-3.2: a fragment carrying name/schema_version (project-level keys)
    # does not belong in a pack's own policy.yaml.
    instance = {"schema_version": 1, "name": "x", "rules": {"security": {}}}
    errors = _pack_policy_errors(instance)
    assert any(e.validator == "additionalProperties" for e in errors)


def test_policy_good_fixture_is_rejected_by_pack_policy_schema():
    # AC-3.3: the two schemas are meaningfully distinct, not the same schema
    # reused under two names — policy-good.yaml validates clean against the
    # project-policy schema (T3) but must reject against this one.
    instance = _safe_load(FIXTURES_DIR / "policy-good.yaml")
    assert _project_policy_errors(instance) == []
    assert len(_pack_policy_errors(instance)) >= 1


# --- T5: US-4 — every shipped pack conforms to the new schemas ---

# The 8 packs known to be shipped as of this increment (foundation: owasp;
# fill-pack-catalog: the other 7). A discovered pack outside this set, or a
# missing one, fails loudly below rather than silently changing the sweep.
KNOWN_PACKS = [
    ("compliance", "owasp"),
    ("compliance", "iso27001"),
    ("language", "java"),
    ("framework", "spring"),
    ("framework", "react"),
    ("architecture", "clean-architecture"),
    ("cloud", "aws"),
    ("cloud", "azure"),
]


def test_known_packs_list_matches_packs_directory_exactly():
    discovered = sorted(
        (p.parent.name, p.name)
        for p in PACKS_DIR.glob("*/*")
        if p.is_dir() and (p / "pack.yaml").exists()
    )
    assert discovered == sorted(KNOWN_PACKS)


@pytest.mark.parametrize("category,pack_id", KNOWN_PACKS)
def test_shipped_pack_yaml_validates_clean(category, pack_id):
    # AC-4.1
    instance = _safe_load(PACKS_DIR / category / pack_id / "pack.yaml")
    errors = _pack_errors(instance)
    assert errors == [], f"{category}/{pack_id}/pack.yaml: {[e.message for e in errors]}"


@pytest.mark.parametrize("category,pack_id", KNOWN_PACKS)
def test_shipped_pack_policy_yaml_validates_clean(category, pack_id):
    # AC-4.2
    instance = _safe_load(PACKS_DIR / category / pack_id / "policy.yaml")
    errors = _pack_policy_errors(instance)
    assert errors == [], f"{category}/{pack_id}/policy.yaml: {[e.message for e in errors]}"


# --- T6: US-5 — bad-fixture failures are attributable to the specific rule ---


def _attributable(errors: list, needle: str) -> bool:
    """True if `needle` (a field name or a distinctive value) appears in some
    error's json_path / absolute_path / message — the three attribution
    channels from the plan's concrete assertion strategy."""
    for e in errors:
        if needle in str(getattr(e, "json_path", "")):
            return True
        if needle in [str(p) for p in e.absolute_path]:
            return True
        if needle in e.message:
            return True
    return False


def test_pack_bad_violations_are_individually_attributable():
    # AC-5.1: pack-bad.yaml's 5 documented violations.
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    errors = _pack_errors(instance)
    violations = {
        "id": _attributable(errors, "id"),
        "category": _attributable(errors, "category"),
        "kind": _attributable(errors, "kind"),
        "version": _attributable(errors, "version"),
        "maps_to_lens": _attributable(errors, "maps_to_lens"),
    }
    assert all(violations.values()), violations


def test_policy_bad_violations_are_individually_attributable():
    # AC-5.2: policy-bad.yaml's 3 documented violations.
    instance = _safe_load(FIXTURES_DIR / "policy-bad.yaml")
    errors = _project_policy_errors(instance)
    violations = {
        "schema_version": _attributable(errors, "schema_version"),
        "aspark:compliance/owasp": _attributable(errors, "aspark:compliance/owasp")
        or _attributable(errors, "imports"),
        "owasp (bare)": _attributable(errors, "owasp") or _attributable(errors, "imports"),
    }
    assert all(violations.values()), violations


def test_at_least_six_of_eight_documented_violations_are_attributable():
    # AC-5.3: best-effort tally across both *-bad fixtures — 8 documented
    # violations total (5 pack-bad + 3 policy-bad); Should, not Must, so the
    # bar is >=6, not 8/8. Generic JSON Schema messages don't cleanly pin
    # down every violation (spec's own honest framing).
    pack_errors = _pack_errors(_safe_load(FIXTURES_DIR / "pack-bad.yaml"))
    policy_errors = _project_policy_errors(_safe_load(FIXTURES_DIR / "policy-bad.yaml"))

    attributable = sum(
        [
            _attributable(pack_errors, "id"),
            _attributable(pack_errors, "category"),
            _attributable(pack_errors, "kind"),
            _attributable(pack_errors, "version"),
            _attributable(pack_errors, "maps_to_lens"),
            _attributable(policy_errors, "schema_version"),
            _attributable(policy_errors, "imports"),  # aspark:compliance/owasp entry
            _attributable(policy_errors, "imports"),  # bare owasp entry
        ]
    )
    assert attributable >= 6, f"only {attributable}/8 documented violations were attributable"


# --- T7: consistency, determinism, offline, footprint & performance sweep ---


def test_pack_schema_matches_format_reference_field_set():
    # NFR-1: FORMAT-REFERENCE.md §2's required/optional/enum sets, exactly.
    assert set(PACK_SCHEMA["required"]) == {"id", "category", "kind", "version", "maps_to_lens"}
    assert set(PACK_SCHEMA["properties"].keys()) == {
        "id", "category", "kind", "version", "maps_to_lens", "summary", "references",
    }
    assert PACK_SCHEMA["additionalProperties"] is False
    assert set(PACK_SCHEMA["properties"]["category"]["enum"]) == {
        "compliance", "architecture", "language", "framework", "cloud", "platform",
    }
    assert set(PACK_SCHEMA["properties"]["kind"]["enum"]) == {"universal", "baseline"}
    assert set(PACK_SCHEMA["properties"]["maps_to_lens"]["enum"]) == {
        "seo", "ux", "api", "cli", "library", "security", "i18n", "data", None,
    }


def test_project_policy_schema_matches_format_reference_field_set():
    # NFR-1: FORMAT-REFERENCE.md §1's required/optional set, exactly.
    assert set(PROJECT_POLICY_SCHEMA["required"]) == {"schema_version", "name"}
    assert set(PROJECT_POLICY_SCHEMA["properties"].keys()) == {
        "schema_version", "name", "extends", "imports", "rules",
    }
    assert PROJECT_POLICY_SCHEMA["additionalProperties"] is False


def test_pack_policy_schema_matches_format_reference_field_set():
    # NFR-1: FORMAT-REFERENCE.md §2.1 — rules only, nothing project-level.
    assert set(PACK_POLICY_SCHEMA["required"]) == {"rules"}
    assert set(PACK_POLICY_SCHEMA["properties"].keys()) == {"rules"}
    assert PACK_POLICY_SCHEMA["additionalProperties"] is False


def test_rule_block_def_is_identical_across_pack_and_project_policy_schemas():
    # R1 drift check: the shared $defs/ruleBlock (final/id/severity/scope/check)
    # must stay byte-for-byte identical across both self-contained schema files.
    pack_rule_block = PACK_POLICY_SCHEMA["$defs"]["ruleBlock"]
    project_rule_block = PROJECT_POLICY_SCHEMA["$defs"]["ruleBlock"]
    assert pack_rule_block == project_rule_block


def test_flat_id_kebab_pattern_is_identical_across_pack_and_project_policy_schemas():
    # R4 drift check: the kebab-case class must be byte-identical wherever it
    # is duplicated, since the two schema files are self-contained (ADR).
    pack_id_pattern = PACK_SCHEMA["properties"]["id"]["pattern"]
    kebab_class = r"[a-z0-9]+(-[a-z0-9]+)*"
    assert pack_id_pattern == f"^{kebab_class}$"
    imports_pattern = PROJECT_POLICY_SCHEMA["properties"]["imports"]["items"]["pattern"]
    assert f"aspark:{kebab_class}" in imports_pattern
    assert f"company:{kebab_class}" in imports_pattern


def test_validation_is_deterministic():
    # NFR-3: validating the same file twice yields identical error output.
    instance = _safe_load(FIXTURES_DIR / "pack-bad.yaml")
    run1 = [e.message for e in _pack_errors(instance)]
    run2 = [e.message for e in _pack_errors(instance)]
    assert run1 == run2


def test_no_schema_references_a_remote_uri():
    # NFR-4: offline operation — no remote $ref, no externally-resolvable $id.
    for name in ["pack.schema.json", "project-policy.schema.json", "pack-policy.schema.json"]:
        text = (SCHEMAS_DIR / name).read_text()
        for match in re.finditer(r'"\$(ref|id)"\s*:\s*"([^"]+)"', text):
            value = match.group(2)
            assert not value.startswith("http://") and not value.startswith("https://"), (
                f"{name} has a network-resolvable {match.group(1)}: {value}"
            )


def test_dependencies_remain_empty():
    # NFR-5 / A2 Option A: schema-only deliverable, no runtime dependency
    # promotion. jsonschema/PyYAML must be dev-only.
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    assert pyproject["project"]["dependencies"] == []
    dev_deps = " ".join(pyproject["project"]["optional-dependencies"]["dev"])
    assert "jsonschema" in dev_deps
    assert "PyYAML" in dev_deps
    assert "scripts" not in pyproject["project"]  # still no CLI wired (§6)


# --- rule-anatomy-v2: id/severity/scope/check as new optional ruleBlock keys ---


def test_rule_anatomy_good_fixture_validates_clean():
    # AC-2.3
    instance = _safe_load(FIXTURES_DIR / "rule-anatomy-good.yaml")
    errors = _pack_policy_errors(instance)
    assert errors == []


def test_rule_anatomy_bad_severity_is_rejected():
    # AC-2.4: rule-anatomy-bad.yaml: severity: critical (not in enum).
    instance = _safe_load(FIXTURES_DIR / "rule-anatomy-bad.yaml")
    assert instance["rules"]["security"]["severity"] == "critical"
    errors = _pack_policy_errors(instance)
    assert any(
        e.validator == "enum" and list(e.absolute_path) == ["rules", "security", "severity"]
        for e in errors
    )


def test_rule_anatomy_bad_check_is_rejected():
    # AC-2.4: rule-anatomy-bad.yaml: check: regex-scan (not in enum).
    instance = _safe_load(FIXTURES_DIR / "rule-anatomy-bad.yaml")
    assert instance["rules"]["security"]["check"] == "regex-scan"
    errors = _pack_policy_errors(instance)
    assert any(
        e.validator == "enum" and list(e.absolute_path) == ["rules", "security", "check"]
        for e in errors
    )


def test_original_four_fixtures_still_behave_as_before():
    # AC-2.5: the pre-existing fixtures are untouched and behave identically
    # after the ruleBlock extension — additive, not a breaking change.
    assert _pack_errors(_safe_load(FIXTURES_DIR / "pack-good.yaml")) == []
    assert len(_pack_errors(_safe_load(FIXTURES_DIR / "pack-bad.yaml"))) >= 1
    assert _project_policy_errors(_safe_load(FIXTURES_DIR / "policy-good.yaml")) == []
    assert len(_project_policy_errors(_safe_load(FIXTURES_DIR / "policy-bad.yaml"))) >= 1


def test_owasp_security_block_carries_rule_anatomy_and_validates_clean():
    # AC-3.1/AC-3.2: owasp's top-level security block migrated to the new
    # anatomy; controls/dependency_policy/secrets untouched (§6, R2).
    instance = _safe_load(PACKS_DIR / "compliance" / "owasp" / "policy.yaml")
    security = instance["rules"]["security"]
    assert security["id"] == "OWASP-TOP10"
    assert security["severity"] == "blocking"
    assert security["scope"] == "**/*"
    assert security["check"] == "static"
    assert security["owasp_top10"] is True
    assert "controls" in security and "dependency_policy" in security and "secrets" in security
    assert _pack_policy_errors(instance) == []


def test_single_file_validation_completes_under_200ms():
    # NFR-7: performance, on the current (small, <=~50 line) fixtures/packs.
    instance = _safe_load(FIXTURES_DIR / "pack-good.yaml")
    validator = Draft202012Validator(PACK_SCHEMA)
    start = time.perf_counter()
    list(validator.iter_errors(instance))
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 200, f"validation took {elapsed_ms:.1f}ms"
