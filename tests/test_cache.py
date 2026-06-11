import os
import tempfile
import unittest
from pathlib import Path

from papyrus.cache import cache_info, clear_cache
from papyrus.cli import parse_document


class CacheTests(unittest.TestCase):
    def setUp(self):
        self._old_cache_dir = os.environ.get("PAPYRUS_CACHE_DIR")
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["PAPYRUS_CACHE_DIR"] = str(Path(self.tmp.name) / "cache")

    def tearDown(self):
        if self._old_cache_dir is None:
            os.environ.pop("PAPYRUS_CACHE_DIR", None)
        else:
            os.environ["PAPYRUS_CACHE_DIR"] = self._old_cache_dir
        self.tmp.cleanup()

    def test_parse_document_uses_content_cache(self):
        path = Path(self.tmp.name) / "sample.md"
        path.write_text("# Cached", encoding="utf-8")

        first = parse_document(str(path), output_format="json", use_cache=True)
        second = parse_document(str(path), output_format="json", use_cache=True)

        self.assertFalse(first["metadata"]["cache_hit"])
        self.assertTrue(second["metadata"]["cache_hit"])
        self.assertEqual(first["content"], second["content"])

    def test_cache_info_and_clear(self):
        path = Path(self.tmp.name) / "sample.md"
        path.write_text("# Cached", encoding="utf-8")
        parse_document(str(path), output_format="json", use_cache=True)

        before = cache_info()
        cleared = clear_cache()
        after = cache_info()

        self.assertEqual(before["entries"], 1)
        self.assertEqual(cleared["entries"], 1)
        self.assertEqual(after["entries"], 0)


if __name__ == "__main__":
    unittest.main()
