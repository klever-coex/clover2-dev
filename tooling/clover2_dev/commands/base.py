import json
from collections.abc import Callable
from typing import Any

import click

from clover2_dev.errors import ToolingError


def output_options(func: Callable) -> Callable:
    func = click.option(
        "--json", "as_json", is_flag=True,
        help="Emit machine-readable JSON")(func)
    func = click.option(
        "--field",
        help="Print a single payload field")(func)
    return func


def emit(payload: dict[str, Any], as_json: bool, field: str | None) -> None:
    if as_json and field:
        raise click.UsageError("--json and --field are mutually exclusive")

    if as_json:
        click.echo(json.dumps(payload))
        return

    if field:
        if field not in payload:
            raise ToolingError(
                f"Unknown field '{field}'; available: {', '.join(payload)}")
        click.echo(payload[field])
        return

    for key, value in payload.items():
        click.echo(f"{key}: {value}")
