from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


from public_opinion.config import get_openai_settings


class ConfigTests(unittest.TestCase):
    def test_get_openai_settings_loads_values_from_env_file(self) -> None:
        keys = [
            "PUBLIC_OPINION_ENV_FILE",
            "PUBLIC_OPINION_OPENAI_BASE_URL",
            "PUBLIC_OPINION_OPENAI_API_KEY",
            "PUBLIC_OPINION_OPENAI_MODEL",
            "PUBLIC_OPINION_OPENAI_TIMEOUT_SECONDS",
        ]
        old_values = {key: os.environ.get(key) for key in keys}

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                env_path = Path(tmp_dir) / ".env"
                env_path.write_text(
                    "\n".join(
                        [
                            "PUBLIC_OPINION_OPENAI_BASE_URL=https://example.com/v1",
                            "PUBLIC_OPINION_OPENAI_API_KEY=test-key",
                            "PUBLIC_OPINION_OPENAI_MODEL=test-model",
                            "PUBLIC_OPINION_OPENAI_TIMEOUT_SECONDS=45",
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )

                for key in keys:
                    os.environ.pop(key, None)
                os.environ["PUBLIC_OPINION_ENV_FILE"] = str(env_path)

                settings = get_openai_settings()
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.assertEqual(settings.base_url, "https://example.com/v1")
        self.assertEqual(settings.api_key, "test-key")
        self.assertEqual(settings.model, "test-model")
        self.assertEqual(settings.timeout_seconds, 45)


if __name__ == "__main__":
    unittest.main()
