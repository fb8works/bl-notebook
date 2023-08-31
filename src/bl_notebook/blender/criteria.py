from typing import List, Optional

import attr

from bl_notebook.blender.arch import Architecture
from bl_notebook.blender.ostype import OSType


@attr.define
class Criteria:
    version: Optional[str] = attr.ib(default=None)
    architectures: List[Architecture] = attr.ib(factory=list)
    ostypes: List[OSType] = attr.ib(factory=list)
    ext_re: Optional[str] = attr.ib(default=None)

    def __str__(self) -> str:
        criteria = []
        if self.version is not None:
            criteria.append(f"Version={self.version}")
        if len(self.architectures) > 0:
            architectures = [x.name.lower() for x in self.architectures]
            criteria.append(f"Architectures={architectures!r}")
        if len(self.ostypes) > 0:
            ostypes = [x.name.lower() for x in self.ostypes]
            criteria.append(f"OSTypes={ostypes!r}")
        if self.ext_re is not None:
            criteria.append(f"Ext={self.ext_re!r}")
        if len(criteria):
            return ", ".join(criteria)
        else:
            return "Any"

    def is_empty(self):
        return (
            self.version is None
            and len(self.architectures) == 0
            and len(self.ostypes) == 0
            and self.ext_re is None
        )
