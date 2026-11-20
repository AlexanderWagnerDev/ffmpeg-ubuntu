#!/usr/bin/env python3
"""Resolve the latest official stable FFmpeg release (9.x and newer)."""

import argparse
from html.parser import HTMLParser
import re
from urllib.request import Request, urlopen

INDEX_URL = "https://ffmpeg.org/releases/"
RELEASE_NAME = re.compile(r"^ffmpeg-([0-9]+(?:\.[0-9]+)+)\.tar\.xz$")


def version_tuple(version: str) -> tuple[int, ...]:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", version):
        raise ValueError(f"Invalid stable version: {version!r}")
    return tuple(map(int, version.split(".")))


class ReleaseIndex(HTMLParser):
    def __init__(self):
        super().__init__()
        self.versions: set[str] = set()

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        match = RELEASE_NAME.fullmatch(dict(attrs).get("href", ""))
        if match:
            self.versions.add(match.group(1))


def select_latest_release(html: str, minimum_major: int = 9) -> str:
    parser = ReleaseIndex()
    parser.feed(html)
    valid = [v for v in parser.versions if version_tuple(v)[0] >= minimum_major]
    if not valid:
        raise ValueError("No FFmpeg stable releases found in the official index")
    return max(valid, key=lambda v: version_tuple(v) + (0,) * 8)


def latest_release(minimum_major: int = 9) -> str:
    request = Request(INDEX_URL, headers={"User-Agent": "ffmpeg-ubuntu/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read(4_000_000).decode("utf-8")
    return select_latest_release(html, minimum_major)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minimum-major", type=int, default=9)
    args = parser.parse_args()
    print(latest_release(args.minimum_major))


if __name__ == "__main__":
    main()
