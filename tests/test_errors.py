import tempfile
import unittest
from pathlib import Path

from papyrus.cli import parse_document
from papyrus.errors import CorruptFileError, EmptyOutputError, TemporaryFileError


class ErrorClassificationTests(unittest.TestCase):
    def test_office_lock_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "~$draft.docx"
            path.write_bytes(b"lock")

            with self.assertRaises(TemporaryFileError):
                parse_document(str(path), use_cache=False)

    def test_dot_tilde_office_lock_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".~draft.docx"
            path.write_bytes(b"lock")

            with self.assertRaises(TemporaryFileError):
                parse_document(str(path), use_cache=False)

    def test_empty_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.pdf"
            path.write_bytes(b"")

            with self.assertRaises(CorruptFileError):
                parse_document(str(path), use_cache=False)

    def test_empty_parser_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.md"
            path.write_text("   \n", encoding="utf-8")

            with self.assertRaises(EmptyOutputError):
                parse_document(str(path), use_cache=False)


if __name__ == "__main__":
    unittest.main()
