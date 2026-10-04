"""Command line entry point: argument parsing, streams and exit codes.

Exit codes (spec NFR-6): 0 ok; 1 policy/validation violation; 2 usage or IO
error. Results go to stdout, diagnostics to stderr as
`error: <file>: <key|->: <reason>`.
"""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from ._layers import ResolveError, discover_imports, discover_project
from ._merge import resolve
from ._validate import ValidateInputError, validate

RESOLVE_FORMAT = "1.0.0"


def _write_json(doc: dict) -> None:
    text = json.dumps(doc, sort_keys=True, ensure_ascii=True, indent=2) + "\n"
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


def _write_errors(items: list[tuple[str, str, str]]) -> None:
    for file, key, reason in items:
        sys.stderr.write(f"error: {file}: {key or '-'}: {reason}\n")
    sys.stderr.flush()


def _resolve(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    parser = args.parser
    if args.directory is not None and args.imports is not None:
        parser.error("<dir> and --imports cannot be combined")
    if args.directory is None and args.imports is None:
        parser.error("give a project <dir> or --imports")
    try:
        found = (
            discover_imports(args.imports)
            if args.imports is not None
            else discover_project(Path(args.directory))
        )
    except ResolveError as exc:
        _write_errors(exc.items)
        if args.json and exc.code == 1:  # schema errors: same document shape, no locker
            _write_json(
                {
                    "resolve_format": RESOLVE_FORMAT,
                    "violations": [
                        {"key": key, "locked_by": None, "violated_by": file, "reason": reason}
                        for file, key, reason in exc.items
                    ],
                }
            )
        return exc.code

    result = resolve(found.layers)
    if result.violations:
        _write_errors([(v.violated_by, v.key, v.message()) for v in result.violations])
        if args.json:
            _write_json(
                {
                    "resolve_format": RESOLVE_FORMAT,
                    "violations": [
                        {
                            "key": v.key,
                            "locked_by": v.locked_by,
                            "violated_by": v.violated_by,
                            "reason": v.reason,
                        }
                        for v in result.violations
                    ],
                }
            )
        return 1
    _write_json(
        {
            "resolve_format": RESOLVE_FORMAT,
            "input": {"policy": found.policy, "imports": found.imports},
            "layers": [
                {
                    "level": level,
                    "kind": layer.kind,
                    "name": layer.name,
                    "pack": layer.pack,
                    "file": layer.file,
                }
                for level, layer in enumerate(found.layers)
            ],
            "rules": result.rules,
            "origins": result.origins,
            "ordered": result.ordered,
        }
    )
    return 0


def _validate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    target = Path(args.path) if args.path is not None else Path("packs")
    try:
        if args.path is None and not target.is_dir():
            raise ValidateInputError("-", "no path given and no ./packs directory here")
        report = validate(target)
    except ValidateInputError as exc:
        _write_errors([(exc.file, "-", exc.reason)])
        return 2
    if report.errors:
        _write_errors(report.errors)
    if args.json:
        _write_json(
            {
                "resolve_format": RESOLVE_FORMAT,
                "errors": [{"file": f, "key": k, "reason": r} for f, k, r in report.errors],
            }
        )
    elif not report.errors:
        sys.stdout.write(f"ok: validated {report.files} file{'s' if report.files != 1 else ''}\n")
        sys.stdout.flush()
    return 1 if report.errors else 0


_DESCRIPTION = "Resolve and validate aSPARK policy files. Offline; no network, no model."

_EPILOG = """\
Exit codes: 0 ok; 1 policy or validation violation; 2 usage or IO error.
Results go to stdout, diagnostics to stderr as `error: <file>: <key>: <reason>`.
"""


def _parser_kwargs() -> dict:
    # Python 3.14 colours argparse help by default; output must never carry ANSI.
    return {"color": False} if sys.version_info >= (3, 14) else {}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aspark-policy",
        description=_DESCRIPTION,
        epilog=_EPILOG + "\nExample:\n  aspark-policy resolve --imports aspark:owasp,aspark:java\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        **_parser_kwargs(),
    )
    parser.add_argument("--version", action="version", version=f"aspark-policy {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="{resolve,validate}")

    resolve_cmd = sub.add_parser(
        "resolve",
        help="print the effective policy as JSON, with the origin of every value",
        description=(
            "Compute the effective policy of a project directory (its\n"
            ".spark/policy/policy.yaml or policy.yaml, its `extends` chain and imports)\n"
            "or of an explicit import list, and print it as one JSON document.\n"
            "A `final` violation fails with exit 1."
        ),
        epilog="Example:\n  aspark-policy resolve --imports aspark:owasp,aspark:java\n"
        "  aspark-policy resolve ./my-project --json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        **_parser_kwargs(),
    )
    resolve_cmd.add_argument("directory", nargs="?", help="project directory (not with --imports)")
    resolve_cmd.add_argument(
        "--imports", help="comma-separated pack ids, e.g. aspark:owasp,aspark:java (not with <dir>)"
    )
    resolve_cmd.add_argument(
        "--json", action="store_true", help="on a violation, print the violations as JSON on stdout"
    )
    resolve_cmd.set_defaults(func=_resolve, parser=resolve_cmd)

    validate_cmd = sub.add_parser(
        "validate",
        help="check files against the schemas and packs for integrity",
        description=(
            "Validate a pack.yaml, a policy.yaml, a pack directory or a whole tree of\n"
            "packs against the JSON Schemas, and check pack integrity (layout, id,\n"
            "baseline vs final). Without a path it validates ./packs."
        ),
        epilog="Example:\n  aspark-policy validate packs/\n  aspark-policy validate packs/cloud/aws --json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        **_parser_kwargs(),
    )
    validate_cmd.add_argument("path", nargs="?", help="file or directory (default: ./packs)")
    validate_cmd.add_argument(
        "--json", action="store_true", help="print the error list as JSON on stdout"
    )
    validate_cmd.set_defaults(func=_validate, parser=validate_cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args, parser)
    except SystemExit as exc:  # argparse: usage error (2) or --help/--version (0)
        return exc.code if isinstance(exc.code, int) else 2
