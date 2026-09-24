import pathlib
import re

import semver

from clover2_dev.errors import StoreReadError
from clover2_dev.plugins.version.stores.base import VersionStore, bare, no_version

VERSION_RE = re.compile(
    r'^(version\s*:\s*)(["\']?)([^\s"\'#]+)\2(\s*(?:#.*)?)$', re.MULTILINE)
NAME_RE = re.compile(
    r'^name\s*:\s*(["\']?)([^\s"\'#]+)\1(\s*(?:#.*)?)$', re.MULTILINE)


class GalaxyStore(VersionStore):

    FILENAME = "galaxy.yml"
    STORE_NAME: str = "galaxy"

    def __init__(self, path: pathlib.Path):
        super().__init__(path)
        self._text = path.read_text()

    @property
    def name(self) -> str:
        match = NAME_RE.search(self._text)
        return match.group(2) if match else self.path.parent.name

    def read(self) -> semver.Version:
        match = VERSION_RE.search(self._text)
        if not match:
            raise no_version(self.path)
        try:
            return semver.Version.parse(match.group(3))
        except ValueError as exc:
            raise StoreReadError(
                f"Invalid version in {self.path}: {match.group(3)}") from exc

    def write(self, version: semver.Version) -> None:
        def replace(match: re.Match) -> str:
            return (match.group(1) + match.group(2)
                    + str(bare(version)) + match.group(2) + match.group(4))

        new_text, count = VERSION_RE.subn(replace, self._text, count=1)
        if count != 1:
            raise no_version(self.path)

        self.path.write_text(new_text)
