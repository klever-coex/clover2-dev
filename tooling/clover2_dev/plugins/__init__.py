import importlib.metadata
import importlib.util
import logging
import pathlib
import sys
import types
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

import click

from clover2_dev.app import App
from clover2_dev.discovery import CONFIG_DIR
from clover2_dev.errors import ToolingError

logger = logging.getLogger(__name__)

PLUGINS_DIR = "plugins"
ENTRY_POINT_GROUP = "clover2_dev.plugins"
CORE_COMMANDS = ("plugins",)


@dataclass(frozen=True)
class PluginContext:
    root: pathlib.Path | None
    config: Mapping[str, Any]
    logger: logging.Logger


@runtime_checkable
class Plugin(Protocol):
    name: str

    def create_commands(self, ctx: PluginContext) -> list[click.Command]: ...


@dataclass(frozen=True)
class PluginRecord:
    name: str
    source: str
    enabled: bool = True
    plugin: Plugin | None = None
    commands: tuple[click.Command, ...] = field(default=())


_MODULE_CACHE: dict[pathlib.Path, Any] = {}


def load_module_from_path(path: pathlib.Path) -> Any:
    canonical = path.resolve()
    cached = _MODULE_CACHE.get(canonical)
    if cached is not None:
        return cached

    module_name = f"clover2_dev_plugin_{len(_MODULE_CACHE)}_{path.stem}"
    kwargs = {"submodule_search_locations": [str(canonical.parent)]} \
        if path.stem == "__init__" else {}
    spec = importlib.util.spec_from_file_location(module_name, canonical, **kwargs)
    if spec is None or spec.loader is None:
        raise ToolingError(f"Cannot import plugin module {canonical}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise ToolingError(f"Failed to import plugin {canonical}: {exc}") from exc

    _MODULE_CACHE[canonical] = module
    return module


def _module_path(entry: pathlib.Path) -> pathlib.Path | None:
    if entry.name.startswith("_"):
        return None
    if entry.is_file() and entry.suffix == ".py":
        return entry
    if (entry / "__init__.py").is_file():
        return entry / "__init__.py"
    return None


def _extract_plugin(module: Any, source: str) -> Plugin:
    candidate = getattr(module, "plugin", None)
    if candidate is None:
        raise ToolingError(
            f"Plugin module {source} does not expose a module-level "
            "'plugin' attribute")

    return _coerce_plugin(candidate, source)


def _coerce_plugin(value: Any, source: str) -> Plugin:
    if isinstance(value, types.ModuleType):
        return _extract_plugin(value, source)

    plugin = value() if callable(value) else value
    if not isinstance(plugin, Plugin):
        raise ToolingError(
            f"Plugin from {source} does not satisfy the Plugin protocol "
            "(needs 'name' and 'create_commands(PluginContext)')")

    return plugin


def _load_installed_plugins(app: App) -> list[PluginRecord]:
    entries = sorted(
        importlib.metadata.entry_points(group=ENTRY_POINT_GROUP),
        key=lambda entry: entry.name)

    records = []
    for entry in entries:
        dist = getattr(getattr(entry, "dist", None), "name", None)
        source = f"installed:{dist or entry.name}"

        try:
            plugin = _coerce_plugin(entry.load(), source)
        except ToolingError:
            raise
        except Exception as exc:
            raise ToolingError(
                f"Failed to load installed plugin '{entry.name}' "
                f"({source}): {exc}") from exc

        enabled = app.config.plugin_enabled(plugin.name)
        records.append(PluginRecord(
            name=plugin.name,
            source=source,
            enabled=enabled,
            plugin=plugin if enabled else None,
        ))

    return records


def _load_local_plugins(app: App) -> list[PluginRecord]:
    if app.root is None:
        return []

    plugins_dir = app.root / CONFIG_DIR / PLUGINS_DIR
    if not plugins_dir.is_dir():
        return []

    records: list[PluginRecord] = []
    for entry in sorted(plugins_dir.iterdir()):
        module_path = _module_path(entry)
        if module_path is None:
            continue

        plugin_id = module_path.parent.name if module_path.stem == "__init__" \
            else module_path.stem
        enabled = app.config.plugin_enabled(plugin_id)
        if not enabled:
            records.append(PluginRecord(name=plugin_id, source=str(module_path),
                                        enabled=False))
            continue

        plugin = _extract_plugin(load_module_from_path(module_path), str(module_path))
        if plugin.name != plugin_id:
            raise ToolingError(
                f"Plugin {module_path} declares name '{plugin.name}' but its "
                f"id is '{plugin_id}'; keep the file name and plugin.name in sync")

        records.append(PluginRecord(name=plugin_id, source=str(module_path),
                                    plugin=plugin))

    return records


def load_plugins(app: App) -> list[PluginRecord]:
    records = _load_installed_plugins(app) + _load_local_plugins(app)

    seen_ids: dict[str, PluginRecord] = {}
    for record in records:
        if record.name in seen_ids:
            other = seen_ids[record.name]
            if record.enabled and other.enabled:
                raise ToolingError(
                    f"Duplicate plugin id '{record.name}' "
                    f"({other.source} and {record.source}); "
                    "disable one of them via [plugins.<id>] enabled = false")
            logger.warning("Duplicate plugin id '%s' (%s, %s); "
                           "one of them is disabled",
                           record.name, other.source, record.source)
            continue
        seen_ids[record.name] = record

    command_owners: dict[str, str] = {name: "(core)" for name in CORE_COMMANDS}
    built_records: list[PluginRecord] = []

    for record in records:
        if record.plugin is None:
            built_records.append(record)
            continue

        ctx = PluginContext(
            root=app.root,
            config=app.config.plugin_section(record.name),
            logger=logging.getLogger(f"clover2_dev.plugin.{record.name}"),
        )
        try:
            commands = record.plugin.create_commands(ctx)
        except Exception as exc:
            raise ToolingError(
                f"Plugin '{record.name}' ({record.source}) "
                f"failed to create commands: {exc}") from exc

        for command in commands:
            owner = command_owners.get(command.name)
            if owner is not None:
                raise ToolingError(
                    f"Command name collision: {owner} and plugin "
                    f"'{record.name}' both provide '{command.name}'")
            command_owners[command.name] = record.name

        built_records.append(PluginRecord(
            name=record.name, source=record.source, enabled=record.enabled,
            plugin=record.plugin, commands=tuple(commands)))

    return built_records
