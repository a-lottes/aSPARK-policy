"""Merge core unit tests (resolve-cli T5): pure, on in-memory layers."""

from aspark_policy._layers import Layer
from aspark_policy._loader import Override
from aspark_policy._merge import resolve


def layer(rules, file="f.yaml", kind="policy", pack="none", name="L", pack_kind=None):
    return Layer(kind=kind, name=name, pack=pack, file=file, rules=rules, pack_kind=pack_kind)


def origins(result):
    return {o["key"]: (o["level"], o["file"]) for o in result.origins}


def test_specific_scalar_wins_and_origin_records_the_winning_level():
    # AC-1.3
    result = resolve([layer({"r": {"n": 1}}, "a.yaml"), layer({"r": {"n": 2}}, "b.yaml")])
    assert result.rules == {"r": {"n": 2}}
    assert origins(result)["rules.r.n"] == (1, "b.yaml")


def test_rule_on_one_level_is_unchanged_with_that_level_as_origin():
    # AC-1.5
    result = resolve([layer({"a": {"x": 1}}, "a.yaml"), layer({"b": {"y": 2}}, "b.yaml")])
    assert result.rules == {"a": {"x": 1}, "b": {"y": 2}}
    assert origins(result) == {"rules.a.x": (0, "a.yaml"), "rules.b.y": (1, "b.yaml")}


def test_lists_concatenate_general_to_specific_keeping_first_occurrence():
    # AC-1.4
    result = resolve([layer({"r": {"d": ["a", "b"]}}), layer({"r": {"d": ["c", "a", "d"]}})])
    assert result.rules["r"]["d"] == ["a", "b", "c", "d"]
    by_key = origins(result)
    assert by_key["rules.r.d[0]"][0] == 0  # `a` keeps the general layer as origin
    assert by_key["rules.r.d[2]"][0] == 1
    assert by_key["rules.r.d[3]"][0] == 1


def test_list_dedup_is_by_whole_value_equality_and_keeps_types_apart():
    result = resolve([layer({"r": {"d": [1, {"a": 1}]}}), layer({"r": {"d": [True, 1, {"a": 1}, {"a": 2}]}})])
    # `true` is not `1`; equal mappings collapse.
    assert result.rules["r"]["d"] == [1, {"a": 1}, True, {"a": 2}]


def test_override_keeps_only_the_specific_list():
    result = resolve([layer({"r": {"d": ["a", "b"]}}), layer({"r": {"d": Override(["z"])}})])
    assert result.rules["r"]["d"] == ["z"]
    assert type(result.rules["r"]["d"]) is list  # marker never leaks into output
    assert origins(result) == {"rules.r.d[0]": (1, "f.yaml")}


def test_type_change_replaces_including_null():
    result = resolve([layer({"r": {"a": {"x": 1}, "b": 1}}), layer({"r": {"a": "s", "b": None}})])
    assert result.rules == {"r": {"a": "s", "b": None}}


def test_every_leaf_and_list_element_has_exactly_one_origin():
    # AC-1.6
    rules = {"r": {"s": 1, "l": [1, 2], "m": {"k": "v"}, "empty_m": {}, "empty_l": []}}
    result = resolve([layer(rules, pack="aspark:x", file="packs/c/x/policy.yaml")])
    keys = [o["key"] for o in result.origins]
    assert keys == [
        "rules.r.empty_l",
        "rules.r.empty_m",
        "rules.r.l[0]",
        "rules.r.l[1]",
        "rules.r.m.k",
        "rules.r.s",
    ]
    assert len(keys) == len(set(keys))
    assert all(o["pack"] == "aspark:x" and o["level"] == 0 for o in result.origins)


def test_pack_is_none_for_local_files():
    result = resolve([layer({"r": {"a": 1}})])
    assert result.origins[0]["pack"] == "none"


def test_list_index_origins_sort_numerically():
    result = resolve([layer({"r": {"d": list(range(12))}})])
    assert [o["key"] for o in result.origins][:3] == ["rules.r.d[0]", "rules.r.d[1]", "rules.r.d[2]"]
    assert [o["key"] for o in result.origins][-1] == "rules.r.d[11]"


def test_awkward_key_segments_are_bracket_quoted():
    result = resolve([layer({"r": {"a.b": 1, 'q"t': 2}})])
    assert [o["key"] for o in result.origins] == ['rules.r["a.b"]', 'rules.r["q\\"t"]']


def test_empty_mapping_override_and_empty_rules():
    assert resolve([layer({})]).rules == {}
    assert resolve([layer({}), layer({})]).origins == []
    result = resolve([layer({"r": {"a": {}}}), layer({"r": {"a": {"x": 1}}})])
    assert result.rules == {"r": {"a": {"x": 1}}}
    assert origins(result) == {"rules.r.a.x": (1, "f.yaml")}


def test_merge_does_not_mutate_the_input_layers():
    rules = {"r": {"d": ["a"]}}
    resolve([layer(rules), layer({"r": {"d": ["b"]}})])
    assert rules == {"r": {"d": ["a"]}}
