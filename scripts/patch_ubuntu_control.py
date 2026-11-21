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


DEBHELPER_COMPAT_BY_SERIES = {
    "noble": 13,
    "resolute": 13,
    "stonking": 14,
}


def select_debhelper_compat(control: str, series: str) -> str:
    """Use the compatibility level available in the target Ubuntu release."""
    if series not in DEBHELPER_COMPAT_BY_SERIES:
        raise ValueError(f"Unsupported Ubuntu series: {series}")
    matches = list(re.finditer(r"\bdebhelper-compat\s*\(=\s*(\d+)\s*\)", control))
    if len(matches) != 1 or matches[0].group(1) not in ("13", "14"):
        raise ValueError("Unexpected Debian debhelper requirement; review the packaging")
    match = matches[0]
    level = DEBHELPER_COMPAT_BY_SERIES[series]
    return control[:match.start()] + f"debhelper-compat (= {level})" + control[match.end():]



def ensure_generated_dependencies(control: str) -> str:
    """Keep dpkg-shlibdeps dependencies for every native binary package.

    Debian's packaging can omit Depends fields in library stanzas; in that case
    dh_shlibdeps calculates the correct dependencies but dpkg-gencontrol discards
    them. Include the standard substvars without hardcoding external libraries.
    """
    paragraphs = re.split(r"(\n\n+)", control)
    for index in range(0, len(paragraphs), 2):
        paragraph = paragraphs[index]
        if not re.search(r"(?m)^Package: [^\n]+$", paragraph):
            continue
        architecture = re.search(r"(?m)^Architecture:\s*([^\n]+)", paragraph)
        if architecture is None or architecture.group(1).strip() == "all":
            continue

        lines = paragraph.splitlines(keepends=True)
        dep_positions = [i for i, line in enumerate(lines)
                         if line.startswith("Depends:")]
        if len(dep_positions) > 1:
            raise ValueError("Multiple Depends fields in binary package")
        if not dep_positions:
            package_pos = next(i for i, line in enumerate(lines)
                               if line.startswith("Package:"))
            lines.insert(package_pos + 1,
                         "Depends: ${shlibs:Depends}, ${misc:Depends}\n")
        else:
            start = dep_positions[0]
            end = start + 1
            while end < len(lines) and lines[end][:1] in (" ", "\t"):
                end += 1
            existing = "".join(lines[start:end])
            missing = [var for var in ("${shlibs:Depends}", "${misc:Depends}")
                       if var not in existing]
            if missing:
                first_value = lines[start][len("Depends:"):].strip()
                if first_value:
                    lines[start] = f"Depends: {', '.join(missing)},\n"
                    lines.insert(start + 1, f" {first_value}\n")
                elif end > start + 1:
                    lines[start] = f"Depends: {', '.join(missing)},\n"
                else:
                    lines[start] = f"Depends: {', '.join(missing)}\n"
        paragraphs[index] = "".join(lines)
    return "".join(paragraphs)


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
        if f"{packages[1]} (= ${{binary:Version}})" in original:
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



def add_device_library_dependency(
    control: str, device_package: str, dependency: str = "libraw1394-11"
) -> str:
    """Declare runtime libraw1394 dependency on the package that ships libavdevice.

    Debian's automatic shlibs dependency missed the dynamically linked library
    on Ubuntu 26.04 and 26.10. The test container had an installable package but
    ffmpeg could not load libraw1394.so.11 at startup.
    """
    paragraphs = re.split(r"(\n\n+)", control)
    matches = 0
    for index in range(0, len(paragraphs), 2):
        paragraph = paragraphs[index]
        if not re.search(rf"(?m)^Package: {re.escape(device_package)}$", paragraph):
            continue
        matches += 1
        lines = paragraph.splitlines(keepends=True)
        dep_positions = [i for i, line in enumerate(lines) if line.startswith("Depends:")]
        if len(dep_positions) > 1:
            raise ValueError(f"Multiple Depends fields in {device_package}")
        if not dep_positions:
            # Debian packaging may omit Depends and rely on generated
            # shlibs dependencies. Preserve those while adding libraw1394.
            package_pos = next(
                (i for i, line in enumerate(lines)
                 if line.rstrip("\n") == f"Package: {device_package}"),
                None,
            )
            if package_pos is None:
                raise ValueError(f"Missing {device_package} package field")
            insert_at = package_pos + 1
            while insert_at < len(lines) and lines[insert_at][:1] in (" ", "\t"):
                insert_at += 1
            lines.insert(insert_at, "Depends: ${shlibs:Depends}, ${misc:Depends}\n")
            dep_positions = [insert_at]
        start = dep_positions[0]
        end = start + 1
        while end < len(lines) and lines[end][:1] in (" ", "\t"):
            end += 1
        dependency_field = "".join(lines[start:end])
        if re.search(rf"(?<![A-Za-z0-9-]){re.escape(dependency)}(?![A-Za-z0-9-])",
                     dependency_field):
            continue
        lines[end - 1] = lines[end - 1].rstrip("\n").rstrip().rstrip(",") + ",\n"
        lines.insert(end, f" {dependency}\n")
        paragraphs[index] = "".join(lines)
    if matches != 1:
        raise ValueError(f"Expected one {device_package} binary package, got {matches}")
    return "".join(paragraphs)

def current_runtime_packages(source_root: Path) -> tuple[str, ...]:
    """Resolve current library SONAME package names from upstream headers."""
    packages = []
    for old in FFMPEG_RUNTIME:
        match = re.fullmatch(r"(lib[a-z]+?)(\d+)", old)
        if not match:
            raise ValueError(f"Unexpected FFmpeg package name: {old}")
        prefix = match.group(1)
        header = source_root / prefix / (
            "version.h" if prefix == "libavutil" else "version_major.h"
        )
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
    parser.add_argument("series", choices=tuple(DEBHELPER_COMPAT_BY_SERIES))
    args = parser.parse_args()
    packages = current_runtime_packages(args.control.parent.parent)
    sync_abi_metadata(args.control.parent, packages)
    content = args.control.read_text(encoding="utf-8")
    updated = select_debhelper_compat(content, args.series)
    updated = ensure_generated_dependencies(updated)
    updated = add_runtime_dependencies(updated, packages)
    updated = add_device_library_dependency(updated, packages[1])
    args.control.write_text(updated, encoding="utf-8")
    print(
        f"Using debhelper compat {DEBHELPER_COMPAT_BY_SERIES[args.series]} "
        f"for Ubuntu {args.series}; verified FFmpeg runtime and ABI dependencies"
    )


if __name__ == "__main__":
    main()
