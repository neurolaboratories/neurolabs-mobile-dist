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


class StampFromStateTests(unittest.TestCase):
    """The readiness gate, and what had to change to make gating survivable.

    Stamping each platform on its own dispatch published an `asset_url` on a
    still-draft release — a 404 for every partner who is not a collaborator —
    and simply adding an `if:` to those steps would have left two of the three
    manifests stamped by nobody, because a dispatch only ever touched its own
    file. These cover the replacement: one stamp, from release-state, for every
    platform at once.
    """

    ASSETS = {
        "ios": "NeurolabsSDK.xcframework-{v}.zip",
        "android": "neurolabs-android-sdk-{v}.aar",
        "cordova": "neurolabs-cordova-sdk-{v}.tgz",
    }
    MAVEN = {
        "repository_url": "https://maven.pkg.github.com/neurolaboratories/neurolabs-mobile-dist",
        "group_id": "ai.neurolabs",
        "artifact_id": "neurolabs-android-sdk",
        "version": "1.7.8",
        "packaging": "aar",
    }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifests = self.root / "manifests"
        self.state_dir = self.manifests / "release-state"
        self.state_dir.mkdir(parents=True)
        for platform, asset in self.ASSETS.items():
            name = asset.format(v="v1.7.7")
            (self.manifests / f"{platform}.json").write_text(json.dumps({
                "platform": platform,
                "latest": {
                    "version": "v1.7.7",
                    "asset_name": name,
                    "asset_url": f"{BASE}/v1.7.7/{name}",
                    "checksum_sha256": SHA_A,
                },
            }, indent=2) + "\n")
        self.package = self.root / "Package.swift"
        self.package.write_text(SpmStampTests.MANIFEST)
        self.before = self.snapshot()

    def snapshot(self) -> dict:
        return {p.name: p.read_text()
                for p in list(self.manifests.glob("*.json")) + [self.package]}

    def url(self, platform: str, version: str) -> str:
        return f"{BASE}/{version}/{self.ASSETS[platform].format(v=version)}"

    def write_state(self, version, platforms=("ios", "android", "cordova"),
                    *, maven=None, spm_targets=None, overrides=None):
        artifacts = {
            platform: {
                "asset_url": self.url(platform, version),
                "checksum_sha256": SHA_B,
            }
            for platform in platforms
        }
        if maven:
            artifacts["android"]["maven"] = maven
        if spm_targets:
            artifacts["ios"]["spm_targets"] = spm_targets
        for platform, patch in (overrides or {}).items():
            artifacts[platform].update(patch)
        path = self.state_dir / f"{version}.json"
        path.write_text(json.dumps({"version": version, "artifacts": artifacts},
                                   indent=2) + "\n")
        return path

    def stamp(self, version, *extra) -> subprocess.CompletedProcess:
        return run("stamp_manifests_from_state.py",
                   str(self.state_dir / f"{version}.json"),
                   "--manifests-dir", str(self.manifests),
                   "--package-swift", str(self.package), *extra)

    def manifest(self, platform: str) -> dict:
        return json.loads((self.manifests / f"{platform}.json").read_text())

    def assertNothingWritten(self, proc):
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(self.snapshot(), self.before)

    def test_all_three_manifests_are_stamped_from_one_state_file(self):
        """The whole point: the run where `ready` flips stamps every platform,
        not just the one that happened to dispatch last."""
        self.write_state("v1.7.8")
        proc = self.stamp("v1.7.8")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for platform, asset in self.ASSETS.items():
            latest = self.manifest(platform)["latest"]
            self.assertEqual(latest["version"], "v1.7.8")
            self.assertEqual(latest["asset_name"], asset.format(v="v1.7.8"))
            self.assertEqual(latest["asset_url"], self.url(platform, "v1.7.8"))
            self.assertEqual(latest["checksum_sha256"], SHA_B)

    def test_android_maven_block_survives_the_round_trip(self):
        self.write_state("v1.7.8", maven=self.MAVEN)
        self.assertEqual(self.stamp("v1.7.8").returncode, 0)
        latest = self.manifest("android")["latest"]
        self.assertEqual(latest["maven"], self.MAVEN)
        self.assertEqual(
            latest["gradle_maven_dependency_example"],
            'implementation("ai.neurolabs:neurolabs-android-sdk:1.7.8")',
        )
        self.assertIn("v1.7.8", latest["gradle_example"])
        self.assertIn("v1.7.8", self.manifest("cordova")["latest"]["install_example"])

    def test_state_without_an_ios_target_map_does_not_crash_the_train(self):
        """Every state file written before the map existed looks like this."""
        self.write_state("v1.7.8")
        proc = self.stamp("v1.7.8")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no iOS spm_targets map", proc.stdout)
        self.assertEqual(self.package.read_text(), SpmStampTests.MANIFEST)
        self.assertEqual(self.manifest("ios")["latest"]["version"], "v1.7.8")

    def test_ios_target_map_stamps_package_swift(self):
        self.write_state("v1.7.8", spm_targets={
            "NeurolabsSDK": {
                "url": f"{BASE}/v1.7.8/NeurolabsSDK.xcframework-v1.7.8.zip",
                "checksum_sha256": SHA_A,
            },
            "RecognitionEngine": {
                "url": f"{BASE}/v1.7.8/RecognitionEngine.xcframework-v1.7.8.zip",
                "checksum_sha256": SHA_B,
            },
        })
        proc = self.stamp("v1.7.8")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("v1.7.7", self.package.read_text())

    def test_partial_ios_target_map_is_still_all_or_nothing(self):
        """The split-manifest gate applies to this path too."""
        self.write_state("v1.7.8", spm_targets={
            "NeurolabsSDK": {
                "url": f"{BASE}/v1.7.8/NeurolabsSDK.xcframework-v1.7.8.zip",
                "checksum_sha256": SHA_A,
            },
        })
        proc = self.stamp("v1.7.8")
        self.assertIn("RecognitionEngine", proc.stderr)
        self.assertNothingWritten(proc)

    def test_a_partial_release_is_refused_outright(self):
        """The defect: a cordova-only dispatch stamping cordova.json with an
        asset_url on a draft release, which 404s for every partner."""
        self.write_state("v1.7.8", platforms=("cordova",))
        proc = self.stamp("v1.7.8")
        self.assertIn("Missing platforms: android, ios", proc.stderr)
        self.assertIn("not publishable yet", proc.stderr)
        self.assertNothingWritten(proc)

    def test_backport_stamps_its_line_and_leaves_latest_alone(self):
        """The monotonic rule is unchanged by going through release-state."""
        self.write_state("v1.6.12")
        proc = self.stamp("v1.6.12")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for platform in self.ASSETS:
            data = self.manifest(platform)
            self.assertEqual(data["latest"]["version"], "v1.7.7")
            self.assertEqual(data["lines"]["1.6"]["version"], "v1.6.12")
            self.assertEqual(data["lines"]["1.7"]["version"], "v1.7.7")

    def test_within_line_regression_is_still_refused_and_writes_nothing(self):
        self.write_state("v1.7.6")
        proc = self.stamp("v1.7.6")
        self.assertIn("backwards", proc.stderr)
        self.assertNothingWritten(proc)

    def test_empty_asset_url_is_refused(self):
        self.write_state("v1.7.8", overrides={"android": {"asset_url": ""}})
        proc = self.stamp("v1.7.8")
        self.assertIn("empty asset_url", proc.stderr)
        self.assertNothingWritten(proc)

    def test_asset_url_with_no_file_name_is_refused(self):
        """Passes the readiness gate — it carries the tag segment — and would
        otherwise stamp `asset_name: ""` into a partner install instruction."""
        self.write_state("v1.7.8", overrides={
            "cordova": {"asset_url": f"{BASE}/v1.7.8/"},
        })
        proc = self.stamp("v1.7.8")
        self.assertIn("cannot derive an asset name", proc.stderr)
        self.assertNothingWritten(proc)

    def test_asset_url_from_another_release_is_refused(self):
        self.write_state("v1.7.8", overrides={
            "ios": {"asset_url": self.url("ios", "v1.7.7")},
        })
        proc = self.stamp("v1.7.8")
        self.assertIn("does not reference v1.7.8", proc.stderr)
        self.assertNothingWritten(proc)

    def test_skip_package_swift_leaves_it_to_the_recovery_tool(self):
        self.write_state("v1.7.8", spm_targets={
            "NeurolabsSDK": {
                "url": f"{BASE}/v1.7.8/NeurolabsSDK.xcframework-v1.7.8.zip",
                "checksum_sha256": SHA_A,
            },
        })
        proc = self.stamp("v1.7.8", "--skip-package-swift")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.package.read_text(), SpmStampTests.MANIFEST)
        self.assertEqual(self.manifest("ios")["latest"]["version"], "v1.7.8")


class CheckedInStateTests(unittest.TestCase):
    """The repo as committed must satisfy its own rules."""

    def test_manifests_and_package_swift_agree(self):
        proc = run("verify_spm_manifest.py", str(ROOT / "Package.swift"),
                   "--cross-check-manifests", "--skip-dump-package")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
