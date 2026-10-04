"""`final` locks and pack-declared ordered rules (resolve-cli T6, T7).

Pure unit tests on in-memory layers plus CLI-level fixture-tree tests.
No shipped pack sets `final` or declares `ordered`, so these use fixtures (plan A6).
"""

import json

from aspark_policy._layers import Layer
from aspark_policy._loader import Override
from aspark_policy._merge import resolve

LOCK = "org.yaml"


def layer(rules, file="f.yaml", kind="policy", pack="none", pack_kind=None):
    return Layer(kind=kind, name="L", pack=pack, file=file, rules=rules, pack_kind=pack_kind)


def org(rules):
    return layer(rules, LOCK)


def reasons(result):
    return [(v.key, v.reason) for v in result.violations]


# --- T6: final locks -------------------------------------------------------


def test_removing_a_final_block_is_a_violation_and_the_block_is_kept():
    # AC-2.1
    result = resolve([org({"sec": {"final": True, "tls": True}}), layer({"sec": None}, "proj.yaml")])
    assert reasons(result) == [("rules.sec", "removed")]
    v = result.violations[0]
    assert (v.locked_by, v.violated_by) == (LOCK, "proj.yaml")
    assert result.rules == {"sec": {"final": True, "tls": True}}


def test_replacing_an_ancestor_of_a_nested_final_block_is_a_violation():
    # AC-2.1, review F1: a lock below the replaced node still binds
    locked = {"code": {"lang": {"java": {"final": True, "version": 21}}}}
    for replacement in (None, 5, ["x"]):
        result = resolve([org(locked), layer({"code": {"lang": replacement}}, "proj.yaml")])
        assert reasons(result) == [("rules.code.lang.java", "removed")], replacement
        v = result.violations[0]
        assert (v.locked_by, v.violated_by) == (LOCK, "proj.yaml")
        assert result.rules == locked


def test_replacing_a_mapping_without_any_lock_below_is_still_allowed():
    result = resolve([org({"code": {"lang": {"java": 21}}}), layer({"code": {"lang": None}}, "p.yaml")])
    assert result.violations == [] and result.rules == {"code": {"lang": None}}


def test_type_change_and_override_dropping_items_count_as_removal():
    base = org({"sec": {"final": True, "ids": ["a", "b"]}})
    r1 = resolve([base, layer({"sec": "off"}, "p.yaml")])
    assert reasons(r1) == [("rules.sec", "removed")]
    r2 = resolve([base, layer({"sec": {"ids": Override(["a"])}}, "p.yaml")])
    assert reasons(r2) == [("rules.sec.ids", "removed")]
    assert r2.rules["sec"]["ids"] == ["a", "b"]


def test_changing_a_locked_value_is_a_violation_and_the_locked_value_is_kept():
    # AC-2.2
    result = resolve([org({"sec": {"final": True, "mode": "strict"}}), layer({"sec": {"mode": "lax"}}, "p.yaml")])
    assert reasons(result) == [("rules.sec.mode", "changed")]
    assert result.rules["sec"]["mode"] == "strict"


def test_turning_final_off_null_or_appending_to_a_locked_list_are_violations():
    base = org({"sec": {"final": True, "ids": ["a"], "x": 1}})
    assert reasons(resolve([base, layer({"sec": {"final": False}}, "p")])) == [("rules.sec.final", "changed")]
    assert reasons(resolve([base, layer({"sec": {"x": None}}, "p")])) == [("rules.sec.x", "removed")]
    assert reasons(resolve([base, layer({"sec": {"ids": ["b"]}}, "p")])) == [("rules.sec.ids", "changed")]


def test_restating_a_locked_value_unchanged_is_fine():
    base = org({"sec": {"final": True, "mode": "strict", "ids": ["a"]}})
    result = resolve([base, layer({"sec": {"mode": "strict", "ids": ["a"]}}, "p")])
    assert result.violations == []


def test_adding_a_new_key_inside_a_final_block_is_allowed():
    # AC-2.4
    result = resolve([org({"sec": {"final": True, "a": 1}}), layer({"sec": {"b": 2}}, "proj.yaml")])
    assert result.violations == []
    assert result.rules["sec"] == {"final": True, "a": 1, "b": 2}
    by_key = {o["key"]: o["file"] for o in result.origins}
    assert by_key["rules.sec.b"] == "proj.yaml"
    assert by_key["rules.sec.a"] == LOCK


def test_a_nested_mapping_can_be_locked_on_its_own():
    base = org({"code": {"java": {"final": True, "v": 21}, "py": {"v": 3}}})
    result = resolve([base, layer({"code": {"java": {"v": 17}, "py": {"v": 4}}}, "p")])
    assert reasons(result) == [("rules.code.java.v", "changed")]
    assert result.rules["code"]["py"]["v"] == 4


def test_several_violations_are_all_reported_in_stable_order():
    # AC-2.5
    base = org({"b": {"final": True, "x": 1}, "a": {"final": True, "y": 1}})
    layers = [base, layer({"b": {"x": 2}, "a": {"y": 2}}, "p.yaml")]
    first, second = resolve(layers), resolve(layers)
    assert reasons(first) == [("rules.a.y", "changed"), ("rules.b.x", "changed")]
    assert first.violations == second.violations


def test_a_lock_set_in_the_same_layer_does_not_bind_that_layer():
    result = resolve([layer({"sec": {"mode": "a"}}), layer({"sec": {"final": True, "mode": "b"}})])
    assert result.violations == []
    assert result.rules["sec"]["mode"] == "b"


def test_baseline_pack_with_final_is_an_error_naming_the_pack():
    # AC-2.6, at any depth
    pack = layer(
        {"code": {"java": {"final": True}}}, "packs/language/x/policy.yaml", "pack", "company:x", "baseline"
    )
    result = resolve([pack])
    assert reasons(result) == [("rules.code.java", "baseline-final")]
    assert result.violations[0].violated_by == "packs/language/x/policy.yaml"
    universal = layer({"code": {"final": True}}, "u.yaml", "pack", "aspark:u", "universal")
    assert resolve([universal]).violations == []


# --- T7: pack-declared ordered rules ---------------------------------------


def ordered_pack(direction="higher-is-stricter", key="strict_mode"):
    return layer(
        {"sec": {"final": True, key: False, "ordered": {key: direction}}},
        "packs/compliance/x/policy.yaml",
        "pack",
        "company:x",
        "universal",
    )


def test_ordered_boolean_stricter_is_allowed_and_origin_is_the_specific_level():
    # AC-2.3
    result = resolve([ordered_pack(), layer({"sec": {"strict_mode": True}}, "proj.yaml")])
    assert result.violations == []
    assert result.rules["sec"]["strict_mode"] is True
    assert {o["key"]: o["file"] for o in result.origins}["rules.sec.strict_mode"] == "proj.yaml"


def test_ordered_boolean_weaker_is_a_violation():
    pack = ordered_pack()
    pack.rules["sec"]["strict_mode"] = True
    result = resolve([pack, layer({"sec": {"strict_mode": False}}, "proj.yaml")])
    assert reasons(result) == [("rules.sec.strict_mode", "weakened")]
    assert result.rules["sec"]["strict_mode"] is True


def test_ordered_numbers_work_in_both_directions():
    for direction, stricter, weaker in [("higher-is-stricter", 5, 1), ("lower-is-stricter", 1, 5)]:
        pack = layer(
            {"sec": {"final": True, "n": 3, "ordered": {"n": direction}}}, "p.yaml", "pack", "aspark:p", "universal"
        )
        ok = resolve([pack, layer({"sec": {"n": stricter}}, "proj.yaml")])
        assert ok.violations == [] and ok.rules["sec"]["n"] == stricter
        bad = resolve([pack, layer({"sec": {"n": weaker}}, "proj.yaml")])
        assert reasons(bad) == [("rules.sec.n", "weakened")]


def test_an_undeclared_key_changed_is_changed_not_ordered():
    pack = ordered_pack()
    result = resolve([pack, layer({"sec": {"other": 1}}, "p"), layer({"sec": {"other": 2}}, "q")])
    assert reasons(result) == [("rules.sec.other", "changed")]


def test_ordered_in_a_non_pack_file_is_invalid():
    result = resolve([layer({"sec": {"ordered": {"n": "higher-is-stricter"}}}, "proj.yaml")])
    assert reasons(result) == [("rules.sec", "ordered-invalid")]


def test_conflicting_directions_from_two_packs_are_invalid():
    a = ordered_pack("higher-is-stricter")
    b = ordered_pack("lower-is-stricter")
    b.file = "packs/compliance/y/policy.yaml"
    result = resolve([a, b])
    assert reasons(result) == [("rules.sec.strict_mode", "ordered-invalid")]


def test_unknown_direction_and_malformed_ordered_are_invalid():
    bad_direction = layer({"sec": {"ordered": {"n": "bigger"}}}, "p.yaml", "pack", "aspark:p", "universal")
    assert reasons(resolve([bad_direction])) == [("rules.sec.n", "ordered-invalid")]
    malformed = layer({"sec": {"ordered": ["n"]}}, "p.yaml", "pack", "aspark:p", "universal")
    assert reasons(resolve([malformed])) == [("rules.sec", "ordered-invalid")]


def test_ordered_is_stripped_from_rules_and_reported_at_the_top_level():
    result = resolve([ordered_pack()])
    assert "ordered" not in result.rules["sec"]
    assert result.ordered == [
        {"key": "rules.sec.strict_mode", "direction": "higher-is-stricter", "pack": "company:x"}
    ]
    assert all("ordered" not in o["key"] for o in result.origins)


def test_a_rule_domain_named_ordered_is_not_reserved():
    result = resolve([layer({"ordered": {"a": 1}})])
    assert result.rules == {"ordered": {"a": 1}}
    assert result.violations == []


# --- CLI level: fixture trees (made in tmp: `.spark/` is gitignored) -------

PACK = "id: lockpack\ncategory: platform\nkind: universal\nversion: 1\nmaps_to_lens: null\n"
LOCK_POLICY = (
    "rules:\n  security:\n    final: true\n    tls: required\n    strict_mode: false\n"
    "    ordered:\n      strict_mode: higher-is-stricter\n"
)


def _project(make_project, project_rules):
    return make_project(
        files={
            "policy.yaml": "schema_version: 1\nname: P\nimports:\n  - company:lockpack\n" + project_rules,
            "packs/platform/lockpack/pack.yaml": PACK,
            "packs/platform/lockpack/policy.yaml": LOCK_POLICY,
            "packs/platform/lockpack/lock.md": "# lock\n",
        }
    )


def test_cli_stricter_ordered_change_exits_0_and_weaker_exits_1(make_project, run_cli):
    ok = run_cli("resolve", str(_project(make_project, "rules:\n  security:\n    strict_mode: true\n")))
    assert ok.code == 0, ok.err
    doc = json.loads(ok.out)
    assert doc["rules"]["security"]["strict_mode"] is True
    assert doc["ordered"][0]["key"] == "rules.security.strict_mode"


def test_cli_violation_names_key_locker_violator_and_reason_and_prints_no_policy(make_project, tmp_path, run_cli):
    root = _project(make_project, "rules:\n  security:\n    tls: optional\n")
    result = run_cli("resolve", str(root))
    assert result.code == 1
    assert result.out == b""
    err = result.err.decode()
    assert err == (
        "error: .spark/policy/policy.yaml: rules.security.tls: "
        "final lock violated: changed (locked by .spark/policy/packs/platform/lockpack/policy.yaml)\n"
    )


def test_cli_json_flag_emits_only_the_violations_document(make_project, run_cli):
    # AC-2.7
    root = _project(make_project, "rules:\n  security:\n    tls: optional\n")
    result = run_cli("resolve", str(root), "--json")
    assert result.code == 1
    doc = json.loads(result.out)
    assert "rules" not in doc
    assert doc["violations"] == [
        {
            "key": "rules.security.tls",
            "locked_by": ".spark/policy/packs/platform/lockpack/policy.yaml",
            "violated_by": ".spark/policy/policy.yaml",
            "reason": "changed",
        }
    ]
    assert result.err  # diagnostics still go to stderr


def test_resolve_does_not_mutate_its_input_layers():
    pack = ordered_pack()
    before = json.dumps(pack.rules, sort_keys=True)
    resolve([pack, layer({"sec": {"strict_mode": True}}, "proj.yaml")])
    assert json.dumps(pack.rules, sort_keys=True) == before


def test_cli_three_violations_in_one_run_are_three_stderr_lines_in_stable_order(make_project, run_cli):
    # AC-2.5 end to end: one exit, all violations, identical across two runs.
    root = make_project(
        files={
            "policy.yaml": "schema_version: 1\nname: P\nimports:\n  - company:lockpack\n"
            "rules:\n  security:\n    tls: optional\n    strict_mode: true\n    final: false\n"
            "    ids: !override []\n",
            "packs/platform/lockpack/pack.yaml": PACK,
            "packs/platform/lockpack/policy.yaml": LOCK_POLICY + "    ids: [a]\n",
            "packs/platform/lockpack/lock.md": "# lock\n",
        }
    )
    first = run_cli("resolve", str(root))
    second = run_cli("resolve", str(root))
    assert first.code == 1 and first.out == b""
    lines = first.err.decode().splitlines()
    assert [line.split(": ")[2] for line in lines] == [
        "rules.security.final",
        "rules.security.ids",
        "rules.security.tls",
    ]
    assert (first.code, first.err) == (second.code, second.err)


def _declaring_pack(level_label="packs/x/esc/policy.yaml"):
    return layer(
        {"sec": {"ordered": {"minimum_reviewers": "lower-is-stricter"}}},
        level_label,
        "pack",
        "company:esc",
        "universal",
    )


def test_ordered_declared_by_a_layer_after_the_lock_does_not_open_an_escape():
    # review F2: a pack more specific than the lock cannot declare its own escape
    locked = org({"sec": {"final": True, "minimum_reviewers": 2}})
    result = resolve([locked, _declaring_pack(), layer({"sec": {"minimum_reviewers": 0}}, "proj.yaml")])
    assert reasons(result) == [("rules.sec.minimum_reviewers", "changed")]


def test_ordered_declared_before_or_by_the_locking_layer_is_honoured():
    locked = org({"sec": {"final": True, "minimum_reviewers": 2}})
    result = resolve([_declaring_pack(), locked, layer({"sec": {"minimum_reviewers": 1}}, "proj.yaml")])
    assert result.violations == [] and result.rules["sec"]["minimum_reviewers"] == 1


# --- review round-1 fixes: F3, F5, F6, F7 ------------------------------------

HEAD = "schema_version: 1\nname: P\n"


def test_recursive_yaml_alias_is_a_load_error_not_a_traceback(make_project, run_cli):
    # F3 / NFR-4
    root = make_project(files={"policy.yaml": HEAD + "rules: &a\n  x: *a\n"})
    res = run_cli("resolve", str(root))
    assert res.code == 2 and res.out == b"" and b"recursive YAML alias" in res.err


def test_company_pack_id_must_match_its_directory(make_project, run_cli):
    # F5 / plan D-c
    root = make_project(
        files={
            "policy.yaml": HEAD + "imports:\n  - company:lockpack\n",
            "packs/platform/lockpack/pack.yaml": PACK.replace("id: lockpack", "id: other"),
            "packs/platform/lockpack/policy.yaml": "rules: {}\n",
            "packs/platform/lockpack/lock.md": "# x\n",
        }
    )
    res = run_cli("resolve", str(root))
    assert res.code == 2 and res.out == b"" and b"does not match the directory name" in res.err


def test_json_with_a_schema_error_prints_the_violations_document(make_project, run_cli):
    # F6 / plan §1
    root = make_project(files={"policy.yaml": "name: P\nrules: {}\n"})
    res = run_cli("resolve", str(root), "--json")
    doc = json.loads(res.out)
    assert res.code == 1 and doc["resolve_format"] == "1.0.0"
    assert doc["violations"][0]["locked_by"] is None
    assert doc["violations"][0]["violated_by"].endswith("policy.yaml")
    assert run_cli("resolve", str(root)).out == b""


def test_validate_checks_extends_ancestors_in_the_tree(tmp_path, run_cli):
    # F7
    (tmp_path / "base").mkdir()
    (tmp_path / "policy.yaml").write_text(HEAD + "extends: base\nrules: {}\n", encoding="utf-8")
    (tmp_path / "base" / "policy.yaml").write_text("name: 5\n", encoding="utf-8")
    res = run_cli("validate", str(tmp_path))
    assert res.code == 1 and b"base/policy.yaml" in res.err


def test_validate_tree_does_not_check_a_hidden_pack_policy_as_a_project_policy(tmp_path, run_cli):
    # review r2 (F12): `.spark/` packs are skipped as packs, so their policy.yaml
    # must not fall through to the project-policy schema
    (tmp_path / "policy.yaml").write_text(HEAD, encoding="utf-8")
    pack = tmp_path / ".spark" / "policy" / "packs" / "platform" / "lockpack"
    pack.mkdir(parents=True)
    (pack / "pack.yaml").write_text(PACK, encoding="utf-8")
    (pack / "policy.yaml").write_text("rules: {}\n", encoding="utf-8")
    (pack / "lock.md").write_text("# x\n", encoding="utf-8")
    res = run_cli("validate", str(tmp_path))
    assert res.code == 0 and res.err == b""


def _imports(items):
    return f"imports:\n{items}" if items else ""


def _esc_project(make_project, org_imports, project_imports, value):
    files = {
        "policy.yaml": f"{HEAD}extends: org\n{_imports(project_imports)}rules:\n  sec:\n    minimum_reviewers: {value}\n",
        "org/policy.yaml": f"{HEAD}{_imports(org_imports)}rules:\n  sec:\n    final: true\n    minimum_reviewers: 2\n",
        "packs/platform/esc/pack.yaml": PACK.replace("lockpack", "esc"),
        "packs/platform/esc/policy.yaml": "rules:\n  sec:\n    ordered:\n      minimum_reviewers: lower-is-stricter\n",
        "packs/platform/esc/esc.md": "# esc\n",
    }
    return make_project(files=files)


def test_a_pack_imported_by_the_project_cannot_open_an_escape_from_an_ancestors_lock(make_project, run_cli):
    # review F2 (round 2): the lock lives in an `extends` ancestor, the pack is the project's own
    root = _esc_project(make_project, "", "  - company:esc\n", 1)  # stricter only under the escape
    res = run_cli("resolve", str(root))
    assert res.code == 1 and res.out == b"" and b"minimum_reviewers" in res.err


def test_a_pack_imported_by_the_locking_file_is_honoured(make_project, run_cli):
    root = _esc_project(make_project, "  - company:esc\n", "", 1)
    res = run_cli("resolve", str(root))
    assert res.code == 0, res.err
    assert json.loads(res.out)["rules"]["sec"]["minimum_reviewers"] == 1
