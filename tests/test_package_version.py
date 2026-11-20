import importlib.util
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "package_version.py"
SPEC = importlib.util.spec_from_file_location("package_version", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PackageVersionTests(unittest.TestCase):
    def test_resolute_version(self):
        self.assertEqual(
            MODULE.ubuntu_version("7:9.0.2-6", "resolute", 1),
            "7:9.0.2-6+ubuntu26.04~ppa1",
        )

    def test_supported_series(self):
        self.assertIn("ubuntu24.04", MODULE.ubuntu_version("7:9.0.2-6", "noble", 3))
        self.assertIn("ubuntu26.04", MODULE.ubuntu_version("7:9.0.2-6", "resolute", 2))
        self.assertIn("ubuntu26.10", MODULE.ubuntu_version("7:9.0.2-6", "stonking", 3))
        with self.assertRaises(ValueError):
            MODULE.ubuntu_version("7:9.0.2-6", "jammy", 1)

    def test_rejects_wrong_major(self):
        for version in ("7:8.1-3", "not-a-version"):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    MODULE.ubuntu_version(version, "resolute", 1)

    def test_future_major(self):
        self.assertEqual(MODULE.ubuntu_version("7:10.0-1", "resolute", 2),
                         "7:10.0-1+ubuntu26.04~ppa2")

    def test_rejects_bad_series_and_revision(self):
        with self.assertRaises(ValueError):
            MODULE.ubuntu_version("7:9.0.2-6", "oracular", 1)
        with self.assertRaises(ValueError):
            MODULE.ubuntu_version("7:9.0.2-6", "resolute", 0)


if __name__ == "__main__":
    unittest.main()
