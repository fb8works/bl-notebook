import re

from .arch import Architecture
from .ostype import OSType


class BlenderFileName(str):
    @property
    def arch(self):
        if re.search(r"(^|[^\d])64([^\d]|$)", self):
            return Architecture.X64
        elif re.search(r"(^|[^\d])32([^\d]|$)", self):
            return Architecture.X32
        return Architecture.ANY

    @property
    def ostype(self):
        if re.search(r"(^|\b|\d)(win(dows)?)(\b|\d|$)", self):
            return OSType.WINDOWS
        elif re.search(r"(^|\b|\d)(mac([-_ ]?os)?)(\b|\d|$)", self):
            return OSType.MAC
        elif re.search(r"(^|\b|\d)(linux([-_ ]?os)?)(\b|\d|$)", self):
            return OSType.LINUX
        return OSType.ANY
