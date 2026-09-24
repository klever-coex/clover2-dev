import pathlib

import click

from clover2_dev.commands.base import emit, output_options
from clover2_dev.plugins.minio import client


def make_command(plugin_config) -> click.Command:
    @click.command(name="download", help="Download an object from a MinIO bucket")
    @click.argument("source",
                    help="Object key, or a URL as printed by 'minio upload'")
    @click.option("--output", type=click.Path(path_type=pathlib.Path),
                  help="Output file (default: object file name)")
    @client.minio_options
    @output_options
    def download_cmd(source: str, output: pathlib.Path | None,
                     bucket: str | None, endpoint: str | None,
                     insecure: bool, as_json: bool, field: str | None) -> None:
        parsed = client.parse_object_url(source)
        if parsed is not None:
            url_endpoint, url_bucket, key = parsed
        else:
            url_endpoint, url_bucket, key = None, None, source

        bucket_value = bucket or url_bucket or client.resolve_bucket(
            plugin_config, None)

        minio_client, endpoint_value = client.build_client(
            plugin_config, endpoint or url_endpoint, insecure)

        output_path = output or pathlib.Path(pathlib.PurePosixPath(key).name)
        client.download_artifact(minio_client, bucket_value, key, output_path)

        emit({
            "bucket": bucket_value,
            "key": key,
            "path": str(output_path),
        }, as_json, field)

    return download_cmd
