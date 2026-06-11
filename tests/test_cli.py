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


if __name__ == "__main__":
    unittest.main()
