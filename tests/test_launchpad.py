import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_launchpad.py"
spec = importlib.util.spec_from_file_location("check_launchpad", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LaunchpadTests(TestCase):
    def test_parse_changes(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "ffmpeg.changes"
            file.write_text(
                "Format: 1.8\nSource: ffmpeg\nVersion: 7:9.0.2-6+ubuntu26.04~ppa1\n"
                "Distribution: resolute\n", encoding="utf-8",
            )
            self.assertEqual(
                module.read_changes(file),
                ("7:9.0.2-6+ubuntu26.04~ppa1", "resolute"),
            )

    def test_rejects_wrong_source(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "other.changes"
            file.write_text("Source: other\nVersion: 1\nDistribution: resolute\n")
            with self.assertRaises(ValueError):
                module.read_changes(file)

    def test_debian_epochs_and_revisions(self):
        self.assertTrue(module.greater_or_equal("7:9.0.2-6+ubuntu26.04~ppa2",
                                                 "7:9.0.2-6+ubuntu26.04~ppa1"))
        self.assertFalse(module.greater_or_equal("7:9.0.2-6+ubuntu26.04~ppa1",
                                                  "7:9.0.2-6+ubuntu26.04~ppa2"))

    def test_rejects_unsafe_owner(self):
        with self.assertRaises(ValueError):
            module.fetch_versions("bad/owner", "ffmpeg", "resolute")

    @patch.object(module, "urlopen")
    def test_reads_launchpad_response(self, urlopen):
        from io import BytesIO
        result = {"entries": [
            {"source_package_version": "7:9.0.2-6+ubuntu26.04~ppa1"},
        ], "next_collection_link": None}
        response = MagicMock()
        response.__enter__.return_value = BytesIO(__import__("json").dumps(result).encode())
        urlopen.return_value = response
        self.assertEqual(
            module.fetch_versions("alexanderwagnerdev", "ffmpeg", "resolute"),
            ["7:9.0.2-6+ubuntu26.04~ppa1"],
        )
