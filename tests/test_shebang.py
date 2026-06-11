import tempfile
import unittest
from pathlib import Path

from papyrus.shebang import repair_shebangs


class ShebangRepairTests(unittest.TestCase):
    def test_rewrites_stale_python_shebangs(self):
        with tempfile.TemporaryDirectory() as tmp:
            venv = Path(tmp) / "venv"
            bin_dir = venv / "bin"
            bin_dir.mkdir(parents=True)
            python = bin_dir / "python"
            python.write_text("", encoding="utf-8")
            script = bin_dir / "papyrus"
            script.write_text(
                "#!/old/location/venv/bin/python3.13\nprint('ok')\n",
                encoding="utf-8",
            )

            result = repair_shebangs(venv)

            self.assertEqual(result["repaired"], 1)
            self.assertTrue(script.read_text(encoding="utf-8").startswith(f"#!{python.resolve()}"))


if __name__ == "__main__":
    unittest.main()
