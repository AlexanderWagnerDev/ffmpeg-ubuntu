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
        for workflow in ("build-source.yml", "build-release.yml", "publish-ppa.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text()
            for suite in SERIES:
                with self.subTest(workflow=workflow, suite=suite):
                    self.assertIn(suite, text)

    def test_native_architecture_matrix(self):
        release = (ROOT / ".github/workflows/build-release.yml").read_text()
        for suite in SERIES:
            for arch in ("amd64", "arm64"):
                with self.subTest(workflow="build-release.yml", suite=suite, arch=arch):
                    self.assertIn(f"- series: {suite}\n            arch: {arch}", release)

        binary = (ROOT / ".github/workflows/binary-ci.yml").read_text()
        # The dynamic matrix expands to all six combinations on main/manual
        # and one Stonking/amd64 combination for pull requests.
        for entry in ('["noble","resolute","stonking"]', '["amd64","arm64"]',
                      '["stonking"]', '["amd64"]'):
            with self.subTest(matrix=entry):
                self.assertIn(entry, binary)
        self.assertIn("github.event_name == 'pull_request'", binary)
        self.assertIn("  pull_request:\n    paths:", binary)
        self.assertIn(
            "matrix.arch == 'arm64' && 'ubuntu-26.04-arm' || 'ubuntu-latest'",
            binary,
        )

    def test_stonking_pull_request_build_covers_source_and_binary(self):
        text = (ROOT / ".github/workflows/binary-ci.yml").read_text()
        required = (
            "Build Ubuntu source",
            "Verify package source",
            "Verify Ubuntu build dependencies",
            "Compile native FFmpeg packages",
            "Install and smoke-test FFmpeg",
        )
        positions = [text.index(step) for step in required]
        self.assertEqual(positions, sorted(positions))

    def test_only_pipeline_has_a_release_schedule(self):
        workflows = ROOT / ".github/workflows"
        scheduled = [
            path.name
            for path in workflows.glob("*.yml")
            if "  schedule:" in path.read_text()
        ]
        self.assertEqual(scheduled, ["release-pipeline.yml"])

    def test_release_steps_are_reusable_and_ordered(self):
        workflows = ROOT / ".github/workflows"
        pipeline = (workflows / "release-pipeline.yml").read_text()
        self.assertIn("  workflow_dispatch:", pipeline)
        self.assertIn("    needs: check", pipeline)
        self.assertEqual(pipeline.count("    needs: [check, build]"), 2)
        for workflow in (
            "check-release.yml",
            "build-release.yml",
            "pages-apt.yml",
            "publish-ppa.yml",
        ):
            with self.subTest(workflow=workflow):
                text = (workflows / workflow).read_text()
                self.assertIn("  workflow_call:", text)
                self.assertIn(f"uses: ./.github/workflows/{workflow}", pipeline)

    def test_channel_check_failures_do_not_block_other_channel(self):
        workflows = ROOT / ".github/workflows"
        checker = (workflows / "check-release.yml").read_text()
        pipeline = (workflows / "release-pipeline.yml").read_text()
        self.assertEqual(checker.count("        continue-on-error: true"), 2)
        self.assertIn("steps.pages.outcome", checker)
        self.assertIn("steps.ppa.outcome", checker)
        self.assertIn("  check-health:", pipeline)
        self.assertIn("needs.check.outputs.pages_check", pipeline)
        self.assertIn("needs.check.outputs.ppa_check", pipeline)

    def test_pages_downgrades_are_checked_before_deployment(self):
        text = (ROOT / ".github/workflows/pages-apt.yml").read_text()
        self.assertIn("check_pages_downgrade.py --site site", text)
        self.assertIn("if: steps.version-guard.outputs.deploy == 'true'", text)
        self.assertIn("if: needs.sign.outputs.deploy == 'true'", text)

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
