import importlib.util
import pathlib
import subprocess
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "package_version.py"
SPEC = importlib.util.spec_from_file_location("package_version", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PackageVersionTests(unittest.TestCase):
    def test_resolute_version(self):
        self.assertEqual(
            MODULE.ubuntu_version("7:9.0.2-6", "resolute", 1),
            "7:9.0.2-6.1~resolute",
        )

    def test_supported_series(self):
        self.assertEqual(MODULE.ubuntu_version("7:9.0.2-6", "noble", 3),
                         "7:9.0.2-6.3~noble")
        self.assertEqual(MODULE.ubuntu_version("7:9.0.2-6", "resolute", 2),
                         "7:9.0.2-6.2~resolute")
        self.assertEqual(MODULE.ubuntu_version("7:9.0.2-6", "stonking", 3),
                         "7:9.0.2-6.3~stonking")
        with self.assertRaises(ValueError):
            MODULE.ubuntu_version("7:9.0.2-6", "jammy", 1)

    def test_rejects_wrong_major(self):
        for version in ("7:8.1-3", "not-a-version"):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    MODULE.ubuntu_version(version, "resolute", 1)

    def test_future_major(self):
        self.assertEqual(MODULE.ubuntu_version("7:10.0-1", "resolute", 2),
                         "7:10.0-1.2~resolute")

    def test_versions_upgrade_from_old_ubuntu_suffix(self):
        for series, previous in (
            ("noble", "7:9.0.2-6+ubuntu24.04~ppa1"),
            ("resolute", "7:9.0.2-6+ubuntu26.04~ppa1"),
            ("stonking", "7:9.0.2-6+ubuntu26.10~ppa1"),
        ):
            with self.subTest(series=series):
                current = MODULE.ubuntu_version("7:9.0.2-6", series, 1)
                self.assertEqual(
                    subprocess.run(
                        ["dpkg", "--compare-versions", current, "gt", previous],
                        check=False,
                    ).returncode,
                    0,
                )

    def test_debian_version_ordering(self):
        before = MODULE.ubuntu_version("7:9.0.2-6", "resolute", 1)
        after = MODULE.ubuntu_version("7:9.0.2-6", "resolute", 2)
        self.assertEqual(
            subprocess.run(
                ["dpkg", "--compare-versions", after, "gt", before],
                check=False,
            ).returncode,
            0,
        )
        self.assertEqual(
            subprocess.run(
                ["dpkg", "--compare-versions", "7:9.0.2-7", "gt", after],
                check=False,
            ).returncode,
            0,
        )

    def test_rejects_bad_series_and_revision(self):
        with self.assertRaises(ValueError):
            MODULE.ubuntu_version("7:9.0.2-6", "oracular", 1)
        with self.assertRaises(ValueError):
            MODULE.ubuntu_version("7:9.0.2-6", "resolute", 0)


if __name__ == "__main__":
    unittest.main()
