#!/usr/bin/env python3
"""Add the official FFmpeg release-specific changes to a Debian changelog stanza."""

import argparse
from pathlib import Path
import re

VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+)+$")
HEADER = re.compile(r"^version ([0-9]+(?:\.[0-9]+)+):\s*$")
TRAILER = re.compile(r"^ -- .+ <[^<>]+>  .+$", re.MULTILINE)


def release_changes(upstream_changelog: str, version: str) -> list[str]:
    """Read the exact release section, without mixing in earlier releases."""
    if not VERSION.fullmatch(version):
        raise ValueError(f"Invalid FFmpeg release version: {version!r}")
    found = False
    changes = []
    for raw_line in upstream_changelog.splitlines():
        match = HEADER.fullmatch(raw_line.strip())
        if match:
            if found:
                break
            found = match.group(1) == version
            continue
        if not found:
            continue
        line = raw_line.strip().removeprefix("-").strip()
        if line:
            if any(ord(char) < 32 or ord(char) == 127 for char in line):
                raise ValueError("Unexpected control character in upstream Changelog")
            changes.append(line)
    if not found or not changes:
        raise ValueError(f"No official FFmpeg {version} release notes in Changelog")
    return changes


def add_release_notes(debian_changelog: str, version: str, changes: list[str]) -> str:
    """Insert upstream notes before the first stanza's maintainer signature."""
    if not VERSION.fullmatch(version) or not changes:
        raise ValueError("Missing or invalid release metadata")
    if not debian_changelog.startswith("ffmpeg ("):
        raise ValueError("Expected a Debian FFmpeg changelog")
    match = TRAILER.search(debian_changelog)
    if match is None:
        raise ValueError("No maintainer signature found in Debian changelog")
    first_line = debian_changelog.splitlines()[0]
    if not first_line.endswith("; urgency=medium"):
        raise ValueError("Unexpected Debian changelog header")
    notes = [
        f"  * Official FFmpeg {version} release changes (upstream Changelog):",
        *(f"    - {entry}" for entry in changes),
        f"  * Official source: https://ffmpeg.org/releases/ffmpeg-{version}.tar.xz",
    ]
    prefix = debian_changelog[: match.start()].rstrip("\n")
    suffix = debian_changelog[match.start() :]
    return prefix + "\n\n" + "\n".join(notes) + "\n\n" + suffix


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--debian", type=Path, required=True)
    args = parser.parse_args()

    official = args.upstream.read_text(encoding="utf-8")
    existing = args.debian.read_text(encoding="utf-8")
    changes = release_changes(official, args.version)
    updated = add_release_notes(existing, args.version, changes)
    args.debian.write_text(updated, encoding="utf-8")
    print(f"Embedded {len(changes)} official FFmpeg {args.version} changes into Debian changelog")


if __name__ == "__main__":
    main()
