import logging
import os
import pathlib

from clover2_dev.errors import ToolingError

logger = logging.getLogger(__name__)

CONFIG_DIR = "tooling"
CONFIG_FILE = "tooling.toml"
ROOT_ENV = "CLOVER2_DEV_ROOT"


def config_path(root: pathlib.Path) -> pathlib.Path:
    return root / CONFIG_DIR / CONFIG_FILE


def is_project(directory: pathlib.Path) -> bool:
    return config_path(directory).is_file()


def resolve_root(explicit: pathlib.Path | None = None) -> pathlib.Path | None:
    for source, value in (("--root", explicit),
                          ("env " + ROOT_ENV, os.environ.get(ROOT_ENV))):
        if value is None:
            continue

        candidate = pathlib.Path(value).expanduser().resolve()
        if not is_project(candidate):
            raise ToolingError(
                f"{source} points to '{candidate}' which has no "
                f"{CONFIG_DIR}/{CONFIG_FILE}")

        return candidate

    cwd = pathlib.Path.cwd()
    return cwd if is_project(cwd) else None
