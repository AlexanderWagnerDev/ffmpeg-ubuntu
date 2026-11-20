#!/usr/bin/env python3
"""Generate deterministic Ubuntu PPA versions from Debian source versions."""

import argparse
import re

SERIES = {"noble": "24.04", "resolute": "26.04", "stonking": "26.10"}
SOURCE_VERSION_RE = re.compile(r"^(?:(?P<epoch>[0-9]+):)?(?P<upstream>[0-9][A-Za-z0-9.+:~]*)-(?P<revision>[A-Za-z0-9.+~]+)$")


def ubuntu_version(debian_version: str, series: str, revision: int) -> str:
    if series not in SERIES:
        raise ValueError(f"Unsupported Ubuntu series: {series}")
    if revision < 1:
        raise ValueError("PPA revision must be a positive integer")
    match = SOURCE_VERSION_RE.fullmatch(debian_version)
    if not match:
        raise ValueError(f"Invalid Debian source version: {debian_version}")
    upstream = match.group("upstream")
    if int(upstream.split(".", 1)[0]) < 9:
        raise ValueError(f"Unsupported FFmpeg release: {upstream}")
    return f"{debian_version}+ubuntu{SERIES[series]}~ppa{revision}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("debian_version")
    parser.add_argument("series", choices=sorted(SERIES))
    parser.add_argument("revision", type=int)
    args = parser.parse_args()
    try:
        print(ubuntu_version(args.debian_version, args.series, args.revision))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
