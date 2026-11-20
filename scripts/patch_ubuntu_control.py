#!/usr/bin/env python3
"""Ensure FFmpeg 9 tools depend on their matching runtime libraries.

The Debian package's automatic shlibs dependencies were insufficient on the
Ubuntu 26.04 rebuild: "apt install ffmpeg" produced an unstartable ffmpeg
binary. Explicit version-matched dependencies make APT install the libraries.
"""

import argparse
from pathlib import Path
import re

FFMPEG_RUNTIME = (
    "libavcodec63",
    "libavdevice63",
    "libavfilter12",
    "libavformat63",
    "libavutil61",
    "libswresample7",
    "libswscale10",
)


def add_runtime_dependencies(control: str) -> str:
    paragraphs = re.split(r"(\n\n+)", control)
    match_count = 0
    for index in range(0, len(paragraphs), 2):
        paragraph = paragraphs[index]
        if not re.search(r"(?m)^Package: ffmpeg$", paragraph):
            continue
        match_count += 1
        lines = paragraph.splitlines(keepends=True)
        dep_positions = [
            i for i, line in enumerate(lines)
            if line.startswith("Depends:")
        ]
        if len(dep_positions) != 1:
            raise ValueError("Expected exactly one Depends field for ffmpeg")
        pos = dep_positions[0] + 1
        while pos < len(lines) and lines[pos][:1] in (" ", "\t"):
            pos += 1
        original = "".join(lines[dep_positions[0]:pos])
        if "${shlibs:Depends}" not in original:
            raise ValueError("FFmpeg Depends field has unexpectedly changed")
        if "libavdevice63 (= ${binary:Version})" in original:
            continue
        last = pos - 1
        lines[last] = lines[last].rstrip("\n").rstrip().rstrip(",") + ",\n"
        extra = "".join(
            f" {package} (= $${{binary:Version}}){',' if i + 1 < len(FFMPEG_RUNTIME) else ''}\n"
            for i, package in enumerate(FFMPEG_RUNTIME)
        )
        lines.insert(pos, extra)
        paragraphs[index] = "".join(lines)
    if match_count != 1:
        raise ValueError(f"Expected one ffmpeg binary package stanza, got {match_count}")
    return "".join(paragraphs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path)
    args = parser.parse_args()
    content = args.control.read_text(encoding="utf-8")
    updated = add_runtime_dependencies(content)
    args.control.write_text(updated, encoding="utf-8")
    print("Verified explicit FFmpeg 9 runtime library dependencies")


if __name__ == "__main__":
    main()
