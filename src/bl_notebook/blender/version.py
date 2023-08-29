import functools
import re
from typing import Union


@functools.total_ordering
class Version:
    BAD_VERSION_ELEMENT_RE = re.compile(r"^-\d")
    NUMBER_SORT_KEY_FORMAT = "{:08d}"

    def __init__(self, version: Union[str, "Version"]):
        if not isinstance(version, (str, Version)):
            raise ValueError(
                "version must be str or Version"
                f", not {type(version).__name__}"
            )

        version = str(version)
        version = version.strip(". ")
        self.original = version

        if not re.match(r"[0-9]", version):
            raise ValueError(f"Malformed version string {self.original!r}")

        def normalize(i, x):
            """Normalize version element"""
            if self.BAD_VERSION_ELEMENT_RE.match(x):
                raise ValueError(
                    f"Malformed version string {x!r}"
                    f" (matches {self.BAD_VERSION_ELEMENT_RE!r})"
                )
            x = re.sub(r"^0+([^0])", r"\1", x)
            x = re.sub(r"^(-+)", "", x)
            return x

        def sortable(x):
            """Make sortable key"""
            m = re.match(r"(\d+)(.*)", x)
            if m:
                numbers = self.NUMBER_SORT_KEY_FORMAT.format(int(m.group(1)))
                return numbers + m.group(2)
            return x

        # Special case "https://download.blender.org/release/Blender2.56abeta/"
        # eg. '2.56abeta' -> '2.56a-beta'
        version = re.sub(r"([a-zA-Z])(alpha|beta)", r"\1-\2", version)

        # Remove archive suffixes
        version = re.sub(r"(\.tar|((\.tar)?\.(gz|xz|zip)))$", "", version)

        # '2.56a-beta' -> ['2', '56a-beta']
        elements = version.split(".")
        elements = tuple((normalize(*x) for x in enumerate(elements)))
        self.version = ".".join(filter(len, elements))

        # '2.56a-beta' -> ['2', '56', 'a', 'beta']
        version = re.sub(r"([^.\D])([^.\d])", r"\1.\2", version)
        version = re.sub(r"([^.\d])([^.\D])", r"\1.\2", version)
        elements = re.split(r"[-.]", version)

        self.elements = elements
        self._sort_key = tuple(map(sortable, self.elements))

    def __str__(self):
        return self.version

    def __repr__(self):
        return f"Version({self.elements!r})"

    def __contains__(self, version):
        # b:self  a:version  Result
        # 3.4.1   3.4        True
        # 3.4     3.4.1      False
        a = Version(version)._sort_key
        b = self._sort_key
        if len(a) > len(b):
            a = a[: len(b)]
        return a == b

    def __eq__(self, version):
        return Version(version)._sort_key == self._sort_key

    def __lt__(self, version):
        return self._sort_key < Version(version)._sort_key
