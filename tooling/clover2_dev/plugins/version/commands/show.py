import click

from clover2_dev.plugins.version.session import VersionSession
from clover2_dev.plugins.version.stores import discover_stores, reference_store


@click.command(name="show", help="Show stores versions")
@click.option("--main-only", is_flag=True,
              help="Show only reference package version")
@click.pass_obj
def command(session: VersionSession, main_only: bool) -> None:
    stores = discover_stores(session.dir, session.filter, session.exclude)

    if main_only:
        click.echo(reference_store(stores, session.reference).read())
        return

    all_versions: dict[str, list[str]] = {}

    for store in stores:
        all_versions.setdefault(store.store_name, [])
        all_versions[store.store_name] += [f"{store.name}: {store.read()}"]

    for store_name, versions in all_versions.items():
        click.echo(f"{store_name}:")
        for version in versions:
            click.echo(f"\t{version}")
