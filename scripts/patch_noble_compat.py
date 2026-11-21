#!/usr/bin/env python3
"""Apply narrow Ubuntu Noble compatibility fixes to Debian FFmpeg packaging.

Noble's Vulkan headers (1.3.275) are older than FFmpeg's minimum (1.3.277).
Consequently two public, Vulkan-only libavutil symbols are not built. Mark
only these two symbols optional, rather than suppressing the ABI check.
Noble's dwz also fails on current FFmpeg DWARF; leave debug symbols intact.
"""

import argparse
from pathlib import Path
import re

VULKAN_ONLY = (
    "av_vk_get_optional_device_extensions",
    "av_vk_get_optional_instance_extensions",
)


def mark_vulkan_symbols_optional(symbols: str) -> str:
    """Allow absence of exactly two Vulkan-only symbols on Ubuntu Noble."""
    for name in VULKAN_ONLY:
        pattern = re.compile(
            rf"(?m)^(?P<indent>[ \t]+)(?P<symbol>{re.escape(name)}@LIBAVUTIL_\d+)"
            r"(?P<version>[ \t]+\S+[ \t]*)$"
        )
        if len(pattern.findall(symbols)) != 1:
            raise ValueError(f"Expected exactly one untagged Vulkan symbol: {name}")
        symbols, count = pattern.subn(
            lambda m: f'{m.group("indent")}(optional){m.group("symbol")}{m.group("version")}',
            symbols,
        )
        if count != 1:
            raise ValueError(f"Cannot annotate {name}")
    return symbols


def skip_broken_dwz(rules: str) -> str:
    """Skip only dwz optimization; dh_strip and debug package generation still run."""
    if re.search(r"(?m)^override_dh_dwz(?:-[a-z]+)?:", rules):
        raise ValueError("Debian rules already override dh_dwz; review manually")
    return rules.rstrip("\n") + (
        "\n\n# Noble's older dwz fails on FFmpeg's current DWARF loclist data.\n"
        "# Skip only debug-information optimization, not debug symbols or stripping.\n"
        "override_dh_dwz:\n\t@true\n"
    )


def patch(debian: Path) -> None:
    rules_file = debian / "rules"
    # Debian generates libavutil61.symbols from this template during the binary build.
    symbols_file = debian / "libavutil61.symbols.in"
    if not rules_file.is_file() or not symbols_file.is_file():
        raise FileNotFoundError("Expected Debian rules and libavutil61.symbols.in")
    rules = skip_broken_dwz(rules_file.read_text(encoding="utf-8"))
    symbols = mark_vulkan_symbols_optional(symbols_file.read_text(encoding="utf-8"))
    rules_file.write_text(rules, encoding="utf-8")
    symbols_file.write_text(symbols, encoding="utf-8")
    print("Noble: skipped incompatible dwz and annotated two Vulkan-only symbols")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("debian", type=Path)
    args = parser.parse_args()
    patch(args.debian)
