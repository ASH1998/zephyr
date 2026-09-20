from __future__ import annotations

import unittest
from unittest.mock import patch

from zephyr.config import ConfigurationError, load_env_file, load_llm_config


class ConfigTests(unittest.TestCase):
    def test_alternate_endpoint_is_selected_by_configured_identity(self):
        values={'ZEPHYR_NEMOTRON_MODEL':'primary','ZEPHYR_ACTIVE_MODEL':'primary',
                'ZEPHYR_TOKEN_FACTORY_BASE_URL':'https://primary.invalid/v1/',
                'ZEPHYR_TOKEN_FACTORY_BASE_URL_V2':'https://alternate.invalid/v1/'}
        self.assertEqual(load_llm_config(values).base_url,'https://primary.invalid/v1')
        self.assertEqual(load_llm_config(values|{'ZEPHYR_ACTIVE_MODEL':'development'}).base_url,'https://alternate.invalid/v1')
        self.assertEqual(load_llm_config(values|{'ZEPHYR_ACTIVE_MODEL':'development','ZEPHYR_TOKEN_FACTORY_BASE_URL_V2':''}).base_url,'https://primary.invalid/v1')
    def test_active_model_can_change_without_changing_endpoint_or_key(self) -> None:
        common = {
            "NEBIUS_API_KEY": "secret",
            "ZEPHYR_TOKEN_FACTORY_BASE_URL": "https://example.invalid/v1/",
        }
        first = load_llm_config({**common, "ZEPHYR_ACTIVE_MODEL": "development-model"}, require_credentials=True)
        final = load_llm_config({**common, "ZEPHYR_ACTIVE_MODEL": "nvidia/nemotron"}, require_credentials=True)
        self.assertEqual(first.api_key, final.api_key)
        self.assertEqual(first.base_url, final.base_url)
        self.assertNotEqual(first.model, final.model)
        self.assertNotIn("secret", str(final.sanitized()))

    def test_env_file_does_not_override_shell_values(self) -> None:
        with patch("zephyr.config.Path") as path_type:
            target = path_type.return_value
            target.is_file.return_value = True
            target.read_text.return_value = "NEBIUS_API_KEY=file-key\nZEPHYR_ACTIVE_MODEL='nvidia/nemotron'\n"
            environ = {"NEBIUS_API_KEY": "shell-key"}
            self.assertTrue(load_env_file("ignored.env", environ=environ))
            self.assertEqual(environ["NEBIUS_API_KEY"], "shell-key")
            self.assertEqual(environ["ZEPHYR_ACTIVE_MODEL"], "nvidia/nemotron")

    def test_incomplete_config_fails_closed_when_required(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_llm_config({}, require_credentials=True)


if __name__ == "__main__":
    unittest.main()
