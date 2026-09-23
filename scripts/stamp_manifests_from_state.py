#!/usr/bin/env python3
"""Stamp EVERY platform manifest for a release, from its release-state file.

The release train is three independent dispatches. Each one used to stamp its
own `manifests/<platform>.json` the moment it arrived, which meant the manifest
— the partner-facing install instruction — advertised an `asset_url` on a
release that was still a DRAFT until the last platform landed. Draft download
URLs 404 for anyone who is not a repo collaborator, so a partial release
replaced a working install command with a broken one. That is strictly worse
than leaving the previous version in place: `manifests/release-state/v1.6.12.json`
records a single platform, and v1.6.12 nevertheless reached `manifests/ios.json`.

The obvious fix — gate each dispatch's own stamp on
`validate_release_ready.py` — breaks the train instead, because a run only ever
touched its own file: the first two platforms would skip their stamp and the
third would stamp only itself, leaving two manifests permanently stale. So the
stamp moves to the readiness gate and becomes plural. Everything it needs is
already in the state file, which every dispatch appends to and commits:

    {"version": "v1.7.7",
     "artifacts": {"ios": {"asset_url", "checksum_sha256", "spm_targets"?},
                   "android": {"asset_url", "checksum_sha256", "maven"?},
                   "cordova": {"asset_url", "checksum_sha256"}}}

Properties this script keeps:

  * it refuses outright unless `validate_release_ready.py` passes on the state
    file, so the rule holds for a human running it by hand and not only for the
    `if:` in the workflow;
  * every rule stays in one place — it imports `update_platform_manifest` and
    `update_spm_manifest` rather than re-implementing the monotonic, line-aware
    and all-or-nothing logic, which is the failure mode that let the old inline
    heredoc drift;
  * it validates all files before writing any, so a refused manifest cannot
    leave the other two stamped for a release that will not be published.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import update_platform_manifest  # noqa: E402
import update_spm_manifest  # noqa: E402

# The manifests this repo serves. A state file naming anything else is a bug in
# whatever wrote it, not something to stamp quietly past.
KNOWN_PLATFORMS = ("android", "cordova", "ios")


def asset_name_from_url(url: str) -> str:
    """The asset file name, derived rather than stored.

    release-state has never carried `asset_name`, and back-filling it would
    leave every existing file without one. It does not need to: the train built
    the dist URL as `<repo>/releases/download/<tag>/<asset_name>` from the same
    payload field, so the basename IS the asset name, character for character.
    An empty derivation is a hard failure — an entry whose `asset_name` is ""
    still reads as an install instruction and is not one.
    """
    path = urlsplit((url or "").strip()).path
    # A URL ending in "/" names a directory, not an asset. PurePosixPath would
    # hand back the last path segment for it — the release tag — and that is a
    # plausible-looking asset name that downloads nothing.
    if not path or path.endswith("/"):
        return ""
    return PurePosixPath(path).name


def release_is_ready(state_file: Path) -> bool:
    """Delegate to the readiness gate itself; never re-state its rules here."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_release_ready.py"), str(state_file)],
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        return True
    sys.stderr.write(proc.stderr)
    print(
        f"error: refusing to stamp any manifest for {state_file}: the release is "
        "not publishable yet, so its asset URLs point at a draft release that "
        "404s for everyone who is not a collaborator. Manifests are stamped "
        "once, when the last platform lands.",
        file=sys.stderr,
    )
    return False


def spm_targets_of(entry: dict) -> dict[str, tuple[str, str]]:
    targets = entry.get("spm_targets") or {}
    return {
        name: (((t or {}).get("url") or "").strip(),
               ((t or {}).get("checksum_sha256") or "").strip())
        for name, t in targets.items()
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("state_file", type=Path)
    ap.add_argument("--manifests-dir", type=Path, default=Path("manifests"))
    ap.add_argument("--package-swift", type=Path, default=Path("Package.swift"))
    ap.add_argument(
        "--skip-package-swift", action="store_true",
        help="leave Package.swift alone; manual-promote.yml re-derives it from "
             "the bytes published on the tag instead, which is stronger",
    )
    args = ap.parse_args()

    if not args.state_file.exists():
        print(f"error: missing state file: {args.state_file}", file=sys.stderr)
        return 1
    if not release_is_ready(args.state_file):
        return 2

    state = json.loads(args.state_file.read_text())
    version = (state.get("version") or "").strip()
    artifacts = state.get("artifacts") or {}

    problems: list[str] = []
    messages: list[str] = []
    writes: list[tuple[Path, str]] = []

    for platform in sorted(artifacts):
        manifest_path = args.manifests_dir / f"{platform}.json"
        if platform not in KNOWN_PLATFORMS or not manifest_path.exists():
            problems.append(
                f"{platform}: release-state names this platform but there is no "
                f"manifest at {manifest_path}"
            )
            continue
        entry = artifacts[platform]
        if not isinstance(entry, dict):
            problems.append(f"{platform}: artifact entry is not an object")
            continue

        asset_url = (entry.get("asset_url") or "").strip()
        asset_name = asset_name_from_url(asset_url)
        if not asset_name:
            problems.append(
                f"{platform}: cannot derive an asset name from asset_url "
                f"{asset_url!r}"
            )
            continue

        try:
            data, msgs = update_platform_manifest.stamp_data(
                json.loads(manifest_path.read_text()),
                version=version,
                asset_url=asset_url,
                asset_name=asset_name,
                checksum=(entry.get("checksum_sha256") or "").strip(),
                maven=entry.get("maven") or None,
            )
        except update_platform_manifest.StampError as exc:
            problems.append(f"{manifest_path}: {exc}")
            continue

        writes.append((manifest_path, update_platform_manifest.render(data)))
        messages += [f"{manifest_path}: {m}" for m in msgs]

    if not args.skip_package_swift:
        ios = artifacts.get("ios")
        supplied = spm_targets_of(ios) if isinstance(ios, dict) else {}
        if not supplied:
            # Every state file written before the iOS dispatch started
            # persisting its per-target map lacks one. Those releases stamped
            # Package.swift on the iOS dispatch itself, so the file is already
            # at this tag and there is nothing to redo; failing here would stop
            # a train that is in fact correct. Nothing ships on trust either
            # way: `verify_spm_manifest.py --expect-tag` runs immediately after
            # this script and fails the release if Package.swift is elsewhere.
            messages.append(
                f"note: {args.state_file} carries no iOS spm_targets map, so "
                f"{args.package_swift} is left as committed; the --expect-tag "
                "assertion behind this step is what proves it is at the right tag."
            )
        elif not args.package_swift.exists():
            problems.append(f"{args.package_swift}: not found")
        else:
            text = args.package_swift.read_text()
            try:
                updated, summary = update_spm_manifest.stamp_text(text, version, supplied)
            except update_spm_manifest.StampError as exc:
                problems.append(f"{args.package_swift}: {exc}")
            else:
                if updated != text:
                    writes.append((args.package_swift, updated))
                messages.append(f"{args.package_swift}: {summary}")

    if problems:
        print("error: refusing to stamp anything for "
              f"{version}, no file was written:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2

    for path, text in writes:
        path.write_text(text)
    for message in messages:
        print(message)
    print(f"stamped {version} into {len(writes)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
