import pathlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VersionSession:
    dir: pathlib.Path
    filter: re.Pattern
    exclude: list[str]
    reference: str
