import sys
import unittest

from papyrus.config_manager import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_mcp_config_uses_current_python(self):
        manager = ConfigManager()

        config = manager._mcp_server_config()

        self.assertEqual(config["command"], sys.executable)
        self.assertEqual(config["args"], ["-m", "papyrus.mcp_server"])
        self.assertNotIn("cwd", config)


if __name__ == "__main__":
    unittest.main()
