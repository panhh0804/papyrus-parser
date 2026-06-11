import tempfile
import unittest
from pathlib import Path

from papyrus.mcp_server import MCPServer


class MCPServerTests(unittest.TestCase):
    def test_tools_call_returns_mcp_content_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("# Hello", encoding="utf-8")

            response = MCPServer().handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "parse_document",
                        "arguments": {"file_path": str(path)},
                    },
                }
            )

        self.assertEqual(response["id"], 1)
        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["type"], "text")
        self.assertIn("# Hello", result["content"][0]["text"])
        self.assertEqual(result["structuredContent"]["format"], "markdown")

    def test_initialized_notification_has_no_response(self):
        response = MCPServer().handle_request(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )

        self.assertIsNone(response)

    def test_tool_schema_exposes_cache_flag(self):
        response = MCPServer().handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        )

        properties = response["result"]["tools"][0]["inputSchema"]["properties"]
        self.assertIn("use_cache", properties)
        self.assertIn("extract_images", properties)
        self.assertIn("image_dir", properties)


if __name__ == "__main__":
    unittest.main()
