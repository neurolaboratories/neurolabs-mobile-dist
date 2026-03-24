#!/usr/bin/env python3
"""Copy integration guide sources into mobile-dist and generate latest/versioned PDFs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path


GUIDES = {
    "cordova": {
        "repo_dir": "neurolabs-cordova-sdk",
        "markdown": "Neurolabs-Cordova-Integration-Guide.md",
        "pdf_rules": "Neurolabs-Cordova-Integration-Guide-PDF-Rules.md",
        "pdf": "Neurolabs-Cordova-Integration-Guide.pdf",
        "title": "Neurolabs Cordova SDK Integration Guide",
        "document_id": "NLB-CORDOVA-INTEGRATION-GUIDE",
    },
    "android": {
        "repo_dir": "neurolabs-android-sdk",
        "markdown": "Neurolabs-Android-Integration-Guide.md",
        "pdf_rules": "Neurolabs-Android-Integration-Guide-PDF-Rules.md",
        "pdf": "Neurolabs-Android-Integration-Guide.pdf",
        "title": "Neurolabs Android SDK Integration Guide",
        "document_id": "NLB-ANDROID-INTEGRATION-GUIDE",
    },
    "ios": {
        "repo_dir": "neurolabs-ios-sdk",
        "markdown": "Neurolabs-IOS-Integration-Guide.md",
        "pdf_rules": "Neurolabs-IOS-Integration-Guide-PDF-Rules.md",
        "pdf": "Neurolabs-IOS-Integration-Guide.pdf",
        "title": "Neurolabs iOS SDK Integration Guide",
        "document_id": "NLB-IOS-INTEGRATION-GUIDE",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-root", default=".")
    parser.add_argument("--workspace-root", default="..")
    parser.add_argument("--version", required=True)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--fail-if-pdf-stale", action="store_true")
    args = parser.parse_args()

    dist_root = Path(args.dist_root).resolve()
    workspace_root = Path(args.workspace_root).resolve()
    latest_root = dist_root / "docs" / "integration-guides" / "latest"
    release_root = dist_root / "docs" / "integration-guides" / "releases" / args.version
    generator = dist_root / "scripts" / "generate_markdown_pdf.py"

    manifest: dict[str, object] = {
        "version": args.version,
        "generated_on": args.date,
        "latest_root": "docs/integration-guides/latest",
        "release_root": f"docs/integration-guides/releases/{args.version}",
        "guides": {},
    }

    for platform, config in GUIDES.items():
        source_root = workspace_root / config["repo_dir"]
        source_markdown = source_root / config["markdown"]
        source_rules = source_root / config["pdf_rules"]
        source_pdf = source_root / config["pdf"]

        if args.fail_if_pdf_stale and source_pdf.exists() and source_pdf.stat().st_mtime < source_markdown.stat().st_mtime:
            raise SystemExit(
                f"Source PDF is older than markdown for {platform}: {source_pdf.name}. Regenerate before publishing."
            )

        latest_platform_root = latest_root / platform
        release_platform_root = release_root / platform

        latest_markdown = latest_platform_root / config["markdown"]
        latest_rules = latest_platform_root / config["pdf_rules"]
        latest_pdf = latest_platform_root / config["pdf"]

        release_markdown = release_platform_root / config["markdown"]
        release_rules = release_platform_root / config["pdf_rules"]
        release_pdf = release_platform_root / config["pdf"]

        copy_file(source_markdown, latest_markdown)
        copy_file(source_rules, latest_rules)
        copy_file(source_markdown, release_markdown)
        copy_file(source_rules, release_rules)

        for output_pdf, markdown, rules in (
            (latest_pdf, latest_markdown, latest_rules),
            (release_pdf, release_markdown, release_rules),
        ):
            subprocess.run(
                [
                    "python3",
                    str(generator),
                    "--source",
                    str(markdown),
                    "--output",
                    str(output_pdf),
                    "--rules",
                    str(rules),
                    "--title",
                    config["title"],
                    "--document-id",
                    config["document_id"],
                    "--version",
                    args.version,
                    "--date",
                    args.date,
                ],
                check=True,
            )

        manifest["guides"][platform] = {
            "title": config["title"],
            "source_repo": config["repo_dir"],
            "latest": {
                "markdown": str(latest_markdown.relative_to(dist_root)),
                "pdf_rules": str(latest_rules.relative_to(dist_root)),
                "pdf": str(latest_pdf.relative_to(dist_root)),
                "checksum_sha256": sha256(latest_pdf),
            },
            "release": {
                "markdown": str(release_markdown.relative_to(dist_root)),
                "pdf_rules": str(release_rules.relative_to(dist_root)),
                "pdf": str(release_pdf.relative_to(dist_root)),
                "checksum_sha256": sha256(release_pdf),
            },
        }

    manifest_path = dist_root / "manifests" / "guides.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
