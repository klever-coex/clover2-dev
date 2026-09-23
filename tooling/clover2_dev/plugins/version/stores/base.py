import abc
import fnmatch
import logging
import os
import pathlib
import re
from collections.abc import Sequence

import semver

from clover2_dev.errors import StoreReadError, ToolingError

logger = logging.getLogger(__name__)

STORES: dict[str, type["VersionStore"]] = {}

SKIP_DIRS = {"node_modules", ".git", "build",
             "dist", ".venv", "venv", "install"}

REFERENCE_SEP = "::"


def _excluded(rel_dir: pathlib.Path, exclude: Sequence[str]) -> bool:
    rel_posix = rel_dir.as_posix()
    return (any(fnmatch.fnmatch(rel_posix, glob) for glob in exclude)
            or any(fnmatch.fnmatch(part, glob)
                   for glob in exclude for part in rel_posix.split("/")))


class VersionStore(abc.ABC):
    FILENAME: str = ""
    STORE_NAME: str = ""  # type token of the reference syntax: <STORE_NAME>::<name>

    def __init__(self, path: pathlib.Path):
        self.path = path

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        if not cls.FILENAME:
            return

        if cls.FILENAME in STORES:
            raise RuntimeError(f"Duplicate store filename '{cls.FILENAME}'")

        STORES[cls.FILENAME] = cls

    @property
    def store_name(self) -> str:
        return self.STORE_NAME

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def read(self) -> semver.Version: ...

    @abc.abstractmethod
    def write(self, version: semver.Version) -> None: ...

    @property
    def reference(self) -> str:
        return f"{self.STORE_NAME}{REFERENCE_SEP}{self.name}"

    def matches_reference(self, reference: str) -> bool:
        return self.reference == reference


def no_version(path: pathlib.Path) -> StoreReadError:
    return StoreReadError(f"No version field in {path}")


def bare(version: semver.Version) -> semver.Version:
    if version.prerelease is not None or version.build is not None:
        logger.warning(
            "Version %s carries a suffix; stores keep bare versions only", version)

    return version.finalize_version()


def create_store(path: pathlib.Path) -> VersionStore | None:
    store_cls = STORES.get(path.name)
    return store_cls(path) if store_cls else None


def discover_stores(base_path: pathlib.Path, name_filter: re.Pattern,
                    exclude: Sequence[str] = ()) -> list[VersionStore]:
    stores = []
    base = pathlib.Path(base_path)

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS
                   and not _excluded(pathlib.Path(root, d).relative_to(base),
                                     exclude)]
        for file in files:
            try:
                store = create_store(pathlib.Path(root) / file)
                if store is None or not name_filter.search(store.name):
                    continue
                version = store.read()
            except StoreReadError as exc:
                logger.debug("Skipping %s: %s", file, exc)
                continue

            logger.debug("Found store: %s of %s (%s)",
                         store.name, store.store_name, version)
            stores.append(store)

    return stores


def reference_store(stores: Sequence[VersionStore], reference: str) -> VersionStore:
    store_type, sep, name = reference.partition(REFERENCE_SEP)
    if not sep or not store_type or not name:
        raise ToolingError(
            f"Reference '{reference}' must be '<store-type>::<name>', "
            "e.g. ros::clover2")

    for store in stores:
        if store.store_name == store_type and store.name == name:
            return store

    available = ", ".join(s.reference for s in stores) or "none"
    raise ToolingError(
        f"Reference store '{reference}' not found; available: {available}")


def write_all(stores: Sequence[VersionStore], version: semver.Version) -> None:
    for store in stores:
        old = store.read()
        store.write(version)
        logger.info("Updated %s: %s -> %s", store.name, old, bare(version))
