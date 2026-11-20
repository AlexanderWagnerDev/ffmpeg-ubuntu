"""Exercise Launchpad source-status filtering without live API calls."""

import io
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_launchpad import fetch_versions, REMOVED_SOURCE_STATUSES


class LaunchpadSourceStatusTests(unittest.TestCase):
    def setUp(self):
        self.entries = [
            {"source_package_version": "7:9.0.2-6.1~resolute", "status": "Published"},
            {"source_package_version": "7:9.0.2-6.2~resolute", "status": "Pending"},
            {"source_package_version": "7:9.0.2-6.3~resolute", "status": "Superseded"},
            {"source_package_version": "7:9.0.2-6.4~resolute", "status": "Deleted"},
            {"source_package_version": "7:9.0.2-6.5~resolute", "status": "Obsolete"},
        ]

    def get_versions(self, exclude_removed):
        body = io.BytesIO(json.dumps({"entries": self.entries}).encode("utf-8"))
        with patch("check_launchpad.urlopen", return_value=body):
            return fetch_versions(
                "alexanderwagnerdev", "ffmpeg", "resolute",
                exclude_removed=exclude_removed,
            )

    def test_removed_sources_are_not_current(self):
        current = self.get_versions(exclude_removed=True)
        self.assertEqual(len(current), 3)
        self.assertTrue(current[-1].endswith(".3~resolute"))

    def test_historical_uploads_remain_conflicts(self):
        versions = self.get_versions(exclude_removed=False)
        self.assertEqual(len(versions), 5)
        self.assertTrue(versions[-1].endswith(".5~resolute"))

    def test_only_deleted_and_obsolete_are_excluded(self):
        self.assertEqual(REMOVED_SOURCE_STATUSES, frozenset({"Deleted", "Obsolete"}))

    def test_unknown_status_is_not_silently_dropped(self):
        self.entries.append({
            "source_package_version": "7:9.0.2-6.6~resolute",
            "status": "Mystery",
        })
        versions = self.get_versions(exclude_removed=True)
        self.assertTrue(versions[-1].endswith(".6~resolute"))


if __name__ == "__main__":
    unittest.main()
