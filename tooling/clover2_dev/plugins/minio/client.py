import logging
import os
import pathlib
from typing import Any, Mapping

import click
from minio import Minio
from minio.commonconfig import Tags

from clover2_dev.errors import ToolingError

logger = logging.getLogger(__name__)

DEFAULT_BUCKET = "clover2"
ENDPOINT_ENV = "MINIO_ENDPOINT"
ACCESS_KEY_ENV = "MINIO_ACCESS_KEY"
SECRET_KEY_ENV = "MINIO_SECRET_KEY"
SECURE_ENV = "MINIO_SECURE"


def minio_options(func):
    func = click.option(
        "--bucket", help=f"Bucket (default: {DEFAULT_BUCKET})")(func)
    func = click.option(
        "--endpoint",
        help=f"MinIO endpoint host[:port] or URL (env: {ENDPOINT_ENV})")(func)
    func = click.option(
        "--insecure", is_flag=True,
        help="Disable TLS (endpoint without a scheme)")(func)
    return func


def split_endpoint(endpoint: str, default_secure: bool) -> tuple[str, bool]:
    if "://" in endpoint:
        secure, host = endpoint.startswith(
            "https://"), endpoint.split("://", 1)[1]
        return host, secure
    return endpoint, default_secure


def parse_object_url(source: str) -> tuple[str, str, str] | None:
    if "://" not in source:
        return None

    scheme, rest = source.split("://", 1)
    host, _, path = rest.partition("/")
    bucket, _, key = path.partition("/")
    if not host or not bucket or not key:
        raise ToolingError(
            f"Invalid object URL '{source}'; expected <endpoint>/<bucket>/<key>")

    return f"{scheme}://{host}", bucket, key


def resolve_endpoint(plugin_config: Mapping[str, Any],
                     endpoint_flag: str | None) -> str:
    return endpoint_flag or os.environ.get(
        ENDPOINT_ENV, str(plugin_config.get("endpoint", "")))


def resolve_secure(plugin_config: Mapping[str, Any], insecure_flag: bool) -> bool:
    secure = plugin_config.get("secure", True)
    if not isinstance(secure, bool):
        raise ToolingError("[plugins.minio] secure must be a boolean")

    env_secure = os.environ.get(SECURE_ENV)
    if env_secure is not None:
        secure = env_secure.lower() != "false"
    if insecure_flag:
        secure = False

    return secure


def resolve_bucket(plugin_config: Mapping[str, Any],
                   bucket_flag: str | None) -> str:
    return bucket_flag or str(plugin_config.get("bucket", DEFAULT_BUCKET))


def make_client(endpoint: str, secure: bool,
                access_key: str, secret_key: str) -> Minio:
    return Minio(endpoint, access_key=access_key,
                 secret_key=secret_key, secure=secure)


def build_client(plugin_config: Mapping[str, Any], endpoint_flag: str | None,
                 insecure_flag: bool) -> tuple[Minio, str]:
    endpoint_value = resolve_endpoint(plugin_config, endpoint_flag)
    if not endpoint_value:
        raise ToolingError(f"MinIO endpoint is not set ({ENDPOINT_ENV})")

    host, secure = split_endpoint(
        endpoint_value, resolve_secure(plugin_config, insecure_flag))
    client = make_client(host, secure,
                         os.environ.get(ACCESS_KEY_ENV, ""),
                         os.environ.get(SECRET_KEY_ENV, ""))
    return client, endpoint_value


def upload_artifact(client: Minio, bucket: str, key: str,
                    path: pathlib.Path,
                    tags: dict[str, str] | None = None) -> str:
    object_tags = Tags(for_object=True)
    for name, value in (tags or {}).items():
        object_tags[name] = value

    logger.info("Uploading '%s' -> %s/%s", path, bucket, key)
    client.fput_object(bucket, key, path, tags=object_tags)
    logger.info("Uploaded: %s/%s", bucket, key)
    return key


def download_artifact(client: Minio, bucket: str, key: str,
                      output: pathlib.Path) -> pathlib.Path:
    output.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading %s/%s -> '%s'", bucket, key, output)
    client.fget_object(bucket, key, str(output))
    logger.info("Downloaded: %s", output)
    return output
