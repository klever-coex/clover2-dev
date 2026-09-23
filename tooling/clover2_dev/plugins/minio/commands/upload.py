import pathlib

import click

from clover2_dev.commands.base import emit, output_options
from clover2_dev.errors import ToolingError
from clover2_dev.plugins.minio import client


def _parse_tags(raw: tuple[str, ...]) -> dict[str, str]:
    tags: dict[str, str] = {}
    for item in raw:
        name, sep, value = item.partition("=")
        if not sep or not name:
            raise ToolingError(f"Invalid tag '{item}'; expected KEY=VALUE")
        tags[name] = value
    return tags


def make_command(plugin_config) -> click.Command:
    @click.command(name="upload", help="Upload a file to a MinIO bucket")
    @click.argument("path", type=click.Path(
        exists=True, dir_okay=False, path_type=pathlib.Path))
    @click.option("--key", help="Object key (default: file name)")
    @click.option("--tag", "tags_", multiple=True, metavar="KEY=VALUE",
                  help="Object tag (repeatable)")
    @client.minio_options
    @output_options
    def upload_cmd(path: pathlib.Path, key: str | None, bucket: str | None,
                   endpoint: str | None, insecure: bool,
                   tags_: tuple[str, ...], as_json: bool,
                   field: str | None) -> None:
        minio_client, endpoint_value = client.build_client(
            plugin_config, endpoint, insecure)

        bucket_value = client.resolve_bucket(plugin_config, bucket)
        key_value = key or path.name

        client.upload_artifact(minio_client, bucket_value, key_value, path,
                               _parse_tags(tags_))

        emit({
            "endpoint": endpoint_value,
            "bucket": bucket_value,
            "key": key_value,
            "url": f"{endpoint_value}/{bucket_value}/{key_value}",
        }, as_json, field)

    return upload_cmd
