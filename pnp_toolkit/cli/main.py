import click

from pnp_toolkit.cli.build import build


@click.group()
def main():
    pass


main.add_command(build)


if __name__ == "__main__":
    main()
