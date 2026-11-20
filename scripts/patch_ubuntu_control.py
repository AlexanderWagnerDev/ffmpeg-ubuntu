#!/usr/bin/env python3
"""Ensure FFmpeg tools depend on their matching runtime libraries.

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


def add_runtime_dependencies(control: str, packages: tuple[str, ...] = FFMPEG_RUNTIME) -> str:
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
        if len(dep_positions) > 1:
            raise ValueError("Multiple Depends fields for ffmpeg")
        if not dep_positions:
            # Debian's current FFmpeg package stanza has no explicit Depends
            # field, so the Ubuntu rebuild generated a broken standalone CLI.
            # Create the field rather than assuming dh_shlibdeps will do it.
            package_pos = next(
                (i for i, line in enumerate(lines) if line.startswith("Package: ffmpeg")),
                None,
            )
            if package_pos is None:
                raise ValueError("Missing ffmpeg package field")
            pos = package_pos + 1
            while pos < len(lines) and lines[pos][:1] in (" ", "\t"):
                pos += 1
            lines.insert(pos, "Depends: ${shlibs:Depends}, ${misc:Depends},\n")
            dep_positions = [pos]
        pos = dep_positions[0] + 1
        while pos < len(lines) and lines[pos][:1] in (" ", "\t"):
            pos += 1
        original = "".join(lines[dep_positions[0]:pos])
        if f"{packages[1]} (= ${binary:Version})" in original:
            continue
        last = pos - 1
        lines[last] = lines[last].rstrip("\n").rstrip().rstrip(",") + ",\n"
        extra = "".join(
            f" {package} (= ${{binary:Version}}){',' if i + 1 < len(packages) else ''}\n"
            for i, package in enumerate(packages)
        )
        lines.insert(pos, extra)
        paragraphs[index] = "".join(lines)
    if match_count != 1:
        raise ValueError(f"Expected one ffmpeg binary package stanza, got {match_count}")
    return "".join(paragraphs)


def current_runtime_packages(source_root: Path) -> tuple[str, ...]:
    """Resolve current library SONAME package names from upstream headers."""
    packages = []
    for old in FFMPEG_RUNTIME:
        match = re.fullmatch(r"(lib[a-z]+?)(\d+)", old)
        if not match:
            raise ValueError(f"Unexpected FFmpeg package name: {old}")
        prefix = match.group(1)
        header = source_root / prefix / "version_major.h"
        macro = prefix.upper() + "_VERSION_MAJOR"
        if not header.is_file():
            raise ValueError(f"Missing version header: {header}")
        match = re.search(
            rf"(?m)^#define\s+{re.escape(macro)}\s+(\d+)\b",
            header.read_text(encoding="utf-8"),
        )
        if not match:
            raise ValueError(f"Missing {macro} in {header}")
        packages.append(prefix + match.group(1))
    return tuple(packages)


def sync_abi_metadata(debian: Path, packages: tuple[str, ...]) -> None:
    """Update Debian metadata for new SONAMEs without modifying upstream files."""
    replacement = {}
    for old, new in zip(FFMPEG_RUNTIME, packages):
        if old == new:
            continue
        replacement[old] = new
        old_prefix, old_major = re.fullmatch(r"(.+?)(\d+)", old).groups()
        new_prefix, new_major = re.fullmatch(r"(.+?)(\d+)", new).groups()
        replacement[old_prefix + "-extra" + old_major] = new_prefix + "-extra" + new_major
        replacement[old_prefix + ".so." + old_major] = new_prefix + ".so." + new_major

    def rewrite(value: str) -> str:
        for old, new in sorted(replacement.items(), key=lambda item: -len(item[0])):
            value = re.sub(rf"(?<![A-Za-z0-9_-]){re.escape(old)}(?![0-9])", new, value)
        return value

    if not replacement:
        return
    for file in debian.rglob("*"):
        if not file.is_file() or file.is_symlink():
            continue
        if file.name == "changelog" or "patches" in file.relative_to(debian).parts:
            continue
        try:
            original = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        result = rewrite(original)
        if result != original:
            file.write_text(result, encoding="utf-8")
    for file in list(debian.iterdir()):
        name = rewrite(file.name)
        if name != file.name:
            target = file.with_name(name)
            if target.exists():
                raise ValueError(f"Debian packaging filename conflict: {target}")
            file.rename(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path)
    args = parser.parse_args()
    packages = current_runtime_packages(args.control.parent.parent)
    sync_abi_metadata(args.control.parent, packages)
    content = args.control.read_text(encoding="utf-8")
    updated = add_runtime_dependencies(content, packages)
    args.control.write_text(updated, encoding="utf-8")
    print("Verified FFmpeg runtime library and ABI dependencies")


if __name__ == "__main__":
    main()
