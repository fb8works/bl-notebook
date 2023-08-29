import enum

OSTYPE_ALIASES = {
    "win": "Windows",
    "windows": "Windows",
    "mac": "Darwin",
    "macos": "Darwin",
    "darwin": "Darwin",
    "linux": "Linux",
    "unix": "Linux",
    "posix": "Linux",
    "any": "any",
}

EXT_RE_MAP = {}


class OSType(str, enum.Enum):
    WINDOWS = "Windows"
    MAC = "Darwin"
    LINUX = "Linux"
    ANY = "any"

    @property
    def ext_re(self):
        return EXT_RE_MAP[self]

    @classmethod
    def _missing_(cls, value):
        name = OSTYPE_ALIASES.get(value.lower())
        if name is not None:
            return cls(name)
        choice = "windows|win|mac|macos|darwin|linux|unix|posix|any"
        raise ValueError(f"{value!r} must be ({choice})")


EXT_RE_MAP = {
    OSType.WINDOWS: r"\.zip$",
    OSType.MAC: r"\.dmg$",
    OSType.LINUX: r"\.tar\.xz$",
    OSType.ANY: r"",
}
