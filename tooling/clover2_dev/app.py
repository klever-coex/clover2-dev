import pathlib
from dataclasses import dataclass

from clover2_dev.config import ToolingConfig


@dataclass(frozen=True)
class App:
    root: pathlib.Path | None
    config: ToolingConfig
