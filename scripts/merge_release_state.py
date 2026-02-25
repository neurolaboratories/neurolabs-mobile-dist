#!/usr/bin/env python3
from pathlib import Path
import json
import sys


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "Usage: merge_release_state.py <state-dir> <version> <platform> <asset-url> <checksum>",
            file=sys.stderr,
        )
        return 1

    state_dir = Path(sys.argv[1])
    version = sys.argv[2]
    platform = sys.argv[3]
    asset_url = sys.argv[4]
    checksum = sys.argv[5]

    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"{version}.json"

    if state_file.exists():
        state = json.loads(state_file.read_text())
    else:
        state = {"version": version, "artifacts": {}}

    state["artifacts"][platform] = {
        "asset_url": asset_url,
        "checksum_sha256": checksum,
    }

    state_file.write_text(json.dumps(state, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
