import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from papyrus.cli import cli


class CliTests(unittest.TestCase):
    def test_version_option(self):
        result = CliRunner().invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("papyrus, version", result.output)

    def test_python_module_defaults_to_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("module entrypoint", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "-m", "papyrus", str(path)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[1],
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("module entrypoint", result.stdout)

    def test_python_module_accepts_stdin(self):
        result = subprocess.run(
            [sys.executable, "-m", "papyrus", "-"],
            input="stdin content",
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stdin content", result.stdout)

    def test_cache_subcommand_help(self):
        result = CliRunner().invoke(cli, ["cache", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("info", result.output)
        self.assertIn("clear", result.output)

    def test_config_subcommand_help(self):
        result = CliRunner().invoke(cli, ["config", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("show", result.output)

    def test_repair_shebang_command_is_registered(self):
        result = CliRunner().invoke(cli, ["repair-shebang", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--venv", result.output)

    def test_batch_help_exposes_executor(self):
        result = CliRunner().invoke(cli, ["batch", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--executor", result.output)

    def test_parse_help_exposes_image_extraction(self):
        result = CliRunner().invoke(cli, ["parse", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--extract-images", result.output)
        self.assertIn("--image-dir", result.output)


if __name__ == "__main__":
    unittest.main()
