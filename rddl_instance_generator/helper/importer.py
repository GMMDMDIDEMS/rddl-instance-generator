from pathlib import Path
import re
import tempfile
from typing import Any, Dict, List

from jinja2 import Template
from pyRDDLGym.core.parser.reader import RDDLReader
from pyRDDLGym.core.parser.parser import RDDLParser
from pyRDDLGym.core.compiler.model import RDDLLiftedModel

from rddl_instance_generator.helper.templater import get_instance_template


def get_lifted_model(domain_file: Path, instance_file: Path) -> RDDLLiftedModel:
    """Generates the lifted model from the RDDL domain and instance."""
    reader = RDDLReader(domain_file, instance_file)
    rddl_txt = reader.rddltxt
    parser = RDDLParser(lexer=None, verbose=False)
    parser.build()
    rddl_ast = parser.parse(rddl_txt)
    return RDDLLiftedModel(rddl_ast)


def parse_domain(domain_path: Path) -> List[Dict[str, str]]:
    types_section = False
    types: List[Dict[str, str]] = []

    with open(domain_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # TODO add some asserttions and validations to ensure that the given filepath demonstrates a domain.rddl file
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


def write_minimal_instance(types: List[Dict[str, str]]):
    context = {
        "domain_alias": "testminimal_domain",
        "identifier": "id",
        "types": types,
        "object_lengths": {obj["name"]: 1 for obj in types},
    }
    instance_template: Template = get_instance_template()

    # instance_file = instance_template.render(context)

    # print(instance_file)

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".rddl", mode="w", encoding="utf-8"
    ) as temp_file:
        # Render the instance file content using the template
        instance_file_content = instance_template.render(context)

        # Write the rendered content to the temporary file
        temp_file.write(instance_file_content)
        temp_file.flush()

        # print(temp_file)

        # Get the path of the temporary file
        temp_file_path = temp_file.name

        lifted_model = get_lifted_model(domain_path, temp_file_path)
        print(lifted_model)


if __name__ == "__main__":
    domain_path = Path("domains/Wildfire/domain.rddl")
    types = parse_domain(domain_path=domain_path)
    write_minimal_instance(types)
