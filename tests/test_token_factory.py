from __future__ import annotations

import unittest

from zephyr.token_factory import (
    ModelInfo,
    TokenFactoryError,
    is_nvidia_candidate,
    parse_model_list,
    parse_structured_message,
    validate_constraint_probe,
)


class TokenFactoryTests(unittest.TestCase):
    def test_model_list_and_nvidia_filter(self) -> None:
        models = parse_model_list(
            {
                "object": "list",
                "data": [
                    {"id": "nvidia/Nemotron-Test", "owned_by": "system"},
                    {"id": "other/model", "owned_by": "other"},
                ],
            }
        )
        self.assertEqual([model.id for model in models], ["nvidia/Nemotron-Test", "other/model"])
        self.assertTrue(is_nvidia_candidate(models[0]))
        self.assertFalse(is_nvidia_candidate(models[1]))

    def test_invalid_model_payload_fails_closed(self) -> None:
        with self.assertRaises(TokenFactoryError):
            parse_model_list({"object": "list"})

    def test_structured_probe_contract(self) -> None:
        value = parse_structured_message(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"objective":"reduce_drag","locked_regions":["cabin"],"max_displacement_mm":4}',
                            "refusal": None,
                        }
                    }
                ]
            }
        )
        self.assertTrue(validate_constraint_probe(value))
        self.assertFalse(validate_constraint_probe({**value, "extra": True}))

    def test_truncated_completion_is_rejected_even_if_json_parses(self) -> None:
        with self.assertRaisesRegex(TokenFactoryError, "token limit"):
            parse_structured_message({"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]})

    def test_owner_can_mark_nvidia_candidate(self) -> None:
        self.assertTrue(is_nvidia_candidate(ModelInfo(id="some/model", owned_by="NVIDIA")))


if __name__ == "__main__":
    unittest.main()

