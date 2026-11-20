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


def get_pages_versions() -> list[str]:
    url = (
        "https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/"
        "dists/resolute/main/binary-amd64/Packages.gz"
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
    if args.channel == "ppa":
        versions = fetch_versions("alexanderwagnerdev", "ffmpeg", "resolute")
    else:
        versions = get_pages_versions()
    needed = publication_needs_update(latest, versions)
    print(f"Latest stable FFmpeg: {latest}; published {args.channel}: {versions or 'none'}")
    print(f"New stable version available for {args.channel}: {needed}")

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"update={'true' if needed else 'false'}\n")
            handle.write(f"version={latest}\n")


if __name__ == "__main__":
    main()
