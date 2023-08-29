import glob
import re
from pathlib import Path
from typing import List, Optional

from bl_notebook.blender.app import BlenderApp
from bl_notebook.blender.filename import BlenderFileName
from bl_notebook.blender.version import Version
from bl_notebook.util import normalize_path


class BlenderLocalRepository:
    def __init__(self, search_path, strict=True):
        self.search_path = search_path
        self.strict = strict
        self._versions = None

    @property
    def versions(self) -> List[BlenderApp]:
        return self._get_versions()

    def _get_versions(self) -> List[BlenderApp]:
        if self._versions is None:
            search_path = self.search_path.split(";")
            arr = []
            for appdir in (x.strip() for x in search_path if x != ""):
                # TODO appdir == 'REGISTRY'
                for ent in glob.glob(str(Path(normalize_path(appdir)) / "*")):
                    path = Path(ent)
                    if not path.is_dir():
                        continue
                    name = path.name
                    m = re.match(r"blender[-_ ]*(.*)", name, re.I)
                    # TODO remove '-windows-x64'?
                    if m:
                        version = m.group(1)  # eg. '2.56a-beta-windows64'
                        executable = path / "blender"
                        bl_fileame = BlenderFileName(path)
                        try:
                            app = BlenderApp(
                                executable,
                                version,
                                arch=bl_fileame.arch,
                                ostype=bl_fileame.ostype,
                                strict=self.strict,
                            )
                        except ValueError:
                            pass
                        else:
                            arr.append(app)
            self._versions = sorted(arr, key=lambda x: x.version)

        return self._versions

    def find_all(self, version, architectures, ostypes) -> List[BlenderApp]:
        result = []

        for blender in reversed(self.versions):  # Latest version first
            if (
                (version is None or blender.version in Version(version))
                and blender.arch in architectures
                and blender.ostype in ostypes
            ):
                result.append(blender)

        return list(reversed(result))

    def find(self, version, architectures, ostypes) -> Optional[BlenderApp]:
        versions = self.find_all(version, architectures, ostypes)
        try:
            return versions[-1]
        except IndexError:
            return None
