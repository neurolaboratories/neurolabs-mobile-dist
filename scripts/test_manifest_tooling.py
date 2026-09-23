#!/usr/bin/env python3
"""Regression tests for the dist manifest tooling. Stdlib only:

    python3 -m unittest discover -s scripts -p 'test_*.py' -v

Every case here is a downgrade or a split that actually reached `main`, or the
guard that would have stopped it. They are cheap to run and they are the only
thing standing between a backport dispatch and another silent downgrade.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import semver  # noqa: E402

BASE = "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download"
SHA_A = "a" * 64
SHA_B = "b" * 64


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


class SemverTests(unittest.TestCase):
    def test_orders_patch_numerically_not_lexically(self):
        # "v1.6.9" > "v1.6.12" as strings; that is the whole problem.
        self.assertEqual(semver.compare("v1.6.9", "v1.6.12"), -1)
        self.assertEqual(semver.compare("v1.1.3", "v1.1.13"), -1)

    def test_the_september_pair(self):
        self.assertEqual(semver.compare("v1.6.12", "v1.7.7"), -1)

    def test_prerelease_sorts_below_its_release(self):
        self.assertEqual(semver.compare("v1.7.7-rc1", "v1.7.7"), -1)

    def test_line_of(self):
        self.assertEqual(semver.line_of("v1.6.12"), "1.6")
        self.assertEqual(semver.line_of("v1.7.7"), "1.7")

    def test_rejects_junk(self):
        with self.assertRaises(semver.InvalidVersion):
            semver.parse("latest")


class PlatformManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name, "ios.json")
        self.path.write_text(json.dumps({
            "platform": "ios",
            "latest": {
                "version": "v1.7.7",
                "asset_name": "NeurolabsSDK.xcframework-v1.7.7.zip",
                "asset_url": f"{BASE}/v1.7.7/NeurolabsSDK.xcframework-v1.7.7.zip",
                "checksum_sha256": SHA_A,
            },
        }, indent=2) + "\n")
        self.addCleanup(self.tmp.cleanup)

    def stamp(self, version: str) -> subprocess.CompletedProcess:
        asset = f"NeurolabsSDK.xcframework-{version}.zip"
        return run("update_platform_manifest.py", str(self.path),
                   "--version", version,
                   "--asset-name", asset,
                   "--asset-url", f"{BASE}/{version}/{asset}",
                   "--checksum", SHA_B)

    def data(self) -> dict:
        return json.loads(self.path.read_text())

    def test_backport_does_not_move_latest(self):
        """The exact 2026-09-21 dispatch that downgraded main."""
        self.assertEqual(self.stamp("v1.6.12").returncode, 0)
        d = self.data()
        self.assertEqual(d["latest"]["version"], "v1.7.7")
        self.assertEqual(d["lines"]["1.6"]["version"], "v1.6.12")
        self.assertEqual(d["lines"]["1.7"]["version"], "v1.7.7")

    def test_newer_release_promotes_latest(self):
        self.assertEqual(self.stamp("v1.7.8").returncode, 0)
        self.assertEqual(self.data()["latest"]["version"], "v1.7.8")

    def test_replay_is_idempotent(self):
        self.assertEqual(self.stamp("v1.7.7").returncode, 0)
        self.assertEqual(self.data()["latest"]["version"], "v1.7.7")

    def test_within_line_regression_is_refused(self):
        self.assertEqual(self.stamp("v1.6.12").returncode, 0)
        proc = self.stamp("v1.6.11")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("backwards", proc.stderr)
        self.assertEqual(self.data()["lines"]["1.6"]["version"], "v1.6.12")

    def test_asset_url_must_carry_its_own_tag(self):
        proc = run("update_platform_manifest.py", str(self.path),
                   "--version", "v1.7.9",
                   "--asset-name", "x.zip",
                   "--asset-url", f"{BASE}/v1.7.8/x.zip",
                   "--checksum", SHA_B)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.data()["latest"]["version"], "v1.7.7")


class SpmStampTests(unittest.TestCase):
    MANIFEST = '''// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "T",
    targets: [
        .binaryTarget(
            name: "NeurolabsSDK",
            url: "%(base)s/v1.7.7/NeurolabsSDK.xcframework-v1.7.7.zip",
            checksum: "%(a)s"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "%(base)s/v1.7.7/RecognitionEngine.xcframework-v1.7.7.zip",
            checksum: "%(b)s"
        )
    ]
)
''' % {"base": BASE, "a": SHA_A, "b": SHA_B}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name, "Package.swift")
        self.path.write_text(self.MANIFEST)
        self.addCleanup(self.tmp.cleanup)

    def test_partial_stamp_is_refused_and_writes_nothing(self):
        """The 1.6.x dispatch shape: assets for some targets, not all."""
        proc = run("update_spm_manifest.py", str(self.path),
                   "--release-tag", "v1.6.12",
                   "--target", "NeurolabsSDK",
                   "--url", f"{BASE}/v1.6.12/NeurolabsSDK.xcframework-v1.6.12.zip",
                   "--checksum", SHA_A)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("RecognitionEngine", proc.stderr)
        self.assertEqual(self.path.read_text(), self.MANIFEST)

    def test_mixed_tags_are_refused_even_when_complete(self):
        proc = run("update_spm_manifest.py", str(self.path),
                   "--release-tag", "v1.6.12",
                   "--target", "NeurolabsSDK",
                   "--url", f"{BASE}/v1.6.12/NeurolabsSDK.xcframework-v1.6.12.zip",
                   "--checksum", SHA_A,
                   "--target", "RecognitionEngine",
                   "--url", f"{BASE}/v1.7.7/RecognitionEngine.xcframework-v1.7.7.zip",
                   "--checksum", SHA_B)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.path.read_text(), self.MANIFEST)

    def test_shared_url_is_refused(self):
        url = f"{BASE}/v1.6.12/bundle.zip"
        proc = run("update_spm_manifest.py", str(self.path),
                   "--release-tag", "v1.6.12",
                   "--target", "NeurolabsSDK", "--url", url, "--checksum", SHA_A,
                   "--target", "RecognitionEngine", "--url", url, "--checksum", SHA_A)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("shares its url", proc.stderr)

    def test_complete_stamp_succeeds(self):
        proc = run("update_spm_manifest.py", str(self.path),
                   "--release-tag", "v1.6.12",
                   "--target", "NeurolabsSDK",
                   "--url", f"{BASE}/v1.6.12/NeurolabsSDK.xcframework-v1.6.12.zip",
                   "--checksum", SHA_A,
                   "--target", "RecognitionEngine",
                   "--url", f"{BASE}/v1.6.12/RecognitionEngine.xcframework-v1.6.12.zip",
                   "--checksum", SHA_B)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("v1.7.7", self.path.read_text())


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name, "Package.swift")
        self.addCleanup(self.tmp.cleanup)

    def write(self, sdk_tag: str, engine_tag: str):
        self.path.write_text(SpmStampTests.MANIFEST
                             .replace("v1.7.7/NeurolabsSDK", f"{sdk_tag}/NeurolabsSDK")
                             .replace("NeurolabsSDK.xcframework-v1.7.7",
                                      f"NeurolabsSDK.xcframework-{sdk_tag}")
                             .replace("v1.7.7/RecognitionEngine", f"{engine_tag}/RecognitionEngine")
                             .replace("RecognitionEngine.xcframework-v1.7.7",
                                      f"RecognitionEngine.xcframework-{engine_tag}"))

    def test_split_manifest_fails(self):
        """Exactly the file that shipped on main on 2026-09-21."""
        self.write("v1.6.12", "v1.7.7")
        proc = run("verify_spm_manifest.py", str(self.path), "--skip-dump-package")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("split across 2 release tags", proc.stderr)

    def test_single_line_manifest_passes(self):
        self.write("v1.7.7", "v1.7.7")
        proc = run("verify_spm_manifest.py", str(self.path), "--skip-dump-package")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_expect_tag_mismatch_fails(self):
        self.write("v1.7.7", "v1.7.7")
        proc = run("verify_spm_manifest.py", str(self.path),
                   "--expect-tag", "v1.7.8", "--skip-dump-package")
        self.assertEqual(proc.returncode, 2)


class CheckedInStateTests(unittest.TestCase):
    """The repo as committed must satisfy its own rules."""

    def test_manifests_and_package_swift_agree(self):
        proc = run("verify_spm_manifest.py", str(ROOT / "Package.swift"),
                   "--cross-check-manifests", "--skip-dump-package")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
