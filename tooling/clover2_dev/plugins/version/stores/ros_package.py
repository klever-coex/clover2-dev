import pathlib

import semver
from lxml import etree

from clover2_dev.errors import StoreReadError
from clover2_dev.plugins.version.stores.base import VersionStore, bare


class RosPackageStore(VersionStore):
    FILENAME = "package.xml"
    STORE_NAME: str = "ros"

    def __init__(self, path: pathlib.Path):
        super().__init__(path)
        try:
            parser = etree.XMLParser(remove_blank_text=False)
            self._tree = etree.parse(self.path, parser)
        except etree.LxmlError as exc:
            raise StoreReadError(f"Invalid XML in {self.path}: {exc}") from exc

        root = self._tree.getroot()
        self._name = root.findtext("name")
        self._version_el = root.find("version")
        if not self._name or self._version_el is None:
            raise StoreReadError(
                f"Missing <name> or <version> in {self.path}")

    @property
    def name(self) -> str:
        return self._name

    def read(self) -> semver.Version:
        try:
            return semver.Version.parse(self._version_el.text)
        except ValueError as exc:
            raise StoreReadError(
                f"Invalid version in {self.path}: {self._version_el.text}") from exc

    def write(self, version: semver.Version) -> None:
        self._version_el.text = str(bare(version))
        self._tree.write(self.path, encoding="utf-8",
                         xml_declaration=True, pretty_print=True)
