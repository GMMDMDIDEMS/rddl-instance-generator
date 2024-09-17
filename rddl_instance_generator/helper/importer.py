from pathlib import Path
import re
import shutil
import tempfile
from typing import Annotated, Dict, List, Union

import typer

from jinja2 import Template
from pyRDDLGym.core.parser.reader import RDDLReader
from pyRDDLGym.core.parser.parser import RDDLParser
from pyRDDLGym.core.compiler.model import RDDLLiftedModel

from rddl_instance_generator.domain import Domain
from rddl_instance_generator.helper.templater import get_instance_template

DOMAINS_PATH = Path("data")

app = typer.Typer()


def get_lifted_model(domain_file: Path, instance_file: Path) -> RDDLLiftedModel:
    """Generates the lifted model from the RDDL domain and instance."""
    reader = RDDLReader(domain_file, instance_file)
    rddl_txt = reader.rddltxt
    parser = RDDLParser(lexer=None, verbose=False)
    parser.build()
    rddl_ast = parser.parse(rddl_txt)
    return RDDLLiftedModel(rddl_ast)


def parse_domain_file(domain_path: Path) -> List[Dict[str, str]]:
    types_section = False
    types: List[Dict[str, str]] = []

    with open(domain_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # TODO add some asserttions and validations to ensure
    # that the given filepath demonstrates a domain.rddl file
    for line in lines:
        # remove leading and trailing whitespace
        line = line.strip()

        # match 'types' block
        if re.match(r"types\s*\{\s*", line):
            types_section = True
            continue

        # if inside 'types' section, match/extract 'object's
        if types_section:
            type_match = re.match(r"(\w+)\s*:\s*object\s*;", line)
            if type_match:
                obj = type_match.group(1)
                # types.append(type_match.group(1))
                types.append({"name": str(obj), "alias": str(obj)})

            # end of 'types' block -> stop parsing
            if re.match(r"\}\s*", line):
                break

    # print(types)
    return types


def write_minimal_instance(domain_file_path: Path, types: List[Dict[str, str]]):
    context = {
        "domain_alias": "random_domain_alias",
        "identifier": "id",
        "types": types,
        "object_lengths": {obj["name"]: 1 for obj in types},
    }
    instance_template: Template = get_instance_template()

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".rddl", mode="w", encoding="utf-8"
    ) as temp_file:
        # Render the instance file content using the template
        instance_file_content = instance_template.render(context)

        # Write the rendered content to the temporary file
        temp_file.write(instance_file_content)
        temp_file.flush()

        # Get the path of the temporary file
        temp_file_path = Path(temp_file.name)

        lifted_model = get_lifted_model(domain_file_path, temp_file_path)

        return lifted_model


def domain_callback(value: str) -> str:
    domain_path = DOMAINS_PATH / value

    # abort if folder exists and is not empty
    if domain_path.exists() and any(domain_path.iterdir()):
        raise typer.BadParameter(
            f"Domain '{value}' already exists at '{domain_path}', Importing aborted to avoid overwriting.",
        )

    # create domain folder if it doesn't exist yet
    domain_path.mkdir(parents=True, exist_ok=True)

    return value


def domain_file_callback(value: Union[str, Path]) -> Path:
    file_path = Path(value) if isinstance(value, str) else value

    if not file_path.exists():
        raise typer.BadParameter(
            f"'{file_path}' does not exist. Please provide a valid file path."
        )

    return file_path


@app.command()
def import_domain(
    domain_name: Annotated[
        str,
        typer.Option(
            "--domain-name",
            "-d",
            callback=domain_callback,
            help="Name of the domain and the corresponding folder.",
        ),
    ],
    domain_file: Annotated[
        str,
        typer.Option(
            "--domain-file-path",
            "-fp",
            callback=domain_file_callback,
            help="Path of the respective domain.rddl file.",
        ),
    ],
):
    domain_path = DOMAINS_PATH / f"{domain_name}"
    domain_file_path = Path(
        domain_file
    )  # is already Path object due to 'domain_file_callback'. However, otherwise Pylance throws type error.

    # copy domain.rddl file to destination folder
    shutil.copy(domain_file_path, domain_path / "domain.rddl")

    types = parse_domain_file(domain_path=domain_file_path)
    lifted_model = write_minimal_instance(
        domain_file_path=domain_file_path, types=types
    )

    domain = Domain.from_lifted_model(name=domain_name, model=lifted_model)

    config_file_path = domain_path / "config.yaml"
    domain.to_yaml(file_path=config_file_path)


if __name__ == "__main__":
    app()
