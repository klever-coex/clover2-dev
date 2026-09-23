import click

from clover2_dev.commands.base import emit, output_options
from clover2_dev.plugins.version import versioning
from clover2_dev.plugins.version.session import VersionSession
from clover2_dev.plugins.version.stores import discover_stores


@click.command(name="bump",
               help="Bump reference package version and sync all stores")
@click.argument("bump_field", metavar="FIELD",
                type=click.Choice(["major", "minor", "patch", "rc"]),
                required=True)
@click.option("--base", type=click.Choice(["major", "minor", "patch"]),
              default="minor", show_default=True,
              help="Base bump applied when cutting a fresh rc series")
@output_options
@click.pass_obj
def command(session: VersionSession, bump_field: str, base: str,
            as_json: bool, field: str | None) -> None:
    stores = discover_stores(session.dir, session.filter, session.exclude)

    if bump_field == "rc":
        payload = versioning.bump_rc(stores, session.dir, base,
                                      session.reference)
    else:
        payload = versioning.bump(stores, bump_field, session.reference)

    emit(payload, as_json, field)
