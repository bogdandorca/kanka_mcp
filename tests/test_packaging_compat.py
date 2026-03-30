from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent


class PackagingCompatibilityTests(unittest.TestCase):
    def test_setup_py_reports_expected_project_name(self) -> None:
        result = subprocess.run(
            [sys.executable, "setup.py", "--name"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "kanka-mcp-server")

    def test_setup_py_reports_expected_project_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "setup.py", "--version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0.1.0")


if __name__ == "__main__":
    unittest.main()
