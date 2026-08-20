import subprocess
import sys
import unittest


class PackageSmokeTests(unittest.TestCase):
    def test_package_exports_version(self) -> None:
        import vgtree

        self.assertEqual(vgtree.__version__, "1.0.0")

    def test_module_help_is_available(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "vgtree", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("VGTREE", completed.stdout)


if __name__ == "__main__":
    unittest.main()
