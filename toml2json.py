#!/usr/bin/env python3
"""toml2json - Convert between TOML and JSON.

One file. Zero deps. Bridge formats.

Usage:
  toml2json.py to-json config.toml       → TOML to JSON
  toml2json.py to-toml config.json       → JSON to TOML
  toml2json.py validate config.toml      → check TOML syntax
  toml2json.py get config.toml key.path  → extract value
  cat config.toml | toml2json.py to-json - → stdin
"""

import argparse
import json
import sys

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def read_toml(path: str) -> dict:
    if tomllib is None:
        print("Python 3.11+ required for TOML support", file=sys.stderr)
        sys.exit(1)
    if path == "-":
        return tomllib.loads(sys.stdin.read())
    with open(path, "rb") as f:
        return tomllib.load(f)


def to_toml(data: dict, prefix: str = "") -> str:
    lines = []
    tables = []
    for k, v in data.items():
        if isinstance(v, dict):
            tables.append((k, v))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            for item in v:
                lines.append(f"\n[[{prefix}{k}]]")
                lines.append(to_toml(item))
        else:
            lines.append(f"{k} = {toml_value(v)}")
    for k, v in tables:
        section = f"{prefix}{k}"
        lines.append(f"\n[{section}]")
        lines.append(to_toml(v, f"{section}."))
    return "\n".join(lines)


def toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(v)
    if isinstance(v, str):
        if "\n" in v:
            return f'"""\n{v}"""'
        return json.dumps(v)
    if isinstance(v, list):
        items = ", ".join(toml_value(i) for i in v)
        return f"[{items}]"
    if isinstance(v, dict):
        items = ", ".join(f"{k} = {toml_value(val)}" for k, val in v.items())
        return f"{{{items}}}"
    return str(v)


def get_path(data: dict, path: str):
    for key in path.split("."):
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data


def cmd_to_json(args):
    data = read_toml(args.file)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_to_toml(args):
    if args.file == "-":
        data = json.loads(sys.stdin.read())
    else:
        with open(args.file) as f:
            data = json.load(f)
    print(to_toml(data))


def cmd_validate(args):
    try:
        data = read_toml(args.file)
        keys = len(data)
        print(f"✅ Valid TOML ({keys} top-level keys)")
    except Exception as e:
        print(f"❌ Invalid TOML: {e}", file=sys.stderr)
        return 1


def cmd_get(args):
    data = read_toml(args.file)
    val = get_path(data, args.path)
    if val is None:
        print("null")
        return 1
    if isinstance(val, (dict, list)):
        print(json.dumps(val, indent=2))
    else:
        print(val)


def main():
    p = argparse.ArgumentParser(description="Convert between TOML and JSON")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("to-json"); s.add_argument("file")
    s = sub.add_parser("to-toml"); s.add_argument("file")
    s = sub.add_parser("validate"); s.add_argument("file")
    s = sub.add_parser("get"); s.add_argument("file"); s.add_argument("path")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 1
    cmds = {"to-json": cmd_to_json, "to-toml": cmd_to_toml,
            "validate": cmd_validate, "get": cmd_get}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
