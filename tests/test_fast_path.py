import tempfile
import unittest
from pathlib import Path

from papyrus.cli import parse_document
from papyrus.parsers.fast_path import parse_with_fast_path


class FastPathTests(unittest.TestCase):
    def test_markdown_is_read_directly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("# Title\n\nBody", encoding="utf-8")

            result = parse_with_fast_path(str(path), output_format="json")

        self.assertEqual(result["content"], "# Title\n\nBody")
        self.assertEqual(result["metadata"]["parser"], "text")

    def test_parse_document_json_has_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("hello", encoding="utf-8")

            result = parse_document(str(path), output_format="json")

        self.assertEqual(result["format"], "json")
        self.assertEqual(result["metadata"]["file"], "sample.txt")


if __name__ == "__main__":
    unittest.main()
