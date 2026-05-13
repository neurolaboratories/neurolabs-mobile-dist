#!/usr/bin/env python3
"""Cross-platform threshold parity guard.

Reads guidance/quality threshold defaults from `neurolabs-android-sdk` and
`neurolabs-ios-sdk` checkouts and asserts each numeric default matches across
platforms. Any drift fails the script with a non-zero exit code so CI can
block merges that introduce silent UX divergence.

Designed to be invoked from the `Refresh Integration Guides` (or an upcoming
`Parity Guard`) workflow with both SDK repos already checked out under
`external/<repo-name>`. Usage:

    python3 scripts/check_threshold_parity.py \
        --android-root external/neurolabs-android-sdk \
        --ios-root     external/neurolabs-ios-sdk

The script intentionally parses source files with line-anchored regex rather
than running the SDKs — it must stay zero-dependency so it can live in CI
images without a JVM/Swift toolchain.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Reading:
    platform: str
    key: str
    value: float


@dataclass
class Source:
    label: str
    # Each entry: (file path, canonical key name, regex with a single numeric capture group)
    fields: list[tuple[Path, str, re.Pattern[str]]]


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing expected file for parity check: {path}")
    return path.read_text(encoding="utf-8")


def _extract(source: Source) -> list[Reading]:
    readings: list[Reading] = []
    for path, key, pattern in source.fields:
        body = _read(path)
        match = pattern.search(body)
        if not match:
            raise ValueError(
                f"Could not locate `{key}` in {path} using pattern `{pattern.pattern}`. "
                "Threshold parity check needs each platform to keep its defaults at the source-of-truth location."
            )
        try:
            value = float(match.group(1))
        except ValueError as exc:
            raise ValueError(f"Captured non-numeric value for `{key}` in {path}: {exc}") from exc
        readings.append(Reading(platform=source.label, key=key, value=value))
    return readings


def _sources(android_root: Path, ios_root: Path) -> tuple[Source, Source]:
    android_engine = android_root / "sdk/src/main/kotlin/ai/neurolabs/sdk/ui/NLCustomGuidanceEngineAndroid.kt"
    android_evaluator = android_root / "sdk/src/main/kotlin/ai/neurolabs/sdk/ui/NLCustomGuidanceEvaluator.kt"
    ios_engine = ios_root / "Sources/SDK/CaptureUI/NLCustomGuidanceEngine.swift"
    ios_camera_config = ios_root / "Sources/SDK/CaptureUI/NLCameraConfiguration.swift"

    android = Source(
        label="android",
        fields=[
            (android_engine, "noShelfGracePeriod", re.compile(r"noShelfGracePeriod\s*=\s*([0-9.]+)")),
            (android_engine, "angleOffWarningThresholdDegrees", re.compile(r"angleOffWarningThresholdDegrees\s*=\s*([0-9.]+)")),
            (android_engine, "directionalPerspectiveThreshold", re.compile(r"directionalPerspectiveThreshold\s*=\s*([0-9.]+)")),
            (android_engine, "guidanceDebounceInterval", re.compile(r"guidanceDebounceInterval\s*=\s*([0-9.]+)")),
            (android_engine, "guidanceMessageCooldown", re.compile(r"guidanceMessageCooldown\s*=\s*([0-9.]+)")),
            (android_evaluator, "blurScoreThreshold", re.compile(r"LIVE_BLUR_SCORE_THRESHOLD\s*=\s*([0-9.]+)")),
            (android_evaluator, "motionBlurRatioThreshold", re.compile(r"LIVE_MOTION_BLUR_RATIO_THRESHOLD\s*=\s*([0-9.]+)")),
        ],
    )

    ios = Source(
        label="ios",
        fields=[
            (ios_engine, "noShelfGracePeriod", re.compile(r"noShelfGracePeriod:\s*TimeInterval\s*=\s*([0-9.]+)")),
            (ios_engine, "angleOffWarningThresholdDegrees", re.compile(r"angleOffWarningThresholdDegrees:\s*Double\s*=\s*([0-9.]+)")),
            # iOS exposes the live perspective threshold as a `NLCameraConfiguration` init
            # default; mirror Android's `directionalPerspectiveThreshold` key here so the
            # diff compares on a shared name.
            (ios_camera_config, "directionalPerspectiveThreshold", re.compile(r"livePerspectiveSkewWarningThreshold:\s*Double\s*=\s*([0-9.]+)")),
            (ios_engine, "guidanceDebounceInterval", re.compile(r"guidanceDebounceInterval:\s*TimeInterval\s*=\s*([0-9.]+)")),
            (ios_engine, "guidanceMessageCooldown", re.compile(r"guidanceMessageCooldown:\s*TimeInterval\s*\{\s*([0-9.]+)\s*\}")),
            # iOS blur thresholds live inline in `evaluateGuidanceRules`. One regex each.
            (ios_engine, "blurScoreThreshold", re.compile(r"blurScore\s*<\s*([0-9.]+)\s*\|\|")),
            (ios_engine, "motionBlurRatioThreshold", re.compile(r"motionBlurRatio\s*<\s*([0-9.]+)")),
        ],
    )

    return android, ios


def _compare(android: list[Reading], ios: list[Reading]) -> list[str]:
    by_key_android = {r.key: r.value for r in android}
    by_key_ios = {r.key: r.value for r in ios}

    keys = sorted(set(by_key_android) | set(by_key_ios))
    errors: list[str] = []
    for key in keys:
        a = by_key_android.get(key)
        i = by_key_ios.get(key)
        if a is None:
            errors.append(f"[missing-android] iOS has `{key}` = {i} but Android did not yield a value.")
            continue
        if i is None:
            errors.append(f"[missing-ios] Android has `{key}` = {a} but iOS did not yield a value.")
            continue
        if abs(a - i) > 1e-6:
            errors.append(f"[drift] `{key}`: android={a}, ios={i}")
    return errors


def _format_summary(android: list[Reading], ios: list[Reading]) -> str:
    by_key_android = {r.key: r.value for r in android}
    by_key_ios = {r.key: r.value for r in ios}
    keys = sorted(set(by_key_android) | set(by_key_ios))
    width = max((len(k) for k in keys), default=0)
    rows = ["threshold parity (android | ios):"]
    for key in keys:
        a = by_key_android.get(key)
        i = by_key_ios.get(key)
        rows.append(f"  {key.ljust(width)}  android={a}  ios={i}")
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android-root", required=True, type=Path)
    parser.add_argument("--ios-root", required=True, type=Path)
    args = parser.parse_args()

    android_source, ios_source = _sources(args.android_root, args.ios_root)
    android = _extract(android_source)
    ios = _extract(ios_source)

    print(_format_summary(android, ios))

    errors = _compare(android, ios)
    if errors:
        print("\nFAIL: cross-platform threshold drift detected:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1
    print("\nOK: every threshold matches across Android + iOS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
