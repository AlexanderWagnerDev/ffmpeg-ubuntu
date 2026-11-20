"""Guard the publicly supported Ubuntu suites and six native build targets."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "scripts/package_version.py"
spec = importlib.util.spec_from_file_location("package_version", VERSION_PATH)
versions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versions)

SERIES = {"noble": "24.04", "resolute": "26.04", "stonking": "26.10"}


class SupportedUbuntuTests(unittest.TestCase):
    def test_supported_release_map(self):
        self.assertEqual(versions.SERIES, SERIES)

    def test_source_workflows_list_all_three(self):
        for workflow in ("build-source.yml", "publish-ppa.yml", "pages-apt.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text()
            for suite in SERIES:
                with self.subTest(workflow=workflow, suite=suite):
                    self.assertIn(suite, text)

    def test_native_architecture_matrix(self):
        for workflow in ("binary-ci.yml", "pages-apt.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text()
            for suite in SERIES:
                for arch in ("amd64", "arm64"):
                    with self.subTest(workflow=workflow, suite=suite, arch=arch):
                        self.assertIn(f"- series: {suite}\n            arch: {arch}", text)

    def test_retired_release_is_not_configured(self):
        paths = (
            list((ROOT / "scripts").glob("*.sh")) +
            list((ROOT / "scripts").glob("*.py")) +
            list((ROOT / ".github/workflows").glob("*.yml")) +
            [ROOT / "README.md", ROOT / "docs/INSTALLATION.md"]
        )
        for path in paths:
            text = path.read_text()
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("jammy", text)
                self.assertNotIn("22.04", text)


if __name__ == "__main__":
    unittest.main()
