import re
import subprocess
from pathlib import Path

import attr

from bl_notebook.blender.ostype import OSType
from bl_notebook.util import (
    is_win32,
    make_executable_filename,
    normalize_path,
    print_error,
)

from .arch import Architecture
from .version import Version


def get_python_info(python):
    args = [
        python,
        "-c",
        "import sys, platform as p;"
        " print(p.machine()); print(p.system()); print(sys.executable)",
    ]
    try:
        output = subprocess.check_output(args)
    except OSError as exc:
        raise OSError(f"{python}: {exc}")
    return output.decode("utf-8").strip().replace("\r\n", "\n").split("\n")


def get_python_executable(python_bin_dir, ostype):
    if ostype == OSType.WINDOWS or (ostype == OSType.ANY and is_win32()):
        ext_re = r"\.exe$"
    else:
        ext_re = r"$"
    for entry in python_bin_dir.iterdir():
        if re.match(rf"^python([\d]+(\.[\d]+)*)?{ext_re}", entry.name):
            return entry
    raise FileNotFoundError(
        f"Can not find blender executable in directory {python_bin_dir}"
    )


@attr.define
class BlenderApp:
    path: str
    version: Version = attr.ib(converter=Version)
    arch: Architecture = attr.ib(converter=Architecture)
    ostype: OSType = attr.ib(converter=OSType)
    strict: bool = attr.ib(default=True)
    directory: Path = attr.ib(init=False)
    name: str = attr.ib(init=False)
    executable: Path = attr.ib(init=False)
    python_executable: Path = attr.ib(init=False)

    def __attrs_post_init__(self):
        if self.path is None or self.path == "":
            raise ValueError("Invalid path name")

        p = Path(normalize_path(self.path))
        self.directory = p.parent
        self.name = self.directory.name

        strict = self.strict
        if self.ostype == OSType.ANY or self.arch == Architecture.ANY:
            strict = True

        bindir = self.directory / self.version_major_minor / "python" / "bin"
        self.python_executable = get_python_executable(bindir, self.ostype)

        if strict:
            try:
                arch, ostype, python_executable = get_python_info(
                    self.python_executable
                )
            except OSError as exc:
                print_error(f"{self.directory}: {exc}")
            else:
                self.python_executable = python_executable
                try:
                    self.arch = arch
                    self.ostype = ostype
                except ValueError as exc:
                    raise RuntimeError(str(exc))

        self.executable = make_executable_filename(p, self.ostype)

    @property
    def version_major_minor(self):
        return ".".join(self.version.elements[:2])

    def check(self):
        if not self.executable.exists():
            raise FileNotFoundError(
                "Can not find blender executable: {}".format(self.executable)
            )
        if not self.executable.is_file():
            raise FileNotFoundError(f"Not a regular file: {self.executable}")

    def is_ok(self):
        try:
            self.check()
        except IOError:
            return False
        return True
