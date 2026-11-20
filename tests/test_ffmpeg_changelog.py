"""Check inclusion of authentic release-specific FFmpeg changes in Debian changelogs."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "ffmpeg_changelog", ROOT / "scripts/ffmpeg_changelog.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

UPSTREAM = """Entries are sorted chronologically.

version 9.1:
- Improved AAC encoder
- Add APV Vulkan encoder

version 9.0.2:
 Update for 9.0.2
 avcodec/vvc: Prevent OOB write
 avformat/http: free cookies

version 9.0:
- Animated WebP decoder
"""

DEBIAN = """ffmpeg (7:9.0.2-6+ubuntu26.04~ppa1) resolute; urgency=medium

  * Rebuild stable FFmpeg 9.0.2 for Ubuntu resolute.

 -- Alexander Wagner <info@alexanderwagnerdev.com>  Fri, 20 Nov 2026 21:58:06 +0000

ffmpeg (7:9.0.2-6) unstable; urgency=medium

  * Debian packaging change.

 -- Debian Maintainer <maintainer@example.org>  Thu, 19 Nov 2026 00:00:00 +0000
"""


class FFmpegChangelogTests(unittest.TestCase):
    def test_release_changes_are_exact_version_only(self):
        self.assertEqual(
            module.release_changes(UPSTREAM, "9.0.2"),
            ["Update for 9.0.2", "avcodec/vvc: Prevent OOB write",
             "avformat/http: free cookies"],
        )

    def test_newer_release_uses_only_its_section(self):
        self.assertEqual(
            module.release_changes(UPSTREAM, "9.1"),
            ["Improved AAC encoder", "Add APV Vulkan encoder"],
        )

    def test_missing_release_refuses_to_invent_notes(self):
        with self.assertRaises(ValueError):
            module.release_changes(UPSTREAM, "9.0.3")

    def test_invalid_release_refused(self):
        with self.assertRaises(ValueError):
            module.release_changes(UPSTREAM, "9.0.2\nInjected")

    def test_embeds_notes_in_first_debian_stanza(self):
        changes = module.release_changes(UPSTREAM, "9.0.2")
        result = module.add_release_notes(DEBIAN, "9.0.2", changes)
        self.assertIn("  * Official FFmpeg 9.0.2 release changes", result)
        self.assertIn("    - avcodec/vvc: Prevent OOB write", result)
        self.assertIn("  * Official source: https://ffmpeg.org/releases/ffmpeg-9.0.2.tar.xz", result)
        self.assertNotIn("Animated WebP", result)
        self.assertIn(" -- Alexander Wagner <info@alexanderwagnerdev.com>", result)
        self.assertIn(" -- Debian Maintainer <maintainer@example.org>", result)
        self.assertEqual(result.count("  * Debian packaging change."), 1)
        self.assertLess(result.index("    - avcodec/vvc:"), result.index(" -- Alexander"))

    def test_rejects_unexpected_debian_changelog(self):
        with self.assertRaises(ValueError):
            module.add_release_notes("not a Debian changelog", "9.0.2", ["Feature"])

    def test_rejects_empty_changes(self):
        with self.assertRaises(ValueError):
            module.add_release_notes(DEBIAN, "9.0.2", [])


if __name__ == "__main__":
    unittest.main()
