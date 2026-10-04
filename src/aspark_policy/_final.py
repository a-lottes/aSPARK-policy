"""`final` locks and pack-declared `ordered` rules (spec US-2).

A mapping under `rules` with `final: true` locks its subtree for every later
layer. A later layer may only add keys that did not exist, or move a
pack-declared ordered scalar in the stricter direction; any other difference at
a pre-existing locked path is a violation and the locked value is kept.
"""

import json
from dataclasses import dataclass

from ._loader import Override

HIGHER = "higher-is-stricter"
LOWER = "lower-is-stricter"
DIRECTIONS = (HIGHER, LOWER)

REMOVED = "removed"
CHANGED = "changed"
WEAKENED = "weakened"
BASELINE_FINAL = "baseline-final"
ORDERED_INVALID = "ordered-invalid"


@dataclass(frozen=True)
class Violation:
    key: str
    locked_by: str
    violated_by: str
    reason: str
    detail: str = ""  # explanation for reasons that need more than the code

    def sort_key(self) -> tuple[str, str, str, str]:
        return (self.key, self.violated_by, self.reason, self.locked_by)

    def message(self) -> str:
        if self.reason == BASELINE_FINAL:
            return "baseline-final: a `baseline` pack must not mark a rule `final`"
        if self.reason == ORDERED_INVALID:
            return f"ordered-invalid: {self.detail}"
        return f"final lock violated: {self.reason} (locked by {self.locked_by})"


def canon(value: object) -> str:
    """Canonical JSON text: equality that keeps `true` distinct from `1`."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def plain(value: object) -> object:
    """Deep copy with `Override` markers turned into ordinary lists."""
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


def format_path(parts: tuple) -> str:
    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        elif any(ch in part for ch in '.[]"') or part == "":
            out += f"[{json.dumps(part, ensure_ascii=True)}]"
        else:
            out += f".{part}" if out else part
    return out


def sort_key(parts: tuple) -> tuple:
    return tuple((1, p) if isinstance(p, int) else (0, p) for p in parts)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_stricter(old: object, new: object, direction: str) -> bool | None:
    """True/False if `new` is stricter/weaker than `old`; None if not comparable."""
    comparable = (isinstance(old, bool) and isinstance(new, bool)) or (
        _is_number(old) and _is_number(new)
    )
    if not comparable:
        return None
    return (new > old) if direction == HIGHER else (new < old)


def find_final_paths(value: object, path: tuple = ()) -> list[tuple]:
    """Paths of every mapping carrying `final: true` (for baseline-final checks)."""
    found: list[tuple] = []
    if isinstance(value, dict):
        if value.get("final") is True and path:
            found.append(path)
        for key, child in value.items():
            found.extend(find_final_paths(child, path + (key,)))
    return found


def locked_change_reason(old: object, new: object) -> str | None:
    """Why `new` may not replace the locked `old` (None: no real change).

    Handles everything except ordered scalars, which the caller decides first.
    """
    if canon(new) == canon(old):
        return None
    if isinstance(old, list) and isinstance(new, list):
        if isinstance(new, Override):
            kept = {canon(v) for v in new}
            return REMOVED if any(canon(v) not in kept for v in old) else CHANGED
        known = {canon(v) for v in old}
        return None if all(canon(v) in known for v in new) else CHANGED
    if new is None:
        return REMOVED
    if isinstance(old, (dict, list)) and not isinstance(new, type(old)):
        return REMOVED
    return CHANGED
