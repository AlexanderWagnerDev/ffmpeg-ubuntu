#!/usr/bin/env python3
"""Fail closed on duplicate/older uploads to a Launchpad PPA.

Requires only Python stdlib and dpkg from the runner. Does NOT authenticate or
publish anything. API/network errors are fatal rather than assuming a PPA exists.
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlencode, urlparse, urljoin
from urllib.request import Request, urlopen

BASE = "https://api.launchpad.net/devel"
SAFE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def read_changes(path: Path) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8")
    matches = {}
    for line in data.splitlines():
        if line.startswith(("Version: ", "Distribution: ", "Source: ")):
            key, val = line.split(": ", 1)
            matches[key] = val.strip()
    if matches.get("Source") != "ffmpeg":
        raise ValueError("Expected ffmpeg as source package")
    if not matches.get("Version") or not matches.get("Distribution"):
        raise ValueError("Invalid .changes metadata")
    return matches["Version"], matches["Distribution"]


def greater_or_equal(current: str, candidate: str) -> bool:
    result = subprocess.run(
        ["dpkg", "--compare-versions", current, "ge", candidate], check=False
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"dpkg version comparison failed: {result.returncode}")
    return result.returncode == 0


def fetch_versions(owner: str, archive: str, series: str) -> list[str]:
    for label, value in (("owner", owner), ("archive", archive), ("series", series)):
        if not SAFE_NAME.fullmatch(value):
            raise ValueError(f"Invalid {label}: {value!r}")
    archive_url = f"{BASE}/~{owner}/+archive/ubuntu/{archive}"
    query = urlencode({
        "ws.op": "getPublishedSources",
        "source_name": "ffmpeg",
        "exact_match": "true",
        "distro_series": f"{BASE}/ubuntu/{series}",
        "ws.size": 100,
    })
    page = f"{archive_url}?{query}"
    versions: list[str] = []
    for _ in range(30):
        parsed = urlparse(page)
        if parsed.scheme != "https" or parsed.netloc != "api.launchpad.net":
            raise RuntimeError(f"Unexpected Launchpad pagination URL: {page}")
        req = Request(page, headers={"Accept": "application/json", "User-Agent": "ffmpeg-ubuntu-ppa/1.0"})
        with urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        if not isinstance(body, dict) or not isinstance(body.get("entries"), list):
            raise ValueError("Unexpected Launchpad API response")
        for entry in body["entries"]:
            version = entry.get("source_package_version")
            if isinstance(version, str):
                versions.append(version)
        next_page = body.get("next_collection_link")
        if not next_page:
            return versions
        page = urljoin(page, next_page)
    raise RuntimeError("Launchpad pagination limit exceeded")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--series", required=True)
    parser.add_argument("--changes", type=Path, required=True)
    args = parser.parse_args()
    version, suite = read_changes(args.changes)
    if suite != args.series:
        parser.error(f"Suite mismatch: {suite} vs {args.series}")
    published = fetch_versions(args.owner, args.archive, args.series)
    conflicts = [v for v in published if greater_or_equal(v, version)]
    publish = not conflicts
    if conflicts:
        print(f"Skipping {version}: Launchpad already knows a same/newer version: {conflicts[0]}")
    else:
        print(f"No same/newer ffmpeg source version found for {args.series}.")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"publish={'true' if publish else 'false'}\n")


if __name__ == "__main__":
    main()
