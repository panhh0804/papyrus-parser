import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from papyrus.progress import show_document_progress


class ProgressTests(unittest.TestCase):
    def test_pptx_progress_probe_counts_slides_without_parsing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "slides.pptx"
            with ZipFile(path, "w") as zf:
                zf.writestr("[Content_Types].xml", "<Types/>")
                zf.writestr("ppt/slides/slide1.xml", "<slide/>")
                zf.writestr("ppt/slides/slide2.xml", "<slide/>")

            with patch("papyrus.progress.click.echo") as echo:
                with patch("papyrus.progress.click.progressbar", side_effect=lambda items, **kwargs: items):
                    show_document_progress(str(path), file_type="pptx")

            echo.assert_called()


if __name__ == "__main__":
    unittest.main()
