import tempfile
import unittest
from pathlib import Path

from papyrus.detector import detect_file_type
from papyrus.router import route_file


class DetectorTests(unittest.TestCase):
    def test_detects_common_extensions(self):
        self.assertEqual(detect_file_type("paper.pdf"), "pdf")
        self.assertEqual(detect_file_type("slides.pptx"), "pptx")
        self.assertEqual(detect_file_type("notes.markdown"), "markdown")
        self.assertEqual(detect_file_type("data.xlsx"), "excel")

    def test_unknown_extension_stays_unknown_for_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.unknownext"
            path.write_text("", encoding="utf-8")

            self.assertIn(detect_file_type(str(path)), {"unknown", "txt"})

    def test_router_rejects_unsupported_extension(self):
        self.assertEqual(route_file("deck.ppt"), "unsupported")


if __name__ == "__main__":
    unittest.main()
