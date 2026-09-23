#!/usr/bin/env python3
"""Stamp EVERY .binaryTarget in Package.swift, from one release, in one call.

All-or-nothing by construction. The previous version stamped whatever triples
the caller happened to pass, and the workflow decided what to pass with a
cascade of `if [[ -n "$ri_asset" ]]` tests keyed on which assets the dispatch
carried. A 1.6.x backport dispatch has no `recognition` key, so the cascade
stamped NeurolabsSDK + ProductAuditKit and silently left the five recognition
targets on their 1.7.x URLs — a Package.swift serving two release lines at
once, which is how `main` came to hand SPM consumers a 1.6.12 SDK bolted to a
1.7.7 recognition stack.

There is no longer a way to express "stamp some of them":

  * the set of targets supplied must EXACTLY equal the set of .binaryTarget
    blocks in the manifest — a missing target is a hard failure naming it, an
    unknown target is a hard failure too;
  * every URL must carry the same /releases/download/<tag>/ segment;
  * the legacy two-positional-arg form is gone. It stamped NeurolabsSDK only
    and left the other six targets wherever they were, which made the
    documented recovery tool (manual-promote.yml) a manifest-splitter.

Two ways to supply the assets:

    # explicit, for the release train (URLs already known)
    update_spm_manifest.py Package.swift --release-tag v1.7.7 \
        --target NeurolabsSDK --url <url> --checksum <sha> \
        --target ProductAuditKit --url <url> --checksum <sha> ...

    # derived, for recovery: read the published release and hash what is there
    update_spm_manifest.py Package.swift --release-tag v1.7.7 \
        --from-release neurolaboratories/neurolabs-mobile-dist

Run scripts/verify_spm_manifest.py afterwards — stamping and asserting are
deliberately separate so the assertion also covers hand edits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BINARY_TARGET = re.compile(
    r'\.binaryTarget\(\s*name:\s*"(?P<name>[^"]+)",\s*'
    r'url:\s*"(?P<url>[^"]*)",\s*checksum:\s*"(?P<checksum>[^"]*)"',
    re.DOTALL,
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class StampError(Exception):
    """A refused stamp. `code` is the exit status the CLI returns for it: 1 for
    a malformed manifest, 2 for a violated all-or-nothing rule."""

    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def discover_targets(text: str) -> list[str]:
    names = [m.group("name") for m in BINARY_TARGET.finditer(text)]
    if not names:
        raise StampError("no .binaryTarget blocks found in the manifest", 1)
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise StampError(f"duplicate binaryTarget names: {sorted(dupes)}", 1)
    return names


def stamp_target(text: str, name: str, url: str, checksum: str) -> str:
    pattern = re.compile(
        r'(\.binaryTarget\(\s*name:\s*"' + re.escape(name) + r'",\s*'
        r'url:\s*")[^"]*(",\s*checksum:\s*")[^"]*(")',
        re.DOTALL,
    )
    new_text, n = pattern.subn(rf"\g<1>{url}\g<2>{checksum}\g<3>", text)
    if n != 1:
        raise StampError(f"expected exactly one binaryTarget {name!r}, matched {n}", 1)
    return new_text


def stamp_text(text: str, tag: str, supplied: dict[str, tuple[str, str]]) -> tuple[str, str]:
    """Stamp every declared binaryTarget, or none. Pure; raises StampError.

    Importable so `stamp_manifests_from_state.py` stamps Package.swift through
    the same all-or-nothing gate the release train uses, rather than growing a
    second, laxer path into the file that decides what SPM consumers link.
    """
    names = discover_targets(text)

    # ---- all-or-nothing gate -------------------------------------------------
    missing = sorted(set(names) - set(supplied))
    unknown = sorted(set(supplied) - set(names))
    if missing:
        raise StampError(
            "the dispatch carried no asset for "
            f"{', '.join(missing)}. Package.swift declares {len(names)} "
            "binaryTargets and every release must stamp all of them — a "
            "partial stamp is what splits the manifest across two release "
            "lines. Refusing to write.",
            2,
        )
    if unknown:
        raise StampError(f"not a binaryTarget in this manifest: {', '.join(unknown)}", 2)

    problems = []
    seen_urls: dict[str, str] = {}
    for name in names:
        url, checksum = supplied[name]
        if not url:
            problems.append(f"{name}: empty url")
        elif f"/releases/download/{tag}/" not in url:
            problems.append(f"{name}: url is not from {tag} ({url})")
        if not SHA256.match(checksum):
            problems.append(f"{name}: checksum is not a sha256 hex digest ({checksum!r})")
        if url in seen_urls:
            # SPM keys the binary artifact cache by URL; two targets sharing a
            # zip resolve to one artifact and the other framework goes missing.
            problems.append(f"{name}: shares its url with {seen_urls[url]}")
        seen_urls[url] = name
    if problems:
        raise StampError(
            "refusing to stamp:\n" + "\n".join(f"  - {p}" for p in problems), 2
        )

    updated = text
    for name in names:
        url, checksum = supplied[name]
        updated = stamp_target(updated, name, url, checksum)

    # An identical re-stamp is a legitimate replay, NOT an error. The old
    # script exited 1 on "No changes applied", which failed re-dispatches.
    if updated != text:
        summary = f"stamped {len(names)} binaryTargets at {tag}: {', '.join(names)}"
    else:
        summary = f"already stamped at {tag}: {', '.join(names)} (no change)"
    return updated, summary


def _gh(args: list[str]) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"error: gh {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout


def resolve_from_release(repo: str, tag: str, names: list[str]) -> dict[str, tuple[str, str]]:
    """Download every target's asset from the published release and hash it.

    This is what makes recovery trustworthy: the checksums come from the bytes
    actually being served, not from a workflow input somebody retyped.
    """
    assets = json.loads(_gh(["release", "view", tag, "--repo", repo, "--json", "assets"]))
    available = [a["name"] for a in assets.get("assets", [])]
    resolved: dict[str, tuple[str, str]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name in names:
            exact = f"{name}.xcframework-{tag}.zip"
            candidates = [a for a in available if a == exact] or [
                a for a in available if a.startswith(f"{name}.")
            ]
            if len(candidates) != 1:
                raise SystemExit(
                    f"error: release {tag} of {repo} has "
                    f"{len(candidates)} assets for binaryTarget {name!r} "
                    f"(candidates={candidates}); cannot stamp all-or-nothing."
                )
            asset = candidates[0]
            _gh(["release", "download", tag, "--repo", repo, "--pattern", asset,
                 "--dir", tmp, "--clobber"])
            digest = hashlib.sha256(Path(tmp, asset).read_bytes()).hexdigest()
            resolved[name] = (
                f"https://github.com/{repo}/releases/download/{tag}/{asset}",
                digest,
            )
    return resolved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--release-tag", required=True)
    ap.add_argument("--target", action="append", default=[])
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--checksum", action="append", default=[])
    ap.add_argument("--from-release", default="",
                    help="OWNER/REPO: derive every URL + checksum from that published release")
    args = ap.parse_args()

    if not args.manifest.exists():
        print(f"error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    tag = args.release_tag.strip()
    text = args.manifest.read_text()
    try:
        names = discover_targets(text)
    except StampError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code

    if args.from_release:
        if args.target:
            print("error: --from-release and --target are mutually exclusive", file=sys.stderr)
            return 1
        supplied = resolve_from_release(args.from_release, tag, names)
    else:
        if not (len(args.target) == len(args.url) == len(args.checksum)):
            print("error: --target/--url/--checksum must come in matched sets", file=sys.stderr)
            return 1
        supplied = {
            t: (u.strip(), c.strip())
            for t, u, c in zip(args.target, args.url, args.checksum)
        }

    try:
        updated, summary = stamp_text(text, tag, supplied)
    except StampError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code

    if updated != text:
        args.manifest.write_text(updated)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
