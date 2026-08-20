"""Build deterministic VGTREE plugin bundles and their checksum manifest."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "vgtree"
ZIP_TIME = (2020, 1, 1, 0, 0, 0)
ARCHIVE_EPOCH = 1_577_836_800
FILE_MODE = 0o100644


class BundleError(ValueError):
    """Raised when the release source tree is incomplete or unsafe."""


def tracked_plugin_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--", "plugins/vgtree"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise BundleError(f"cannot enumerate tracked plugin files: {detail}")
    paths: list[Path] = []
    root = PLUGIN_ROOT.resolve()
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(raw.decode("utf-8"))
        source_path = ROOT / relative
        if source_path.is_symlink():
            raise BundleError(f"plugin source cannot be a symlink: {relative}")
        path = source_path.resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise BundleError(f"plugin path escapes source root: {relative}") from exc
        if not path.is_file():
            raise BundleError(f"plugin source must be a regular tracked file: {relative}")
        paths.append(path)
    if not paths:
        raise BundleError("plugin source contains no tracked files")
    return sorted(paths, key=lambda path: path.relative_to(PLUGIN_ROOT).as_posix())


def archive_bytes(files: list[Path], *, allowed_prefixes: tuple[str, ...] | None = None) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for path in files:
            name = path.relative_to(PLUGIN_ROOT).as_posix()
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise BundleError(f"unsafe archive path: {name}")
            if allowed_prefixes is not None and not name.startswith(allowed_prefixes):
                continue
            info = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = FILE_MODE << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def one_artifact(dist: Path, pattern: str) -> Path:
    matches = sorted(dist.glob(pattern))
    if len(matches) != 1:
        raise BundleError(f"expected exactly one {pattern} artifact, found {len(matches)}")
    return matches[0]


def normalized_sdist_bytes(path: Path, version: str) -> bytes:
    source = io.BytesIO(path.read_bytes())
    entries: list[tuple[tarfile.TarInfo, bytes | None]] = []
    expected_root = f"vgtree-{version}"
    try:
        with tarfile.open(fileobj=source, mode="r:gz") as archive:
            for member in sorted(archive.getmembers(), key=lambda item: item.name):
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or ".." in pure.parts or not pure.parts:
                    raise BundleError(f"unsafe sdist path: {member.name}")
                if pure.parts[0] != expected_root:
                    raise BundleError(f"sdist path is outside {expected_root}: {member.name}")
                if not (member.isdir() or member.isfile()):
                    raise BundleError(f"sdist member must be a regular file or directory: {member.name}")
                data: bytes | None = None
                if member.isfile():
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        raise BundleError(f"cannot read sdist member: {member.name}")
                    data = extracted.read()
                entries.append((member, data))
    except tarfile.TarError as exc:
        raise BundleError(f"invalid sdist archive: {path.name}") from exc

    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for original, data in entries:
            info = tarfile.TarInfo(original.name)
            info.type = tarfile.DIRTYPE if original.isdir() else tarfile.REGTYPE
            info.mode = 0o755 if original.isdir() else 0o644
            info.mtime = ARCHIVE_EPOCH
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.size = 0 if data is None else len(data)
            info.pax_headers = {}
            archive.addfile(info, None if data is None else io.BytesIO(data))

    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=output,
        mtime=ARCHIVE_EPOCH,
    ) as compressed:
        compressed.write(tar_bytes.getvalue())
    return output.getvalue()


def normalized_wheel_bytes(path: Path) -> bytes:
    entries: list[tuple[str, bytes, bool]] = []
    names: set[str] = set()
    try:
        with zipfile.ZipFile(path, mode="r") as archive:
            for info in archive.infolist():
                pure = PurePosixPath(info.filename)
                if pure.is_absolute() or ".." in pure.parts or not pure.parts:
                    raise BundleError(f"unsafe wheel path: {info.filename}")
                if info.filename in names:
                    raise BundleError(f"duplicate wheel path: {info.filename}")
                names.add(info.filename)
                entries.append((info.filename, b"" if info.is_dir() else archive.read(info), info.is_dir()))
    except zipfile.BadZipFile as exc:
        raise BundleError(f"invalid wheel archive: {path.name}") from exc

    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for name, data, is_dir in sorted(entries, key=lambda item: item[0]):
            info = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o40755 if is_dir else FILE_MODE) << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def build(dist: Path, version: str) -> dict[str, str]:
    manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("version") != version:
        raise BundleError("requested version does not match plugin manifest")
    dist.mkdir(parents=True, exist_ok=True)
    wheel = one_artifact(dist, f"vgtree-{version}-*.whl")
    sdist = one_artifact(dist, f"vgtree-{version}.tar.gz")
    wheel.write_bytes(normalized_wheel_bytes(wheel))
    sdist.write_bytes(normalized_sdist_bytes(sdist, version))

    files = tracked_plugin_files()
    plugin = dist / f"vgtree-plugin-{version}.zip"
    skills = dist / f"vgtree-skills-{version}.zip"
    plugin.write_bytes(archive_bytes(files))
    skills.write_bytes(archive_bytes(files, allowed_prefixes=("skills/", "shared/")))

    payloads = sorted((wheel, sdist, plugin, skills), key=lambda path: path.name)
    digests = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in payloads}
    checksum_text = "".join(f"{digest}  {name}\n" for name, digest in digests.items())
    (dist / "SHA256SUMS").write_text(checksum_text, encoding="ascii", newline="\n")
    return digests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--version", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        digests = build(args.dist.resolve(), args.version)
    except (BundleError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"release bundle build failed: {exc}", file=sys.stderr)
        return 1
    json.dump({"artifacts": digests, "status": "PASS"}, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
