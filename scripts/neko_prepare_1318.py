"""Prepare a new config COPY for 1.3.18; never edit the input or run the host."""

from copy import deepcopy
from pathlib import Path

import argparse
import tomllib
import tomlkit


def split_attention_drift(data):
    """Carry the old shared settings to both scopes; explicit new values win."""
    result = deepcopy(data)
    experimental = result.get("experimental", {})
    if "attention_drift" not in experimental:
        return result
    legacy = experimental.pop("attention_drift")
    if not isinstance(legacy, dict):
        raise ValueError("Legacy attention_drift must be a table")
    for key in ("group_attention_drift", "private_attention_drift"):
        current = experimental.get(key, {})
        if not isinstance(current, dict):
            raise ValueError(key + " must be a table")
        experimental[key] = {**deepcopy(legacy), **current}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Previously copied bot config")
    parser.add_argument("--output", required=True, type=Path, help="New copy; must not exist")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise ValueError("Input and output must be different copies")
    original = tomllib.loads(args.input.read_text(encoding="utf-8"))
    prepared = split_attention_drift(original)
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        args.output.chmod(0o600)
        output.write(tomlkit.dumps(prepared))
    print("Prepared config copy; input unchanged. Host version migration still required.")


if __name__ == "__main__":
    main()
