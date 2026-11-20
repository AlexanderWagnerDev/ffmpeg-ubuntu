"""Check that publishing cannot downgrade any Pages APT architecture or suite."""

import gzip
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_pages_downgrade import ARCHES, candidate_version, deployment_is_safe
from needs_release import SERIES


class PagesDowngradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        for series in SERIES:
            for arch in ARCHES:
                target = self.site / "dists" / series / "main" / f"binary-{arch}"
                target.mkdir(parents=True)
                content = (
                    "Package: ffmpeg\n"
                    "Version: 7:9.0.2-6.2~" + series + "\n"
                    "Architecture: " + arch + "\n\n"
                )
                (target / "Packages.gz").write_bytes(gzip.compress(content.encode()))

    def test_safe_for_unpublished_suites(self):
        with patch("check_pages_downgrade.get_pages_versions", return_value=[]):
            allowed, reasons = deployment_is_safe(self.site)
        self.assertTrue(allowed)
        self.assertEqual(reasons, [])

    def test_equal_and_newer_candidates_allowed(self):
        def current(series, arch):
            if arch == "amd64":
                return [f"7:9.0.2-6.2~{series}"]
            return [f"7:9.0.2-6.1~{series}"]
        with patch("check_pages_downgrade.get_pages_versions", side_effect=current):
            allowed, reasons = deployment_is_safe(self.site)
        self.assertTrue(allowed)
        self.assertEqual(reasons, [])

    def test_one_older_arm64_package_blocks_entire_deployment(self):
        def current(series, arch):
            if series == "resolute" and arch == "arm64":
                return ["7:9.0.2-6.3~resolute"]
            return []
        with patch("check_pages_downgrade.get_pages_versions", side_effect=current):
            allowed, reasons = deployment_is_safe(self.site)
        self.assertFalse(allowed)
        self.assertEqual(len(reasons), 1)
        self.assertIn("resolute/arm64", reasons[0])

    def test_missing_candidate_fails_closed(self):
        index = self.site / "dists/noble/main/binary-amd64/Packages.gz"
        index.unlink()
        with self.assertRaises(FileNotFoundError):
            candidate_version(self.site, "noble", "amd64")

    def test_live_repository_failure_is_not_treated_as_empty(self):
        with patch(
            "check_pages_downgrade.get_pages_versions",
            side_effect=OSError("Pages temporarily unavailable"),
        ):
            with self.assertRaises(OSError):
                deployment_is_safe(self.site)


if __name__ == "__main__":
    unittest.main()
