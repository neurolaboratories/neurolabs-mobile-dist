#!/usr/bin/env python3
"""Minimal semver helpers shared by the dist manifest tooling.

The release train compares tags CONSTANTLY (is this dispatch newer? does it
belong to the current line?) and every prior comparison in this repo was a
plain string compare or no compare at all — which is how a v1.6.x backport
published after v1.7.7 overwrote `latest` and downgraded every SPM consumer on
`main`. String order says "v1.6.12" > "v1.1.13" but also "v1.6.9" > "v1.6.12",
so string compare is wrong in both directions.
"""
from __future__ import annotations

import re

_TAG = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<pre>[0-9A-Za-z.-]+))?$"
)


class InvalidVersion(ValueError):
    pass


def parse(tag: str) -> tuple[int, int, int, str]:
    """('v1.7.7') -> (1, 7, 7, ''). Raises InvalidVersion on anything else."""
    m = _TAG.match((tag or "").strip())
    if not m:
        raise InvalidVersion(f"Not a vMAJOR.MINOR.PATCH tag: {tag!r}")
    return (
        int(m.group("major")),
        int(m.group("minor")),
        int(m.group("patch")),
        m.group("pre") or "",
    )


def sort_key(tag: str) -> tuple[int, int, int, int, str]:
    """Total order over tags. A prerelease sorts BELOW its release
    (1.7.7-rc1 < 1.7.7), per semver."""
    major, minor, patch, pre = parse(tag)
    return (major, minor, patch, 0 if pre else 1, pre)


def compare(a: str, b: str) -> int:
    ka, kb = sort_key(a), sort_key(b)
    return (ka > kb) - (ka < kb)


def line_of(tag: str) -> str:
    """The MAJOR.MINOR release line a tag belongs to: 'v1.6.12' -> '1.6'.

    Lines are the unit of monotonicity here: v1.6.12 is newer than v1.7.7 in
    wall-clock time and older in every way a consumer cares about, so the two
    have to be tracked separately instead of fighting over one `latest` key.
    """
    major, minor, _, _ = parse(tag)
    return f"{major}.{minor}"
