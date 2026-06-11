import tempfile
import unittest
import zipfile
from base64 import b64decode
from pathlib import Path

from papyrus.images import append_image_section, extract_images


PNG_BYTES = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class ImageExtractionTests(unittest.TestCase):
    def test_pptx_media_files_are_extracted_from_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pptx = tmp_path / "slides.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/media/image1.png", PNG_BYTES)
                archive.writestr("ppt/slides/slide1.xml", "<xml/>")

            images = extract_images(str(pptx), tmp_path / "images", reference_dir=tmp_path)

            self.assertEqual(len(images), 1)
            self.assertEqual(images[0]["source"], "ppt/media/image1.png")
            self.assertTrue(Path(images[0]["path"]).exists())
            self.assertEqual(images[0]["relative_path"], "images/image-0001-image1.png")

    def test_pdf_images_are_extracted_with_page_metadata(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF is not installed")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pdf = tmp_path / "image.pdf"
            doc = fitz.open()
            page = doc.new_page(width=50, height=50)
            page.insert_image(fitz.Rect(0, 0, 10, 10), stream=PNG_BYTES)
            doc.save(pdf)
            doc.close()

            images = extract_images(str(pdf), tmp_path / "images", reference_dir=tmp_path)

            self.assertEqual(len(images), 1)
            self.assertEqual(images[0]["page"], 1)
            self.assertTrue(Path(images[0]["path"]).exists())
            self.assertTrue(images[0]["relative_path"].startswith("images/page-0001-image-001"))

    def test_markdown_image_section_uses_relative_paths(self):
        content = append_image_section(
            "# Content\n",
            [{"index": 1, "relative_path": "assets/image.png", "source": "ppt/media/image.png"}],
        )

        self.assertIn("# Extracted Images", content)
        self.assertIn("![Image 1 from ppt/media/image.png](assets/image.png)", content)


if __name__ == "__main__":
    unittest.main()
