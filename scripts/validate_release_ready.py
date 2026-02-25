#!/usr/bin/env python3
from pathlib import Path
import json
import sys


REQUIRED = {"ios", "android", "cordova"}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_release_ready.py <state-file>", file=sys.stderr)
        return 1

    state_file = Path(sys.argv[1])
    if not state_file.exists():
        print(f"Missing state file: {state_file}", file=sys.stderr)
        return 1

    state = json.loads(state_file.read_text())
    artifacts = set((state.get("artifacts") or {}).keys())
    missing = sorted(REQUIRED - artifacts)
    if missing:
        print(f"Release not ready. Missing platforms: {', '.join(missing)}", file=sys.stderr)
        return 2

    print("ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
