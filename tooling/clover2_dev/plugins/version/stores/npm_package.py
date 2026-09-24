import json
import pathlib
import re

import semver

from clover2_dev.errors import StoreReadError
from clover2_dev.plugins.version.stores.base import VersionStore, bare, no_version

VERSION_RE = re.compile(r'("version"\s*:\s*")([^"]*)(")')


class NpmPackageStore(VersionStore):
    FILENAME = "package.json"
    STORE_NAME: str = "npm"

    def __init__(self, path: pathlib.Path):
        super().__init__(path)
        try:
            self._data = json.loads(self.path.read_text())
        except json.JSONDecodeError as exc:
            raise StoreReadError(
                f"Invalid JSON in {self.path}: {exc}") from exc
        self._name = self._data.get("name", self.path.parent.name)

    @property
    def name(self) -> str:
        return self._name

    def read(self) -> semver.Version:
        raw = self._data.get("version")
        if raw is None:
            raise no_version(self.path)
        try:
            return semver.Version.parse(raw)
        except ValueError as exc:
            raise StoreReadError(
                f"Invalid version in {self.path}: {raw}") from exc

    def write(self, version: semver.Version) -> None:
        text = self.path.read_text()
        new_text, count = VERSION_RE.subn(
            rf"\g<1>{bare(version)}\g<3>", text, count=1)

        if count != 1:
            raise no_version(self.path)

        self.path.write_text(new_text)
