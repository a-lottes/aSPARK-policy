"""Layer merging with per-value origins (spec US-1, US-2).

`resolve(layers)` is a pure function: layers in, (rules, origins, ordered,
violations) out. A scalar is replaced by the more specific layer, mappings
merge deeply, lists concatenate general to specific keeping the first
occurrence, and `!override` replaces. `final` locks are enforced as described
in `_final`.
"""

from dataclasses import dataclass, field, replace

from . import _final
from ._final import Violation, canon, format_path, plain, sort_key
from ._layers import Layer
from ._loader import Override


@dataclass
class Resolution:
    rules: dict
    origins: list[dict]
    ordered: list[dict]
    violations: list[Violation] = field(default_factory=list)


@dataclass(frozen=True)
class _Lock:
    path: tuple
    by: int  # layer index that set `final: true`


def _origin_tree(value: object, level: int) -> object:
    """Origin of every part of `value`, all supplied by layer `level`."""
    if isinstance(value, dict) and value:
        return {k: _origin_tree(v, level) for k, v in value.items()}
    if isinstance(value, list) and value:
        return [level] * len(value)
    return level


def _leaves(value: object, org: object, path: tuple, out: list[tuple[tuple, int]]) -> None:
    if isinstance(value, dict) and value:
        for key in value:
            _leaves(value[key], org[key], path + (key,), out)
    elif isinstance(value, list) and value:
        for index, level in enumerate(org):
            out.append((path + (index,), level))
    else:
        out.append((path, org))


class _Merger:
    def __init__(self, layers: list[Layer], ordered: dict[tuple, tuple[str, str]]):
        self.layers = layers
        self.ordered = ordered
        policy_levels = [i for i, layer in enumerate(layers) if layer.kind == "policy"]
        # F2: a pack counts as the policy file that imported it, not as its list position
        self.rank = [
            policy_levels[layer.imported_by]
            if layer.kind == "pack" and layer.imported_by is not None
            else i
            for i, layer in enumerate(layers)
        ]
        self.violations: list[Violation] = []

    def violate(self, path: tuple, lock: _Lock, level: int, reason: str) -> None:
        self.violations.append(
            Violation(
                key=format_path(path),
                locked_by=self.layers[lock.by].file,
                violated_by=self.layers[level].file,
                reason=reason,
            )
        )

    def merge(self, a, ao, b, level: int, path: tuple, lock: _Lock | None):
        """Merge specific value `b` (from layer `level`) onto general `a`."""
        if lock is None and isinstance(a, dict) and a.get("final") is True:
            lock = _Lock(path, ao["final"])
        if isinstance(a, dict) and isinstance(b, dict):
            return self.merge_mappings(a, ao, b, level, path, lock)
        if lock is None and isinstance(a, dict) and self.violate_nested_locks(a, ao, level, path):
            return a, ao  # AC-2.1: replacing an ancestor cannot drop a lock below it
        if lock is not None:
            return self.merge_locked(a, ao, b, level, path, lock)
        if isinstance(a, list) and isinstance(b, list) and not isinstance(b, Override):
            values, origins = list(a), list(ao) if a else []
            seen = {canon(v) for v in values}
            for item in b:
                key = canon(item)
                if key not in seen:
                    seen.add(key)
                    values.append(plain(item))
                    origins.append(level)
            return values, (origins if values else level)
        return plain(b), _origin_tree(plain(b), level)

    def violate_nested_locks(self, a: dict, ao, level: int, path: tuple) -> bool:
        """Report `removed` for every `final` block inside `a`; True if there was one."""
        found = _final.find_final_paths(a, path)
        for locked in found:
            origin = ao
            for key in locked[len(path):]:
                origin = origin[key]
            self.violate(locked, _Lock(locked, origin["final"]), level, _final.REMOVED)
        return bool(found)

    def merge_mappings(self, a, ao, b, level, path, lock):
        out: dict = {}
        org: dict = {}
        for key in a:
            if key in b:
                out[key], org[key] = self.merge(
                    a[key], ao[key], b[key], level, path + (key,), lock
                )
            else:
                out[key], org[key] = a[key], ao[key]
        for key in b:
            if key not in a:  # additive, also inside a locked block (AC-2.4)
                out[key] = plain(b[key])
                org[key] = _origin_tree(out[key], level)
        return out, (org if out else level)

    def merge_locked(self, a, ao, b, level, path, lock):
        stricter = self.stricter_ordered(a, b, path, lock)
        if stricter:
            return b, level  # AC-2.3: moved in the stricter direction
        reason = _final.locked_change_reason(a, b)
        if reason is None:
            return a, ao
        if stricter is False:
            reason = _final.WEAKENED
        self.violate(path, lock, level, reason)
        return a, ao

    def stricter_ordered(self, a, b, path: tuple, lock: _Lock) -> bool | None:
        declared = self.ordered.get(path)
        if declared is None or declared[2] > lock.by or self.rank[declared[2]] > self.rank[lock.by]:
            return None  # F2: only the locking layer's file or an earlier one may declare
        verdict = _final.is_stricter(a, b, declared[0])
        return verdict if canon(a) != canon(b) else None


def _strip_ordered(
    layers: list[Layer], violations: list[Violation]
) -> tuple[list[Layer], dict[tuple, tuple[str, str, int]]]:
    """Copies of `layers` without the reserved `ordered` keys, plus what they declared."""
    declared: dict[tuple, tuple[str, str, int]] = {}

    def walk(node: dict, path: tuple, layer: Layer, level: int) -> dict:
        out = {}
        for key, value in node.items():
            if key == "ordered" and len(path) > 1:  # `rules.ordered` is just a rule domain
                _declare(value, path, layer, level)
                continue
            out[key] = walk(value, path + (key,), layer, level) if isinstance(value, dict) else value
        return out

    def _declare(value, path: tuple, layer: Layer, level: int) -> None:
        def bad(reason: str, key: tuple = path) -> None:
            violations.append(
                Violation(format_path(key), layer.file, layer.file, _final.ORDERED_INVALID, reason)
            )

        if layer.kind != "pack":
            bad("`ordered` may only be declared by a pack")
            return
        if not isinstance(value, dict):
            bad("`ordered` must map keys to a direction")
            return
        for child, direction in value.items():
            key = path + (child,)
            if direction not in _final.DIRECTIONS:
                bad(f"direction must be one of {', '.join(_final.DIRECTIONS)}", key)
            elif key in declared and declared[key][0] != direction:
                bad(f"direction conflicts with {declared[key][1]}", key)
            else:
                declared.setdefault(key, (direction, layer.pack, level))

    stripped = [
        replace(layer, rules=walk(layer.rules, ("rules",), layer, level))
        for level, layer in enumerate(layers)
    ]
    return stripped, declared


def resolve(layers: list[Layer]) -> Resolution:
    violations: list[Violation] = []
    for layer in layers:  # AC-2.6: a baseline pack never locks anything
        if layer.kind == "pack" and layer.pack_kind == "baseline":
            for path in _final.find_final_paths(layer.rules, ("rules",)):
                violations.append(
                    Violation(format_path(path), layer.file, layer.file, _final.BASELINE_FINAL)
                )
    layers, ordered = _strip_ordered(layers, violations)
    merger = _Merger(layers, ordered)

    rules: dict = {}
    org: dict = {}
    for level, layer in enumerate(layers):
        incoming = layer.rules
        for key, value in incoming.items():
            if key in rules:
                rules[key], org[key] = merger.merge(
                    rules[key], org[key], value, level, ("rules", key), None
                )
            else:
                rules[key] = plain(value)
                org[key] = _origin_tree(rules[key], level)

    leaves: list[tuple[tuple, int]] = []
    for key in rules:
        _leaves(rules[key], org[key], ("rules", key), leaves)
    leaves.sort(key=lambda item: sort_key(item[0]))
    origins = [
        {
            "key": format_path(path),
            "level": level,
            "pack": layers[level].pack,
            "file": layers[level].file,
        }
        for path, level in leaves
    ]
    ordered_out = [
        {"key": format_path(path), "direction": direction, "pack": pack}
        for path, (direction, pack, _) in sorted(ordered.items(), key=lambda i: sort_key(i[0]))
    ]
    all_violations = sorted(violations + merger.violations, key=Violation.sort_key)
    return Resolution(rules=rules, origins=origins, ordered=ordered_out, violations=all_violations)
