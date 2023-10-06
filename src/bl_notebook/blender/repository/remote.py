import os
import re
import shutil
import time
import zipfile
from contextlib import suppress
from functools import total_ordering
from pathlib import Path
from typing import List, Optional

import attr
import requests
from tqdm.auto import tqdm

from bl_notebook.blender.app import BlenderApp
from bl_notebook.blender.arch import Architecture
from bl_notebook.blender.filename import BlenderFileName
from bl_notebook.blender.ostype import OSType
from bl_notebook.blender.version import Version
from bl_notebook.util import (
    is_win32,
    make_executable_filename,
    normalize_path,
    print_error,
    run_command,
)


def download_file(url, filename):
    # make an HTTP request within a context manager
    delete = True
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()

            def progress(r):
                length = int(r.headers.get("Content-Length"))
                return tqdm.wrapattr(r.raw, "read", total=length, desc="")

            with progress(r) as stream, open(filename, "wb") as output:
                shutil.copyfileobj(stream, output)
                delete = False
    finally:
        if delete:
            with suppress(FileNotFoundError):
                os.unlink(filename)


@attr.define(order=False)
@total_ordering
class BlenderRemoteFile:
    href: str
    name: str
    version: Version = attr.ib(converter=Version)
    apps_root: Path
    download_dir: Path
    arch: Architecture
    ostype: OSType
    sort_key: List[float]

    def __attrs_post_init__(self):
        self.apps_root = normalize_path(self.apps_root)
        self.download_dir = normalize_path(self.download_dir)

    def __eq__(self, x):
        return self.sort_key == x.sort_key

    def __le__(self, x):
        return self.sort_key <= x.sort_key

    @property
    def archive_path(self):
        directory = Path(self.download_dir)
        return directory / self.name

    @property
    def blender_directory(self):
        s, n = re.subn(r"\.zip$", "", str(self.archive_path), 1, re.I)
        if n > 0:
            return self.archive_path.parent / s
        s, n = re.subn(r"\.tar.xz$", "", str(self.archive_path), 1, re.I)
        if n > 0:
            return self.archive_path.parent / s
        else:
            raise NotImplementedError(
                f"Not implemented to install file for {self.archive_path}"
            )

    @property
    def blender_executable(self):
        return make_executable_filename(
            self.blender_directory / "blender", self.ostype
        )

    def download(self, force=False):
        archive_path = self.archive_path
        if force or not archive_path.exists():
            print_error(f"Downloading {self.href}...")
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            download_file(self.href, archive_path)

    def _get_zipfile_members_without_root(self, archive):
        """zipfile を展開する為のメンバーを取得します

        Zip ファイルのルートにディレクトリが一つしか無い場合はディレクトリを
        パスから取り除きます。
        """

        def _get_root_dirname(info: zipfile.ZipInfo) -> bool:
            p = info.filename.split("/")
            n = len(p)
            if n > 2 or (n == 2 and p[1] == "") or (n == 1 and info.is_dir()):
                return p[0] + "/"
            return None

        def _remove_root(info: zipfile.ZipInfo, root_filename: str):
            assert root_filename[-1] == "/"
            if info.filename == root_filename:
                info.filename = "./"
                return True
            parts = info.filename.split(root_filename)
            if len(parts) > 1 and parts[1]:
                info.filename = root_filename.join(parts[1:])
                return True
            else:
                return False

        infolist = list(archive.infolist())

        try:
            root_filename = next(
                x for x in map(_get_root_dirname, infolist) if x is not None
            )
        except StopIteration:
            raise ValueError(
                f"{self.archive_path} does not contains directory"
            )

        members = []
        for x in infolist:
            if _remove_root(x, root_filename):
                members.append(x)
            else:
                raise ValueError(f"{self.archive_path} contains multiple root")

        return members

    def install(self, force=False, verbose=False, dry_run=False):
        directory = self.blender_directory
        if force:
            if directory.exists():
                shutil.rmtree(directory)
        else:
            if directory.exists():
                return directory
        if re.search(r"\.zip$", str(self.archive_path), re.I):
            with zipfile.ZipFile(self.archive_path, "r") as archive:
                try:
                    members = self._get_zipfile_members_without_root(archive)
                except ValueError as exc:
                    print_error(f"warning: {exc}")
                    members = None
                if verbose:
                    print_error(
                        f"Extracting {self.archive_path} into {directory}"
                    )
                archive.extractall(path=directory, members=members)
                return directory
        if re.search(r"\.tar.xz$", str(self.archive_path), re.I):
            # tar xaf FILENAME -C DIRECTORY --strip-components=1
            directory.mkdir(parents=True, exist_ok=True)
            if verbose:
                print_error(f"Extracting {self.archive_path} into {directory}")
            try:
                if is_win32():
                    args = [
                        "wsl",
                        "--exec",
                        "bash",
                        "-c",
                        f'tar -xaf $(wslpath "{str(self.archive_path)}")'
                        f' -C $(wslpath "{str(directory)}")'
                        " --strip-components=1",
                    ]
                else:
                    args = [
                        "tar",
                        "-xaf",
                        str(self.archive_path),
                        "-C",
                        str(directory),
                        "--strip-components=1",
                    ]
                run_command(args, verbose=verbose, dry_run=dry_run)
            finally:
                with suppress(OSError):
                    # Delete directory if directory is empty
                    directory.rmdir()
        else:
            raise NotImplementedError(
                f"Not implemented to extract file for {self.archive_path}"
            )


@attr.define
class BlenderRemoteVersionFolder:
    version_url: str  # eg. 'https://download.blender.org/release/Blender3.5/'
    name: str
    apps_root: Path
    download_dir: Path = attr.ib()
    version: str = attr.ib(init=False, converter=Version)

    def __attrs_post_init__(self):
        version, n = re.subn(r"^blender(\d.*)", r"\1", self.name, 1, re.I)
        if n == 0:
            raise ValueError(
                'The value of "name" argument must starts '
                'with "blender": ' + self.name
            )
        self.version = version

    @download_dir.default
    def _default_cache_root(self):
        return self.apps_root

    @classmethod
    def _is_match_architecture(cls, arch, architectures):
        return any((a == Architecture.ANY or a == arch for a in architectures))

    @classmethod
    def _is_match_ostype(cls, ostype, ostypes):
        return any((o == OSType.ANY or o == ostype for o in ostypes))

    @property
    def folder_version(self) -> str:
        m = re.match(r"^Blender(\d+\.\d+.*)", self.name, re.I)
        if m:
            return m.group(1)
        raise ValueError(f"Not a bolder remote folder: {self.name}")

    def find_all(self, version, architectures, ostypes, ext_re):
        if version is not None:
            version = Version(version)

        r = requests.get(self.version_url, allow_redirects=False)

        pattern = re.compile(
            r'<a\s+href\s*=\s*"(blender[-_ ]?([^\"]+))"[^>]*>\s*([^<\s]+)',
            re.I,
        )

        result = []

        for line in r.text.split("\n"):
            m = pattern.search(line)
            if m:
                href = m.group(1)
                ver = m.group(2)
                name = m.group(3)

                if not re.search(ext_re, name):
                    continue

                bl_filename = BlenderFileName(name)

                def get_sort_key(arr, value):
                    try:
                        return len(arr) - arr.index(value)
                    except ValueError:
                        return float("-inf")

                arch_sortkey = get_sort_key(architectures, bl_filename.arch)
                ostype_sortkey = get_sort_key(ostypes, bl_filename.ostype)

                if arch_sortkey >= 0 and ostype_sortkey >= 0:
                    try:
                        v = Version(ver)
                    except ValueError:
                        continue

                    if version is not None and v not in version:
                        continue

                    result.append(
                        BlenderRemoteFile(
                            self.version_url + href,
                            name,
                            version=ver,
                            apps_root=self.apps_root,
                            download_dir=self.download_dir,
                            arch=bl_filename.arch,
                            ostype=bl_filename.ostype,
                            sort_key=[
                                ostype_sortkey,
                                arch_sortkey,
                                v.elements,
                            ],
                        )
                    )

        return sorted(result)

    def find(self, version, architectures, ostypes, ext_re):
        result = self.find_all(version, architectures, ostypes, ext_re)
        if len(result) == 0:
            raise FileNotFoundError("No match blender file on remote")

        return result[-1]


class BlenderRemoteRepository:
    URL_BASE = "https://download.blender.org/release/"
    CACHE_EXPIRE = 3600 * 24

    def __init__(self, url, apps_root, cache_dir, ext_re, cache_expire=None):
        """
        Create blender remote repository class instance

        Parameters
        ----------
        url : str
            公式またはミラーダウンロード URL
        apps_root : str
            ダウンロードおよびインストール先のディレクトリ
        cache_dir : str
            キャッシュディレクトリ
        ext_re : str
            zip 拡張子の正規表現
        cache_expire : Optional[float]
            HTML キャッシュ有効期限
        """
        if cache_expire is None:
            cache_expire = self.CACHE_EXPIRE

        self.url_base = url or self.URL_BASE
        self._versions = None
        self.ext_re = ext_re
        self.apps_root = Path(normalize_path(apps_root))
        self.cache_dir = Path(normalize_path(cache_dir))
        self.cache_expire = self.CACHE_EXPIRE

    @property
    def versions(self) -> List[BlenderApp]:
        return self._get_versions()

    def _get_versions(self, cache=True) -> List[BlenderApp]:
        if cache and self._versions:
            return self._versions

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_filename = self.cache_dir / "release_index.html"
        cache_expire = float("-inf")

        if cache_filename.exists():
            cache_expire = cache_filename.stat().st_mtime + self.CACHE_EXPIRE

        if cache and time.time() < cache_expire:
            with open(cache_filename, "r") as fh:
                html = fh.read()
        else:
            r = requests.get(self.url_base, allow_redirects=False)
            html = r.text
            with open(cache_filename, "w") as fh:
                fh.write(r.text)

        arr = []

        # parse HTML
        for line in html.split("\n"):
            m = re.search(
                r'<a\s+href\s*=\s*"(blender(\d[^"]+))"[^>]*>([^<]+)<',
                line,
                re.I,
            )  # " this double quote avoids syntax bug for emacs
            if m:
                name = m.group(3).rstrip("/")
                url = self.url_base + m.group(1)
                arr.append(
                    BlenderRemoteVersionFolder(
                        url, name, apps_root=self.apps_root
                    )
                )

        # sort as latest version first
        arr = sorted(arr, key=lambda x: x.version, reverse=True)
        self._versions = list(arr)

        return self._versions

    def _get_version(self, version) -> List[BlenderApp]:
        version = Version(version)
        last_matched = None
        for folder in self.versions:
            if folder.version in version:
                return folder
        return last_matched

    def find_version(self, version=None) -> Optional[BlenderApp]:
        if version is None:
            return self.versions[0]  # latest version
        return self._get_version(version)
