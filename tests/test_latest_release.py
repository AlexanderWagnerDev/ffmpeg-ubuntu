import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from latest_release import select_latest_release, version_tuple


class StableReleaseTests(unittest.TestCase):
    def test_prefers_latest_stable_major(self):
        page = """
        <a href="ffmpeg-9.0.2.tar.xz">9.0.2</a>
        <a href="ffmpeg-9.1.tar.xz">9.1</a>
        <a href="ffmpeg-10.0.tar.xz">10</a>
        <a href="ffmpeg-10.0-rc1.tar.xz">release candidate</a>
        <a href="ffmpeg-snapshot-git.tar.xz">nightly</a>
        """
        self.assertEqual(select_latest_release(page), "10.0")

    def test_selects_latest_patch(self):
        page = '<a href="ffmpeg-9.1.tar.xz"></a><a href="ffmpeg-9.1.1.tar.xz"></a>'
        self.assertEqual(select_latest_release(page), "9.1.1")

    def test_old_branches_ignored(self):
        with self.assertRaises(ValueError):
            select_latest_release('<a href="ffmpeg-8.1.3.tar.xz"></a>')

    def test_numeric_version_comparison(self):
        self.assertGreater(version_tuple("10.0"), version_tuple("9.99.9"))


if __name__ == "__main__":
    unittest.main()
