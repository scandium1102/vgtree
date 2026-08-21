from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.1.0"
FIXED_ZIP_TIME = (2020, 1, 1, 0, 0, 0)
FIXED_EPOCH = 1_577_836_800


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseBundleTests(unittest.TestCase):
    def build(self, dist: Path) -> subprocess.CompletedProcess[str]:
        with zipfile.ZipFile(dist / f"vgtree-{VERSION}-py3-none-any.whl", "w") as archive:
            archive.writestr(
                f"vgtree-{VERSION}.dist-info/WHEEL",
                "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            )
        with tarfile.open(dist / f"vgtree-{VERSION}.tar.gz", "w:gz") as archive:
            data = b"Metadata-Version: 2.5\nName: vgtree\nVersion: 1.1.0\n"
            info = tarfile.TarInfo(f"vgtree-{VERSION}/PKG-INFO")
            info.size = len(data)
            info.mtime = time.time()
            info.uid = 1000
            info.gid = 1000
            info.uname = "builder"
            info.gname = "builder"
            archive.addfile(info, io.BytesIO(data))
        return subprocess.run(
            [
                sys.executable,
                "scripts/build_release_bundles.py",
                "--dist",
                str(dist),
                "--version",
                VERSION,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_builds_exact_deterministic_release_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            completed = self.build(dist)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

            expected = {
                f"vgtree-{VERSION}-py3-none-any.whl",
                f"vgtree-{VERSION}.tar.gz",
                f"vgtree-plugin-{VERSION}.zip",
                f"vgtree-skills-{VERSION}.zip",
                "SHA256SUMS",
            }
            self.assertEqual(expected, {path.name for path in dist.iterdir()})
            first = {
                path.name: sha256(path)
                for path in dist.iterdir()
                if path.name != "SHA256SUMS"
            }
            completed = self.build(dist)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            second = {
                path.name: sha256(path)
                for path in dist.iterdir()
                if path.name != "SHA256SUMS"
            }
            self.assertEqual(first, second)

    def test_normalizes_wheel_archive_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            completed = self.build(dist)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

            with zipfile.ZipFile(dist / f"vgtree-{VERSION}-py3-none-any.whl") as archive:
                self.assertEqual(sorted(archive.namelist()), archive.namelist())
                self.assertTrue(all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist()))
                self.assertTrue(all(info.external_attr >> 16 == 0o100644 for info in archive.infolist()))

    def test_normalizes_sdist_archive_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            completed = self.build(dist)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

            with tarfile.open(dist / f"vgtree-{VERSION}.tar.gz", "r:gz") as archive:
                members = archive.getmembers()
                self.assertEqual([f"vgtree-{VERSION}/PKG-INFO"], [item.name for item in members])
                self.assertTrue(all(item.mtime == FIXED_EPOCH for item in members))
                self.assertTrue(all(item.uid == 0 and item.gid == 0 for item in members))
                self.assertTrue(all(not item.uname and not item.gname for item in members))
                self.assertTrue(all(item.mode == 0o644 for item in members))

    def test_plugin_and_skills_archives_have_safe_complete_layouts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            completed = self.build(dist)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

            plugin_path = dist / f"vgtree-plugin-{VERSION}.zip"
            skills_path = dist / f"vgtree-skills-{VERSION}.zip"
            with zipfile.ZipFile(plugin_path) as archive:
                names = archive.namelist()
                self.assertIn(".codex-plugin/plugin.json", names)
                self.assertEqual(6, len([name for name in names if name.endswith("/SKILL.md")]))
                self.assertTrue(any(name.startswith("shared/schemas/") for name in names))
                self.assertTrue(any(name.startswith("shared/templates/") for name in names))
                self.assertTrue(any(name.startswith("shared/references/") for name in names))
                manifest = json.loads(archive.read(".codex-plugin/plugin.json"))
                self.assertEqual(VERSION, manifest["version"])
                self.assertEqual(names, sorted(names))
                self.assertTrue(all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist()))
                for info in archive.infolist():
                    path = PurePosixPath(info.filename)
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn("..", path.parts)
                    self.assertEqual(0o100644, info.external_attr >> 16)

            with zipfile.ZipFile(skills_path) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertNotIn(".codex-plugin/plugin.json", names)
                self.assertTrue(all(name.startswith(("skills/", "shared/")) for name in names))
                self.assertEqual(6, len([name for name in names if name.endswith("/SKILL.md")]))

    def test_checksum_manifest_binds_exact_four_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            completed = self.build(dist)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

            lines = (dist / "SHA256SUMS").read_text(encoding="ascii").splitlines()
            self.assertEqual(4, len(lines))
            names = []
            for line in lines:
                digest, name = line.split("  ", 1)
                names.append(name)
                self.assertEqual(64, len(digest))
                self.assertEqual(digest, sha256(dist / name))
            self.assertEqual(names, sorted(names))


if __name__ == "__main__":
    unittest.main()
