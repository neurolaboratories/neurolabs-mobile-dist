#!/usr/bin/env python3
"""Post-stamp assertion: Package.swift serves exactly ONE release line.

Runs after every stamp and on demand. It is deliberately not part of the
stamper, so it also catches hand edits and bad merges — the v1.6.12 split
reached `main` through a workflow, but nothing would have stopped a human
producing the same file.

Three checks, all fatal:

  1. every .binaryTarget url carries a /releases/download/<tag>/ segment, and
     every target agrees on the same <tag>. This is the assertion that cannot
     be reasoned around: a manifest pinning NeurolabsSDK at v1.6.12 and
     RecognitionEngine at v1.7.7 fails here, loudly, naming both;
  2. no two binaryTargets share a url (SPM keys the binary artifact cache by
     URL, so a shared zip silently drops one framework) and every checksum is
     a sha256 hex digest;
  3. `swift package dump-package` still parses the manifest, and every
     product's targets resolve to declared targets — the link-closure lists in
     `products:` are hand-maintained and a typo there is a launch-time
     @rpath crash in a partner app, not a build error here.

With --cross-check-manifests it also holds manifests/*.json to the same story:
`latest` never below any line head, `latest` mirroring its own line, asset URLs
carrying their own tag, and manifests/ios.json agreeing with Package.swift.
That last one is the other half of the September defect — ios.json advertised
v1.6.12 while five binaryTargets pointed at v1.7.7.

Check 3 needs a Swift toolchain. It uses `swift` from PATH when present,
otherwise the official `swift` docker image (GitHub's ubuntu runners ship
Docker but no Swift). Missing both is a FAILURE, not a skip — pass
--skip-dump-package only where a human has already run it.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import semver  # noqa: E402

BINARY_TARGET = re.compile(
    r'\.binaryTarget\(\s*name:\s*"(?P<name>[^"]+)",\s*'
    r'url:\s*"(?P<url>[^"]*)",\s*checksum:\s*"(?P<checksum>[^"]*)"',
    re.DOTALL,
)
RELEASE_SEGMENT = re.compile(r"/releases/download/(?P<tag>[^/]+)/(?P<asset>[^/?#]+)$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SWIFT_IMAGE = "swift:6.0-jammy"


def dump_package(root: Path) -> dict:
    if shutil.which("swift"):
        cmd = ["swift", "package", "dump-package"]
    elif shutil.which("docker"):
        cmd = ["docker", "run", "--rm", "-v", f"{root}:/pkg", "-w", "/pkg",
               SWIFT_IMAGE, "swift", "package", "dump-package"]
    else:
        raise SystemExit(
            "error: `swift package dump-package` needs a Swift toolchain or "
            "Docker and neither is available. This repo has no CI test suite, "
            "so the dump IS the parse gate — do not skip it silently."
        )
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(
            "error: `swift package dump-package` failed — Package.swift does "
            f"not parse:\n{proc.stderr.strip()}"
        )
    return json.loads(proc.stdout)


def cross_check_manifests(root: Path, spm_tag: str) -> list[str]:
    problems: list[str] = []
    for platform in ("ios", "android", "cordova"):
        path = root / "manifests" / f"{platform}.json"
        if not path.exists():
            problems.append(f"{path}: missing")
            continue
        data = json.loads(path.read_text())
        latest = data.get("latest") or {}
        version = latest.get("version")
        if not version:
            problems.append(f"{platform}.json: latest.version is missing")
            continue
        try:
            semver.parse(version)
        except semver.InvalidVersion as exc:
            problems.append(f"{platform}.json: {exc}")
            continue

        asset_url = latest.get("asset_url", "")
        if f"/releases/download/{version}/" not in asset_url:
            problems.append(
                f"{platform}.json: latest.asset_url is not from {version} ({asset_url})"
            )

        lines = data.get("lines") or {}
        for line, entry in lines.items():
            entry_version = entry.get("version", "")
            try:
                if semver.compare(version, entry_version) < 0:
                    problems.append(
                        f"{platform}.json: latest ({version}) is BELOW "
                        f"lines[\"{line}\"] ({entry_version}) — `latest` was "
                        "overwritten by an older release"
                    )
                if semver.line_of(entry_version) != line:
                    problems.append(
                        f"{platform}.json: lines[\"{line}\"] holds {entry_version}"
                    )
            except semver.InvalidVersion as exc:
                problems.append(f"{platform}.json: lines[\"{line}\"]: {exc}")
        own_line = semver.line_of(version)
        if lines and lines.get(own_line, {}).get("version") != version:
            problems.append(
                f"{platform}.json: latest ({version}) is not mirrored by "
                f"lines[\"{own_line}\"]"
            )

        if platform == "ios" and version != spm_tag:
            problems.append(
                f"ios.json advertises {version} but Package.swift pins every "
                f"binaryTarget at {spm_tag} — the SPM package and the manifest "
                "describe different releases"
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path, nargs="?", default=Path("Package.swift"))
    ap.add_argument("--expect-tag", default="",
                    help="additionally require that the one shared tag is this one")
    ap.add_argument("--skip-dump-package", action="store_true")
    ap.add_argument("--cross-check-manifests", action="store_true",
                    help="also hold manifests/*.json to the same single-line story")
    args = ap.parse_args()

    manifest = args.manifest.resolve()
    if not manifest.exists():
        print(f"error: manifest not found: {manifest}", file=sys.stderr)
        return 1
    text = manifest.read_text()

    targets = list(BINARY_TARGET.finditer(text))
    if not targets:
        print("error: no .binaryTarget blocks found", file=sys.stderr)
        return 2

    problems: list[str] = []
    tags: dict[str, list[str]] = {}
    seen_urls: dict[str, str] = {}
    for m in targets:
        name, url, checksum = m.group("name"), m.group("url"), m.group("checksum")
        seg = RELEASE_SEGMENT.search(url)
        if not seg:
            problems.append(f"{name}: url has no /releases/download/<tag>/<asset> segment ({url})")
        else:
            tags.setdefault(seg.group("tag"), []).append(name)
        if not SHA256.match(checksum):
            problems.append(f"{name}: checksum is not a sha256 hex digest ({checksum!r})")
        if url in seen_urls:
            problems.append(f"{name}: shares its url with {seen_urls[url]} "
                            "(SPM caches binary artifacts by url — one of them will be missing)")
        seen_urls[url] = name

    if len(tags) > 1:
        detail = "; ".join(f"{tag}: {', '.join(sorted(n))}" for tag, n in sorted(tags.items()))
        problems.append(
            f"binaryTargets are split across {len(tags)} release tags ({detail}). "
            "A consumer resolving this package links frameworks built from two "
            "different source trees."
        )
    elif tags and args.expect_tag and args.expect_tag not in tags:
        problems.append(
            f"expected every binaryTarget at {args.expect_tag}, found {next(iter(tags))}"
        )

    if problems:
        print("error: Package.swift does not serve one release line:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2

    tag = next(iter(tags))
    print(f"ok: {len(targets)} binaryTargets, all at {tag}")

    if args.cross_check_manifests:
        manifest_problems = cross_check_manifests(manifest.parent, tag)
        if manifest_problems:
            print("error: platform manifests disagree:", file=sys.stderr)
            for p in manifest_problems:
                print(f"  - {p}", file=sys.stderr)
            return 2
        print("ok: ios/android/cordova manifests agree, `latest` at or above every line")

    if args.skip_dump_package:
        print("warning: skipped `swift package dump-package` on request", file=sys.stderr)
        return 0

    dump = dump_package(manifest.parent)
    declared = {t["name"] for t in dump.get("targets", [])}
    dangling = []
    for product in dump.get("products", []):
        for target in product.get("targets", []):
            if target not in declared:
                dangling.append(f"product {product['name']} -> undeclared target {target}")
    if dangling:
        print("error: products reference targets that do not exist:", file=sys.stderr)
        for d in dangling:
            print(f"  - {d}", file=sys.stderr)
        return 2
    print(
        f"ok: dump-package parses; {len(dump.get('products', []))} products, "
        f"{len(declared)} targets, every product target declared"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
