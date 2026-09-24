import pathlib

import semver
import tomlkit
from tomlkit.exceptions import TOMLKitError

from clover2_dev.errors import StoreReadError
from clover2_dev.plugins.version.stores.base import VersionStore, bare, no_version

PROJECT_SECTION = "project"
POETRY_SECTION = "tool.poetry"


class PyProjectStore(VersionStore):

    FILENAME = "pyproject.toml"
    STORE_NAME: str = "pyproject"

    def __init__(self, path: pathlib.Path):
        super().__init__(path)
        try:
            self._doc = tomlkit.parse(path.read_text())
        except TOMLKitError as exc:
            raise StoreReadError(
                f"Invalid TOML in {self.path}: {exc}") from exc

    @property
    def _version_container(self):
        project = self._doc.get(PROJECT_SECTION)
        if isinstance(project, dict) and "version" in project:
            return self._doc[PROJECT_SECTION]

        poetry = self._doc.get("tool", {}).get("poetry")
        if isinstance(poetry, dict) and "version" in poetry:
            return self._doc["tool"]["poetry"]

        raise no_version(self.path)

    @property
    def name(self) -> str:
        project = self._doc.get(PROJECT_SECTION, {})
        poetry = self._doc.get("tool", {}).get("poetry", {})
        return project.get("name") or poetry.get("name") or self.path.parent.name

    def read(self) -> semver.Version:
        raw = str(self._version_container["version"])
        try:
            return semver.Version.parse(raw)
        except ValueError as exc:
            raise StoreReadError(
                f"Invalid version in {self.path}: {raw}") from exc

    def write(self, version: semver.Version) -> None:
        container = self._version_container
        container["version"] = str(bare(version))
        self.path.write_text(tomlkit.dumps(self._doc))
