import click

from clover2_dev.plugins import PluginContext


class HelloPlugin:
    name = "hello"

    def create_commands(self, ctx: PluginContext) -> list[click.Command]:
        greeting = ctx.config.get("greeting", "Hello")

        @click.command(name="hello", help="Example plugin: greet the project")
        def hello() -> None:
            project = "world"
            if ctx.root is not None:
                project = ctx.root.name
            click.echo(f"{greeting}, {project}!")

        return [hello]


plugin = HelloPlugin()
