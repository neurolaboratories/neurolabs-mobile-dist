#!/usr/bin/env python3
"""Stamp one platform manifest (ios/android/cordova) for a release, MONOTONICALLY.

Replaces the inline `latest["version"] = os.environ["VERSION"]` heredoc that
both dist-release.yml and manual-promote.yml carried. That write was
unconditional, so whichever release ran LAST won — and a maintenance backport
always runs last by definition. Verified downgrades it produced on `main`:

    android.json   v1.7.0 -> v1.6.7   (2026-08-05)
    android.json   v1.7.1 -> v1.6.9   (2026-08-18)
    android.json   v1.7.2 -> v1.6.11  (2026-08-20)
    cordova.json   v1.7.0 -> v1.6.7   (2026-08-05)
    cordova.json   v1.7.1 -> v1.6.9   (2026-08-18)
    ios.json       v1.7.0 -> v1.6.7   (2026-08-05)
    ios.json       v1.7.1 -> v1.6.9   (2026-08-18)
    ios.json       v1.7.2 -> v1.6.11  (2026-08-20)
    ios.json       v1.7.7 -> v1.6.12  (2026-09-21)

Each was masked by the next 1.7.x release overwriting it again, until v1.6.12
landed with no 1.7.x behind it.

The manifest is therefore LINE-AWARE:

  * `lines["<major>.<minor>"]` is the head of each release line and always
    records the release that just shipped, backport or not.
  * `latest` mirrors the highest line and is only ever promoted forward.
    A backport updates its own line and leaves `latest` alone.

Rules enforced:
  * a release may never move its OWN line backwards (hard failure — that means
    an out-of-order or replayed dispatch, which is a bug, not a backport);
  * a release older than `latest` records its line and exits 0 WITHOUT touching
    `latest` (that is a backport, which is legitimate);
  * a release newer than or equal to `latest` promotes `latest`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import semver  # noqa: E402


def _platform_extras(platform: str, entry: dict, maven: dict | None) -> None:
    """Regenerate the copy/paste snippets so they track the asset that just
    landed — they used to be hand-written and sat frozen at v1.2.5."""
    if platform == "android":
        entry["gradle_example"] = f'implementation(files("libs/{entry["asset_name"]}"))'
        if maven:
            entry["maven"] = maven
            if maven.get("group_id") and maven.get("artifact_id") and maven.get("version"):
                if maven.get("repository_url"):
                    entry["gradle_maven_repository_example"] = (
                        f'maven {{ url = uri("{maven["repository_url"]}") }}'
                    )
                entry["gradle_maven_dependency_example"] = (
                    f'implementation("{maven["group_id"]}:'
                    f'{maven["artifact_id"]}:{maven["version"]}")'
                )
        else:
            for key in ("maven", "gradle_maven_repository_example",
                        "gradle_maven_dependency_example"):
                entry.pop(key, None)
    elif platform == "cordova":
        entry["install_example"] = f'cordova plugin add {entry["asset_url"]}'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--version", required=True)
    ap.add_argument("--asset-url", required=True)
    ap.add_argument("--asset-name", required=True)
    ap.add_argument("--checksum", required=True)
    ap.add_argument("--maven-json", default="",
                    help='android only: {"maven": {...}} as produced by the workflow')
    args = ap.parse_args()

    try:
        version = args.version.strip()
        line = semver.line_of(version)
    except semver.InvalidVersion as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if f"/releases/download/{version}/" not in args.asset_url:
        print(
            f"error: asset_url does not carry the /releases/download/{version}/ "
            f"segment: {args.asset_url}",
            file=sys.stderr,
        )
        return 1

    data = json.loads(args.manifest.read_text())
    platform = data.get("platform", "")

    maven = None
    if args.maven_json.strip():
        maven = (json.loads(args.maven_json) or {}).get("maven") or None

    entry = {
        "version": version,
        "asset_name": args.asset_name,
        "asset_url": args.asset_url,
        "checksum_sha256": args.checksum,
    }
    _platform_extras(platform, entry, maven)

    lines = data.setdefault("lines", {})
    # One-time migration: an untracked `latest` is the head of its own line.
    current_latest = data.get("latest") or {}
    if not lines and current_latest.get("version"):
        lines[semver.line_of(current_latest["version"])] = dict(current_latest)

    previous_in_line = (lines.get(line) or {}).get("version")
    if previous_in_line and semver.compare(version, previous_in_line) < 0:
        print(
            f"error: refusing to move the {line}.x line backwards: "
            f"{previous_in_line} -> {version}. A newer release already shipped "
            f"on this line; an out-of-order dispatch is a bug, not a backport.",
            file=sys.stderr,
        )
        return 2
    lines[line] = entry

    latest_version = current_latest.get("version")
    if latest_version and semver.compare(version, latest_version) < 0:
        print(
            f"note: {version} is a {line}.x backport published behind "
            f"{latest_version}; recorded under lines[\"{line}\"] and `latest` "
            f"left at {latest_version}.",
        )
    else:
        data["latest"] = dict(entry)

    # Keep key order stable: lines last, sorted newest line first.
    data["lines"] = {
        k: lines[k] for k in sorted(lines, key=lambda k: semver.sort_key(f"v{k}.0"), reverse=True)
    }
    args.manifest.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{args.manifest}: lines[\"{line}\"]={version}, latest={data['latest']['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
