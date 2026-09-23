import logging
import pathlib
import re
from typing import Any, Mapping

import click

from clover2_dev.app import App
from clover2_dev.discovery import CONFIG_DIR
from clover2_dev.plugins.version import commands
from clover2_dev.plugins.version.session import VersionSession
from clover2_dev.errors import ToolingError
from clover2_dev.plugins import PluginContext, load_module_from_path

logger = logging.getLogger(__name__)

DEFAULT_REFERENCE = "ros::clover2"


def _resolve_dir(app: App, plugin_config: Mapping[str, Any],
                 cli_dir: pathlib.Path | None) -> pathlib.Path:
    if cli_dir is not None:
        return cli_dir

    search_root = plugin_config.get("search_root", ".")
    base = app.root if app.root is not None else pathlib.Path.cwd()
    return base / search_root


def _load_extra_stores(root: pathlib.Path | None,
                       plugin_config: Mapping[str, Any]) -> None:
    if root is None:
        return

    store_paths = plugin_config.get("stores", [])
    if not isinstance(store_paths, list) or \
            not all(isinstance(p, str) for p in store_paths):
        raise ToolingError(
            "[plugins.version] stores must be a list of file paths")

    for rel_path in store_paths:
        module_path = (root / CONFIG_DIR / rel_path).resolve()
        if not module_path.is_file():
            raise ToolingError(
                f"Extra store module '{rel_path}' not found at {module_path}")

        load_module_from_path(module_path)
        logger.debug("Loaded extra store module: %s", module_path)


class VersionPlugin:
    name = "version"

    def create_commands(self, ctx: PluginContext) -> list[click.Command]:
        plugin_config = ctx.config

        @click.group(name="version", help="Project version management")
        @click.option("-d", "--dir", "dir_",
                      type=click.Path(path_type=pathlib.Path),
                      help="Dir for version stores search "
                           "(default: search_root from tooling.toml or project root)")
        @click.option("-f", "--filter", "filter_", default=".*",
                      show_default=True, help="Package name filter")
        @click.option("-e", "--exclude", "exclude_", multiple=True,
                      metavar="GLOB",
                      help="Directory glob to skip during the scan "
                           "(repeatable; extends exclude from tooling.toml)")
        @click.pass_context
        def group(ctx: click.Context, dir_: pathlib.Path | None,
                  filter_: str, exclude_: tuple[str, ...]) -> None:
            app: App = ctx.obj
            _load_extra_stores(app.root, plugin_config)
            configured = plugin_config.get("exclude", [])
            if not isinstance(configured, list) or \
                    not all(isinstance(g, str) for g in configured):
                raise ToolingError(
                    "[plugins.version] exclude must be a list of globs")

            ctx.obj = VersionSession(
                dir=_resolve_dir(app, plugin_config, dir_),
                filter=re.compile(filter_),
                exclude=(*configured, *exclude_),
                reference=plugin_config.get(
                    "reference", DEFAULT_REFERENCE),
            )

        group.add_command(commands.show.command)
        group.add_command(commands.update.command)
        group.add_command(commands.bump.command)
        group.add_command(commands.compose.command)

        return [group]


plugin = VersionPlugin()
