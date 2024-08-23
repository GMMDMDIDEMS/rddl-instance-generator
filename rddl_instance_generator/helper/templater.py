from typing import Dict, List, TypedDict
from jinja2 import Environment, FileSystemLoader, Template

from rddl_instance_generator.domain import ObjectType


class UngroundedInstanceTemplate(TypedDict):
    domain_name: str
    domain_alias: str
    file_id: str
    types: List[ObjectType]
    object_length: Dict[str, int]


class GroundedInstanceTemplate(TypedDict):
    domain_name: str
    domain_alias: str
    file_id: str
    types: List[ObjectType]
    object_length: Dict[str, int]
    non_fluents: List[str]
    init_state: List[str]


def get_instance_template(
    search_path: str = "rddl_instance_generator", template_file: str = "template.jinja2"
) -> Template:
    env = Environment(loader=FileSystemLoader(searchpath=search_path))
    template = env.get_template(name=template_file)
    return template
