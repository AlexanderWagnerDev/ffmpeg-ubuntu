"""Targeted regression tests for Ubuntu 24.04 FFmpeg packaging."""

import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from patch_noble_compat import (
    VULKAN_ONLY, mark_vulkan_symbols_optional, patch, skip_broken_dwz,
)


SYMBOLS = """libavutil.so.61 libavutil61 #MINVER#
 av_gcd@LIBAVUTIL_61 7:8.0
 av_vk_get_optional_device_extensions@LIBAVUTIL_61 7:8.1
 av_vk_get_optional_instance_extensions@LIBAVUTIL_61 7:8.1
 av_write_image_line2@LIBAVUTIL_61 7:8.0
"""


class NobleCompatibilityTests(unittest.TestCase):
    def test_marks_only_vulkan_symbols_optional(self):
        updated = mark_vulkan_symbols_optional(SYMBOLS)
        for symbol in VULKAN_ONLY:
            self.assertIn(f" (optional){symbol}@LIBAVUTIL_61", updated)
        self.assertIn(" av_gcd@LIBAVUTIL_61", updated)
        self.assertNotIn("(optional)av_gcd", updated)

    def test_does_not_suppress_unknown_abi_regressions(self):
        with self.assertRaises(ValueError):
            mark_vulkan_symbols_optional(SYMBOLS.replace(
                " av_vk_get_optional_instance_extensions@LIBAVUTIL_61 7:8.1\n", ""
            ))

    def test_duplicate_symbol_is_rejected(self):
        with self.assertRaises(ValueError):
            mark_vulkan_symbols_optional(SYMBOLS + (
                " av_vk_get_optional_instance_extensions@LIBAVUTIL_61 7:8.1\n"
            ))

    def test_dwz_override_does_not_skip_dh_strip(self):
        updated = skip_broken_dwz("#!/usr/bin/make -f\n%:\n\tdh $@\n")
        self.assertIn("override_dh_dwz:\n\t@true", updated)
        self.assertNotIn("override_dh_strip", updated)

    def test_conflicting_override_fails_closed(self):
        with self.assertRaises(ValueError):
            skip_broken_dwz("override_dh_dwz:\n\tdh_dwz\n")

    def test_files_edited_only_after_validation(self):
        with tempfile.TemporaryDirectory() as root:
            debian = Path(root)
            rules = debian / "rules"
            symbols = debian / "libavutil61.symbols"
            rules.write_text("%:\n\tdh $@\n")
            symbols.write_text(SYMBOLS)
            patch(debian)
            self.assertIn("override_dh_dwz", rules.read_text())
            self.assertIn("(optional)av_vk_get", symbols.read_text())

    def test_validation_error_does_not_write_rules(self):
        with tempfile.TemporaryDirectory() as root:
            debian = Path(root)
            rules = debian / "rules"
            symbols = debian / "libavutil61.symbols"
            original = "%:\n\tdh $@\n"
            rules.write_text(original)
            symbols.write_text("invalid symbols\n")
            with self.assertRaises(ValueError):
                patch(debian)
            self.assertEqual(rules.read_text(), original)


if __name__ == "__main__":
    unittest.main()
