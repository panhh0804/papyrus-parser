import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from papyrus.settings import load_config


class SettingsTests(unittest.TestCase):
    def test_loads_defaults_from_user_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / ".papyrus"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text(
                "[defaults]\nformat = \"json\"\ncache = false\nbatch_executor = \"processes\"\nworkers = 2\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"HOME": tmp}):
                config = load_config()

        self.assertEqual(config["format"], "json")
        self.assertFalse(config["cache"])
        self.assertEqual(config["batch_executor"], "processes")
        self.assertEqual(config["workers"], 2)


if __name__ == "__main__":
    unittest.main()
