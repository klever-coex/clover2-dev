import click

from clover2_dev.commands.base import emit, output_options
from clover2_dev.plugins.version import versioning
from clover2_dev.plugins.version.session import VersionSession
from clover2_dev.plugins.version.stores import discover_stores


@click.command(name="compose",
               help="Compose the full version from the git context")
@click.option("--ref",
              help="Git ref: refs/tags/vX, refs/heads/... or bare vX tag")
@click.option("--mode",
              type=click.Choice(["develop", "master", "release", "pre-release"]),
              help="Explicit build mode (local builds); otherwise derived from --ref")
@click.option("--latest-rc", is_flag=True,
              help="Report the newest rc tag (for promote)")
@click.option("--latest-stable", is_flag=True,
              help="Report the newest stable tag (for changelog ranges)")
@output_options
@click.pass_obj
def command(session: VersionSession, ref: str | None, mode: str | None,
            latest_rc: bool, latest_stable: bool,
            as_json: bool, field: str | None) -> None:
    latest = latest_rc or latest_stable
    stores = None if latest else discover_stores(session.dir, session.filter, session.exclude)

    payload = versioning.compose(
        stores, session.dir, session.reference,
        ref=ref, mode=mode, latest_rc=latest_rc, latest_stable=latest_stable)

    emit(payload, as_json, field)
