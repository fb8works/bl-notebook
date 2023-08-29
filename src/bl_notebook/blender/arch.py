import enum
import re

RE_X64 = re.compile(r"(amd64|x86_64|x64)$", re.I)
RE_X32 = re.compile(r"(i[345]86|x86_32|x86|x32)$", re.I)


def get_architecture(machine):
    if RE_X64.match(machine):
        return "x86_64"
    if RE_X32.match(machine):
        return "x86"
    choice = [x.pattern for x in (RE_X64, RE_X32)]
    raise ValueError(f"{machine!r} must be ({choice!r})")


class Architecture(str, enum.Enum):
    X64 = "x86_64"
    X32 = "x86"
    ANY = "any"

    @classmethod
    def _missing_(cls, value):
        return cls(get_architecture(value))
