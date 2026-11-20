#!/usr/bin/env python3
"""Block a GitHub Pages APT deployment that would downgrade any supported target."""

import argparse
import gzip
import os
from pathlib import Path
import subprocess

from needs_release import SERIES, get_pages_versions

ARCHES = ("amd64", "arm64")


def candidate_version(site: Path, series: str, arch: str) -> str:
    """Read the single FFmpeg binary version from a validated local APT index."""
    index = site / "dists" / series / "main" / f"binary-{arch}" / "Packages.gz"
    content = gzip.decompress(index.read_bytes()).decode("utf-8")
    versions = []
    for section in content.split("\n\n"):
        fields = {}
        for line in section.splitlines():
            if ": " in line and not line[0].isspace():
                key, value = line.split(": ", 1)
                fields[key] = value
        if fields.get("Package") == "ffmpeg" and fields.get("Version"):
            versions.append(fields["Version"])
    if len(versions) != 1:
        raise ValueError(f"Expected one FFmpeg binary in {index}, found {len(versions)}")
    return versions[0]


def is_older(candidate: str, published: str) -> bool:
    command = ["dpkg", "--compare-versions", candidate, "lt", published]
    completed = subprocess.run(command, check=False)
    if completed.returncode not in (0, 1):
        raise RuntimeError(f"dpkg version comparison failed: {completed.returncode}")
    return completed.returncode == 0


def deployment_is_safe(site: Path) -> tuple[bool, list[str]]:
    """Check every suite and architecture against the *live* Pages APT repository."""
    downgrades = []
    for series in SERIES:
        for arch in ARCHES:
            candidate = candidate_version(site, series, arch)
            published_versions = get_pages_versions(series, arch)
            for published in published_versions:
                if is_older(candidate, published):
                    downgrades.append(
                        f"{series}/{arch}: candidate {candidate} < published {published}"
                    )
    return not downgrades, downgrades


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    args = parser.parse_args()
    safe, downgrades = deployment_is_safe(args.site)
    print("Pages deployment allowed" if safe else "Pages deployment skipped: downgrade")
    for reason in downgrades:
        print(f"::warning::{reason}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"deploy={'true' if safe else 'false'}\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write("### GitHub Pages version guard\n")
            summary.write(
                "Publishing is allowed.\n" if safe else
                "Publishing skipped to prevent a package downgrade.\n"
            )
            for reason in downgrades:
                summary.write(f"- {reason}\n")


if __name__ == "__main__":
    main()
