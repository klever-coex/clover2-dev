import logging

import click

from clover2_dev.plugins import PluginContext
from clover2_dev.plugins.minio.client import (  # noqa: F401  (public helpers)
    download_artifact,
    make_client,
    split_endpoint,
    upload_artifact,
)

logger = logging.getLogger(__name__)


class MinioPlugin:
    name = "minio"

    def create_commands(self, ctx: PluginContext) -> list[click.Command]:
        from clover2_dev.plugins.minio import commands

        @click.group(name="minio",
                     help="Upload/download artifacts via MinIO (S3-compatible)")
        def group() -> None:
            pass

        group.add_command(commands.upload.make_command(ctx.config))
        group.add_command(commands.download.make_command(ctx.config))

        return [group]


plugin = MinioPlugin()
