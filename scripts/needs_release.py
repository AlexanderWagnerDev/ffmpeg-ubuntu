#!/usr/bin/env python3
"""Check whether official upstream stable FFmpeg is newer than a public channel."""

import argparse
import gzip
import os
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from check_launchpad import fetch_versions
from latest_release import latest_release, version_tuple


def upstream_from_debian_version(value: str) -> str | None:
    match = re.match(r"^(?:[0-9]+:)?([0-9]+(?:\.[0-9]+)+)-", value)
    return match.group(1) if match else None


def publication_needs_update(latest: str, published_versions: list[str]) -> bool:
    versions = [upstream_from_debian_version(v) for v in published_versions]
    known = [v for v in versions if v]
    return not known or max(map(version_tuple, known)) < version_tuple(latest)


SERIES = ("noble", "resolute", "stonking")


def get_pages_versions(series: str) -> list[str]:
    if series not in SERIES:
        raise ValueError(f"Unsupported Ubuntu release: {series}")
    url = (
        "https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/"
        f"dists/{series}/main/binary-amd64/Packages.gz"
    )
    request = Request(url, headers={"User-Agent": "ffmpeg-ubuntu-updates/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read(5_000_000)
    except HTTPError as exc:
        if exc.code == 404:
            return []  # First Pages deployment has not occurred yet.
        raise
    text = gzip.decompress(data).decode("utf-8")
    result = []
    for section in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1)
            for line in section.splitlines()
            if ": " in line and not line[0].isspace()
        )
        if fields.get("Package") == "ffmpeg" and "Version" in fields:
            result.append(fields["Version"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=["ppa", "pages"], required=True)
    args = parser.parse_args()

    latest = latest_release()
    needed = False
    for series in SERIES:
        if args.channel == "ppa":
            versions = fetch_versions("alexanderwagnerdev", "ffmpeg", series)
        else:
            versions = get_pages_versions(series)
        changed = publication_needs_update(latest, versions)
        needed |= changed
        print(f"{args.channel}/{series}: {versions or 'none'}; stable {latest}: {changed}")
    print(f"Missing suite or newer stable FFmpeg release: {needed}")

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"update={'true' if needed else 'false'}\n")
            handle.write(f"version={latest}\n")


if __name__ == "__main__":
    main()
