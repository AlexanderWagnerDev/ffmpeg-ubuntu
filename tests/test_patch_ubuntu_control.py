"""Regression tests for Ubuntu FFmpeg runtime package relationships."""

import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from patch_ubuntu_control import (add_runtime_dependencies, add_device_library_dependency,
                                  ensure_generated_dependencies,
                                  FFMPEG_RUNTIME, current_runtime_packages,
                                  sync_abi_metadata, select_debhelper_compat)


CONTROL = """Source: ffmpeg
Maintainer: A Person <maintainer@example.com>

Package: ffmpeg
Architecture: any
Depends: ${shlibs:Depends}, ${misc:Depends}
Description: FFmpeg tools

Package: libavdevice63
Architecture: any
Depends: ${shlibs:Depends}, ${misc:Depends}
Description: Device library
"""


class DebhelperCompatibilityTests(unittest.TestCase):
    CONTROL = (
        "Source: ffmpeg\n"
        "Build-Depends: debhelper-compat (= 14), libfoo-dev\n"
        "\nPackage: ffmpeg\nArchitecture: any\n"
    )

    def test_suite_specific_compat(self):
        for suite, level in (("noble", 13), ("resolute", 13), ("stonking", 14)):
            with self.subTest(series=suite):
                result = select_debhelper_compat(self.CONTROL, suite)
                self.assertIn(f"debhelper-compat (= {level})", result)
                self.assertIn("libfoo-dev", result)
                self.assertEqual(result, select_debhelper_compat(result, suite))

    def test_upgrades_13_to_14_on_stonking(self):
        old = self.CONTROL.replace("debhelper-compat (= 14)", "debhelper-compat (= 13)")
        self.assertIn(
            "debhelper-compat (= 14)", select_debhelper_compat(old, "stonking")
        )

    def test_unknown_suite_fails(self):
        with self.assertRaises(ValueError):
            select_debhelper_compat(self.CONTROL, "jammy")

    def test_unexpected_upstream_level_fails(self):
        for value in ("debhelper-compat (= 15)", "debhelper-compat (= 12)", "other"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_debhelper_compat(
                    self.CONTROL.replace("debhelper-compat (= 14)", value),
                    "noble",
                )

    def test_multiple_debhelper_requirements_fail(self):
        with self.assertRaises(ValueError):
            select_debhelper_compat(
                self.CONTROL.replace("libfoo-dev", "debhelper-compat (= 13)"),
                "stonking",
            )



class GeneratedShlibsTests(unittest.TestCase):
    def test_adds_substvars_to_missing_native_package_dependencies(self):
        control = (
            "Source: ffmpeg\n\n"
            "Package: libavfilter12\nArchitecture: any\n"
            "Description: Filter library\n\n"
            "Package: ffmpeg-doc\nArchitecture: all\n"
            "Description: Architecture-independent documentation\n"
        )
        updated = ensure_generated_dependencies(control)
        self.assertIn(
            "Package: libavfilter12\n"
            "Depends: ${shlibs:Depends}, ${misc:Depends}\n"
            "Architecture: any\n",
            updated,
        )
        self.assertIn(
            "Package: ffmpeg-doc\nArchitecture: all\nDescription:",
            updated,
        )
        self.assertEqual(updated, ensure_generated_dependencies(updated))

    def test_preserves_existing_multiline_dependencies(self):
        control = (
            "Package: libavcodec63\nArchitecture: any\n"
            "Depends: libc6 (>= 2.39),\n libmfx1\nDescription: Library\n"
        )
        updated = ensure_generated_dependencies(control)
        self.assertIn(
            "Depends: ${shlibs:Depends}, ${misc:Depends},\n"
            " libc6 (>= 2.39),\n libmfx1\n",
            updated,
        )
        self.assertEqual(updated, ensure_generated_dependencies(updated))

    def test_adds_only_missing_substvars(self):
        control = (
            "Package: ffplay\nArchitecture: any\n"
            "Depends: ${misc:Depends}\nDescription: Player\n"
        )
        updated = ensure_generated_dependencies(control)
        self.assertIn(
            "Depends: ${shlibs:Depends},\n ${misc:Depends}\n",
            updated,
        )
        self.assertEqual(updated, ensure_generated_dependencies(updated))

    def test_rejects_duplicate_depends_fields(self):
        control = (
            "Package: libavfilter12\nArchitecture: any\n"
            "Depends: libc6\nDepends: libfoo\n"
        )
        with self.assertRaises(ValueError):
            ensure_generated_dependencies(control)


class RuntimeDependsTests(unittest.TestCase):
    def test_all_version_matched_libraries_included(self):
        modified = add_runtime_dependencies(CONTROL)
        for package in FFMPEG_RUNTIME:
            self.assertIn(f"{package} (= ${{binary:Version}})", modified)
        self.assertIn("${shlibs:Depends}", modified)
        self.assertIn("${misc:Depends}", modified)

    def test_adds_missing_depends_field(self):
        control = CONTROL.replace("Depends: ${shlibs:Depends}, ${misc:Depends}\nDescription: FFmpeg tools\n", "Description: FFmpeg tools\n")
        modified = add_runtime_dependencies(control)
        self.assertIn("Depends: ${shlibs:Depends}, ${misc:Depends},", modified)
        self.assertIn("libavdevice63 (= ${binary:Version})", modified)
        self.assertEqual(modified, add_runtime_dependencies(modified))

    def test_idempotent(self):
        once = add_runtime_dependencies(CONTROL)
        self.assertEqual(add_runtime_dependencies(once), once)

    def test_other_stanzas_preserved(self):
        result = add_runtime_dependencies(CONTROL)
        self.assertIn(
            "Package: libavdevice63\nArchitecture: any\n"
            "Depends: ${shlibs:Depends}, ${misc:Depends}",
            result,
        )

    def test_future_major_abi_package_names(self):
        target = (64, 64, 13, 64, 62, 8, 11)
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            debian = base / "debian"
            debian.mkdir()
            control_file = debian / "control"
            control_file.write_text(CONTROL)
            (debian / "libavcodec63.install").write_text(
                "usr/lib/*/libavcodec.so.63*\\n"
            )
            for old, major in zip(FFMPEG_RUNTIME, target):
                prefix = old.rstrip("0123456789")
                parent = base / prefix
                parent.mkdir()
                (parent / ("version.h" if prefix == "libavutil" else "version_major.h")).write_text(
                    f"#define {prefix.upper()}_VERSION_MAJOR {major}\\n"
                )
            packages = current_runtime_packages(base)
            sync_abi_metadata(debian, packages)
            metadata = add_runtime_dependencies(control_file.read_text(), packages)
            self.assertIn("libavcodec64 (= ${binary:Version})", metadata)
            self.assertIn("libavdevice64 (= ${binary:Version})", metadata)
            self.assertIn("Package: libavdevice64", metadata)
            self.assertTrue((debian / "libavcodec64.install").exists())

    def test_libavdevice_declares_raw1394_runtime_dependency(self):
        updated = add_device_library_dependency(CONTROL, "libavdevice63")
        self.assertIn(
            "Package: libavdevice63\\nArchitecture: any\\n"
            "Depends: ${shlibs:Depends}, ${misc:Depends},\\n"
            " libraw1394-11\\n",
            updated.replace("\n", "\\n"),
        )
        self.assertEqual(
            updated, add_device_library_dependency(updated, "libavdevice63")
        )
        self.assertNotIn("Package: ffmpeg\\nArchitecture: any\\nDepends: libraw1394", updated)

    def test_libavdevice_without_depends_field(self):
        # Current Debian FFmpeg source can omit Depends in the device stanza.
        control = CONTROL.replace(
            "Package: libavdevice63\nArchitecture: any\n"
            "Depends: ${shlibs:Depends}, ${misc:Depends}\n",
            "Package: libavdevice63\nArchitecture: any\n",
        )
        updated = add_device_library_dependency(control, "libavdevice63")
        self.assertIn(
            "Package: libavdevice63\n"
            "Depends: ${shlibs:Depends}, ${misc:Depends},\n"
            " libraw1394-11\n"
            "Architecture: any\n",
            updated,
        )
        self.assertEqual(
            updated, add_device_library_dependency(updated, "libavdevice63")
        )

    def test_missing_device_stanza_refuses_broken_dependencies(self):
        with self.assertRaises(ValueError):
            add_device_library_dependency(CONTROL, "libavdevice64")

    def test_missing_binary_fails(self):
        with self.assertRaises(ValueError):
            add_runtime_dependencies("Source: ffmpeg\n")


if __name__ == "__main__":
    unittest.main()
