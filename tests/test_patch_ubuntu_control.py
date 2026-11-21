"""Regression tests for Ubuntu FFmpeg runtime package relationships."""

import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from patch_ubuntu_control import (add_runtime_dependencies, add_device_library_dependency,
                                  FFMPEG_RUNTIME, current_runtime_packages,
                                  sync_abi_metadata)


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
