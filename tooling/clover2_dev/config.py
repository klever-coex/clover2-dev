import logging
import pathlib
import tomllib
from dataclasses import dataclass
from typing import Any, Mapping

from clover2_dev.errors import ToolingError

logger = logging.getLogger(__name__)

KNOWN_TOP_LEVEL_KEYS = {"project", "plugins"}


@dataclass(frozen=True)
class ToolingConfig:

    path: pathlib.Path | None
    project_name: str
    data: Mapping[str, Any]

    @classmethod
    def empty(cls) -> "ToolingConfig":
        return cls(path=None, project_name="", data={})

    @classmethod
    def load(cls, path: pathlib.Path) -> "ToolingConfig":
        try:
            data = tomllib.loads(path.read_text())
        except tomllib.TOMLDecodeError as exc:
            raise ToolingError(f"{path}: invalid TOML: {exc}") from exc
        except OSError as exc:
            raise ToolingError(f"{path}: cannot read config: {exc}") from exc

        for key in data:
            if key not in KNOWN_TOP_LEVEL_KEYS:
                logger.warning(
                    "%s: unknown top-level key '%s' ignored", path, key)

        project = _table(data, "project", path)
        if not isinstance(project.get("name", ""), str):
            raise ToolingError(f"{path}: project.name must be a string")

        plugins = _table(data, "plugins", path)
        for plugin_id, section in plugins.items():
            if not isinstance(section, dict):
                raise ToolingError(
                    f"{path}: [plugins.{plugin_id}] must be a table")

            _check_enabled(path, plugin_id, section)

        return cls(
            path=path,
            project_name=project.get("name", ""),
            data=data,
        )

    def plugin_section(self, plugin_id: str) -> Mapping[str, Any]:
        section = self.data.get("plugins", {}).get(plugin_id, {})
        return section if isinstance(section, dict) else {}

    def plugin_enabled(self, plugin_id: str) -> bool:
        return _check_enabled(self.path, plugin_id, self.plugin_section(plugin_id))


def _table(data: Mapping[str, Any], key: str, path: pathlib.Path) -> dict[str, Any]:
    value = data.get(key, {})

    if not isinstance(value, dict):
        raise ToolingError(f"{path}: '{key}' must be a table")

    return value


def _check_enabled(path: pathlib.Path | None, plugin_id: str,
                   section: Mapping[str, Any]) -> bool:
    enabled = section.get("enabled", True)

    if not isinstance(enabled, bool):
        where = f"{path}: " if path else ""
        raise ToolingError(
            f"{where}[plugins.{plugin_id}] enabled must be a boolean")

    return enabled
