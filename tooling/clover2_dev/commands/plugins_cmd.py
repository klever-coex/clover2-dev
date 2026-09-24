import click

from clover2_dev.app import App
from clover2_dev.plugins import PluginRecord


def _list(app: App, records: list[PluginRecord]) -> None:
    header = app.config.project_name or (
        app.root.name if app.root is not None else "no project")
    click.echo(f"project: {header}"
               + (f" (root: {app.root})" if app.root is not None else ""))

    columns = ("PLUGIN", "SOURCE", "ENABLED", "COMMANDS")
    rows = []
    for record in records:
        commands = ", ".join(c.name for c in record.commands) or "-"
        rows.append((
            record.name,
            record.source,
            "yes" if record.enabled else "no",
            commands,
        ))

    widths = [max(len(col), *(len(row[i]) for row in rows)) if rows else len(col)
              for i, col in enumerate(columns)]
    for row in (columns, *rows):
        click.echo("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())


def make_plugins_group(app: App, records: list[PluginRecord]) -> click.Group:
    @click.group(name="plugins", help="Plugin management")
    def group() -> None:
        pass

    @group.command(name="list", help="List discovered plugins")
    def list_cmd() -> None:
        _list(app, records)

    return group
