from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.progress import track
from rich.table import Table

from rddl_instance_generator.domain import Domain
from rddl_instance_generator.instance import InstanceGenerator
from rddl_instance_generator.rddl import RDDL

DOMAINS_PATH = Path("data")

app = typer.Typer()
console = Console()


def print_summary(domain_name: str, num_instances: int, num_objects: int, seed: int):
    table = Table(title="Instance Generation Summary")
    table.add_column("Domain Name")
    table.add_column("Number of Instances")
    table.add_column("Number of Objects")
    table.add_column("Seed")
    table.add_row(domain_name, str(num_instances), str(num_objects), str(seed))

    console.print(table)


def load_config(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as _:
            raise yaml.YAMLError("'config.yaml' could not be loaded.")


def domain_callback(value: str):
    supported_domains = [
        str(domain.name)
        for domain in DOMAINS_PATH.iterdir()
        if not domain.name.startswith(".")
    ]
    if value not in supported_domains:
        raise typer.BadParameter(
            f"Unsupported domain. Choose from: {', '.join(supported_domains)}",
        )
    return value


def num_instances_callback(value: int):
    if value < 1:
        raise typer.BadParameter(
            "At least one instance must be generated.",
        )
    return value


def size_callback(ctx: typer.Context, value: int):
    # TODO duplicate code as we have to extract the number of objects
    # the domain has again for finding all combinations
    domain_name = ctx.params.get("domain_name")
    config_path = DOMAIN_PATH / str(domain_name) / "config.yaml"
    assert config_path.exists(), "config.yaml does not exist"

    config = load_config(config_path)
    num_types = len(config.get("types", []))

    if value < num_types:
        raise typer.BadParameter(
            f"Invalid object size: {value}. Domain has {num_types} types. "
            f"Therefore, instances must have an object size of at least {num_types}."
        )
    return value


@app.command()
def main(
    domain_name: Annotated[
        str,
        typer.Option(
            "--domain-name",
            "-d",
            callback=domain_callback,
            help="Name of the domain",
        ),
    ],
    num_instances: Annotated[
        int,
        typer.Option(
            "--num-instances",
            "-n",
            callback=num_instances_callback,
            help="Number of instances to generate",
        ),
    ],
    size: Annotated[
        int,
        typer.Option(
            "--size",
            "-o",
            callback=size_callback,
            help="Number of objects per instance",
        ),
    ],
    seed: Annotated[
        int,
        typer.Option("--seed", "-s", help="Random seed for instance generation"),
    ] = 42,
):
    print_summary(domain_name, num_instances, size, seed)

    # load config data
    config_path = DOMAIN_PATH / str(domain_name) / "config.yaml"
    domain = Domain.from_yaml(config_path)

    instance_generator = InstanceGenerator(
        domain=domain, num_instances=num_instances, size=size, seed=seed
    )

    for instance, instance_seed in track(
        instance_generator.generate_instances(),
        description="[red]Generating instances",
        total=num_instances,
    ):
        rddl = RDDL(domain=domain, instance=instance, seed=instance_seed)
        rddl.write_instance()

        del rddl


if __name__ == "__main__":
    app()
