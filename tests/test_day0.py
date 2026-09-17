from __future__ import annotations

import unittest

from zephyr.probes.day0 import requested_gates_pass


class Day0ReportTests(unittest.TestCase):
    def test_requested_gates_pass_only_when_ready(self) -> None:
        report = {
            "domino_bundle": {"ready": True},
            "token_factory": {
                "requested": True,
                "reachable": True,
                "structured_probe": {"passed": True},
                "error": None,
            },
        }
        self.assertTrue(requested_gates_pass(report))
        report["domino_bundle"]["ready"] = False
        self.assertFalse(requested_gates_pass(report))


if __name__ == "__main__":
    unittest.main()

