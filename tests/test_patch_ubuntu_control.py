"""Regression tests for Ubuntu FFmpeg runtime package relationships."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from patch_ubuntu_control import add_runtime_dependencies, FFMPEG_RUNTIME


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

    def test_missing_binary_fails(self):
        with self.assertRaises(ValueError):
            add_runtime_dependencies("Source: ffmpeg\n")


if __name__ == "__main__":
    unittest.main()
