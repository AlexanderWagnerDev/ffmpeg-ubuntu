import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from needs_release import publication_needs_update, upstream_from_debian_version


class PublicationTests(unittest.TestCase):
    def test_new_major_needs_build(self):
        self.assertTrue(publication_needs_update("10.0", ["7:9.1-0+ubuntu26.04~ppa2"]))
        self.assertFalse(publication_needs_update("9.1", ["7:10.0-0+ubuntu26.04~ppa1"]))

    def test_rebuild_not_needed_for_same_upstream(self):
        self.assertFalse(publication_needs_update("9.1", ["7:9.1-0+ubuntu26.04~ppa1"]))
        self.assertTrue(publication_needs_update("9.1.1", ["7:9.1-0+ubuntu26.04~ppa1"]))

    def test_old_suffix_triggers_one_time_migration(self):
        old = ["7:9.0.2-6+ubuntu26.04~ppa1"]
        self.assertTrue(publication_needs_update("9.0.2", old, "resolute"))
        self.assertFalse(publication_needs_update(
            "9.0.2", ["7:9.0.2-6.1~resolute"], "resolute"
        ))
        self.assertFalse(publication_needs_update(
            "9.0.2",
            ["7:9.0.2-6+ubuntu26.04~ppa1", "7:9.0.2-6.1~resolute"],
            "resolute",
        ))

    def test_release_check_does_not_downgrade_upstream(self):
        self.assertFalse(publication_needs_update(
            "9.0.2", ["7:9.1-0.1~resolute"], "resolute"
        ))

    def test_release_check_validates_target_suite(self):
        with self.assertRaises(ValueError):
            publication_needs_update(
                "9.0.2", ["7:9.0.2-6.1~resolute"], "oracular"
            )

    def test_first_publication(self):
        self.assertTrue(publication_needs_update("9.1", []))

    def test_source_version_parsing(self):
        self.assertEqual(upstream_from_debian_version("7:9.0.2-6"), "9.0.2")
        self.assertEqual(upstream_from_debian_version("7:10.0-0+ubuntu26.04~ppa1"), "10.0")


if __name__ == "__main__":
    unittest.main()
