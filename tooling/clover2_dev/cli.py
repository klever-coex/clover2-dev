import argparse
import logging
import pathlib
import sys

import click

import clover2_dev
from clover2_dev.app import App
from clover2_dev.commands.plugins_cmd import make_plugins_group
from clover2_dev.config import ToolingConfig
from clover2_dev.discovery import config_path, resolve_root
from clover2_dev.errors import ToolingError
from clover2_dev.plugins import load_plugins

logger = logging.getLogger(__name__)


class ToolingGroup(click.Group):
    def main(self, *args, **kwargs):
        try:
            return super().main(*args, **kwargs)
        except ToolingError as exc:
            click.echo(f"Error: {exc}", err=True)
            raise SystemExit(1) from exc


def setup_logging(verbose: int) -> None:
    if verbose >= 3:
        level = logging.DEBUG
    elif verbose == 2:
        level = logging.INFO
    elif verbose == 1:
        level = logging.WARNING
    else:
        level = logging.ERROR

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(asctime)s: %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _prescan() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("--root", type=pathlib.Path, default=None)

    pre: list[str] = []
    tokens = sys.argv[1:]
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            break
        if token == "--root":
            pre.extend(tokens[i:i + 2])
            i += 2
            continue
        if not token.startswith("-"):
            break
        pre.append(token)
        i += 1

    opts, _ = parser.parse_known_args(pre)
    return opts


def build_cli(app: App) -> click.Group:
    @click.group(name="clover2-dev", cls=ToolingGroup,
                 context_settings={"obj": app})
    @click.version_option(clover2_dev.__version__, prog_name="clover2-dev")
    @click.option("-v", "--verbose", count=True,
                  help="Increase output verbosity")
    @click.option("--root", type=click.Path(file_okay=False, path_type=pathlib.Path),
                  help="Project root override (default: the launch directory, "
                       "which must contain tooling/tooling.toml)")
    def cli(verbose: int, root: pathlib.Path | None) -> None:
        pass

    records = load_plugins(app)
    cli.add_command(make_plugins_group(app, records))
    for record in records:
        for command in record.commands:
            cli.add_command(command)

    return cli


def main() -> None:
    opts = _prescan()
    setup_logging(opts.verbose)

    if any(t in ("-h", "--help", "--version") for t in sys.argv[1:]):
        build_cli(App(root=None, config=ToolingConfig.empty()))()
        return

    try:
        root = resolve_root(opts.root)
        if root is None:
            click.echo("warning: no tooling/tooling.toml found; "
                       "only installed plugins are available", err=True)
            config = ToolingConfig.empty()
        else:
            config = ToolingConfig.load(config_path(root))

        cli = build_cli(App(root=root, config=config))
        cli()
    except ToolingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
