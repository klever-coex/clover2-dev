import click
import semver

from clover2_dev.errors import ToolingError
from clover2_dev.plugins.version.session import VersionSession
from clover2_dev.plugins.version.stores import discover_stores, write_all


@click.command(name="update", help="Set explicit version in all stores")
@click.argument("new_version")
@click.pass_obj
def command(session: VersionSession, new_version: str) -> None:
    try:
        target = semver.Version.parse(new_version)
    except ValueError as exc:
        raise ToolingError(f"Invalid version '{new_version}'") from exc

    write_all(discover_stores(session.dir, session.filter, session.exclude), target)
