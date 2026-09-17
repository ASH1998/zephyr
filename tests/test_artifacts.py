from __future__ import annotations

from pathlib import Path
import unittest

from zephyr.artifacts import bundle_ready, validate_bundle


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ArtifactTests(unittest.TestCase):
    def test_missing_bundle_is_not_ready(self) -> None:
        checks = validate_bundle(FIXTURES / "manifest.json", FIXTURES / "missing-assets")
        self.assertFalse(bundle_ready(checks))
        self.assertEqual([item.exists for item in checks], [False, False])

    def test_nonempty_bundle_is_ready_without_pinned_checksums(self) -> None:
        self.assertTrue(
            bundle_ready(
                validate_bundle(FIXTURES / "single-manifest.json", FIXTURES / "assets")
            )
        )


if __name__ == "__main__":
    unittest.main()
