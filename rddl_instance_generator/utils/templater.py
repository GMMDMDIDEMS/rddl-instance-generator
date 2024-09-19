from typing import Annotated, Any, Dict, List, Self
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, Field, model_validator

from rddl_instance_generator.domain import ObjectType


class UngroundedInstanceTemplateData(BaseModel):
    """
    Represents the necessary context to render a template for an ungrounded instance.

    Attributes:
        domain_name (str): The name of the domain.
        domain_alias (str): An alias for the domain.
        identifier (str): An identifier for the template file consisting of the number of objects in
            alphabetically order separated by an underscore.
        types (List[ObjectType]): A list of object types used in the domain.
        object_lengths (Dict[str, int]): A dictionary mapping object types to their
            respective counts.
    """

    # domain_name: str
    identifier: str = Field(..., min_length=1)
    domain_alias: str = Field(..., min_length=3)
    types: List["ObjectType"]
    object_lengths: Dict[str, Annotated[int, Field(strict=True, gt=0)]]

    @model_validator(mode="before")
    @classmethod
    def validate_object_lengths(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        object_lengths = data.get("object_lengths", {})
        if not object_lengths:
            raise ValueError("object_lengths dict must not be empty.")
        for k, v in object_lengths.items():
            if not isinstance(k, str):
                raise ValueError(
                    f"Key '{k}' must be of type 'str', but got '{type(k).__name__}'."
                )
            if not isinstance(v, int):
                raise ValueError(
                    f"Value for key '{k}' must be of type 'int', but got '{type(v).__name__}'."
                )
            if v <= 0:
                raise ValueError(
                    f"Value for key '{k}' must be greater than 0, but got '{v}'."
                )
        return data

    @model_validator(mode="after")
    def validate_matching_types(self) -> Self:
        # no need to check for duplicates as dict keys must be unique
        # therefore given two tests will detect potential duplicates in 'types'
        types_names = [t.name for t in self.types]
        object_length_keys = list(self.object_lengths.keys())

        if len(self.types) != len(self.object_lengths):
            raise ValueError(
                f"Mismatch between 'types' and 'object_lengths'. "
                f"Expected the same number of entries, but got {len(self.types)} types "
                f"({sorted(types_names)}) and {len(self.object_lengths)} object lengths "
                f"({object_length_keys})."
            )

        if set(types_names) != set(object_length_keys):
            raise ValueError(
                f"Mismatch between defined objects: {sorted(types_names)} != "
                f"{sorted(object_length_keys)}"
            )

        return self


class GroundedInstanceTemplateData(UngroundedInstanceTemplateData):
    """
    Represents the context to render a template generating a grounded instance.

    This class extends the `UngroundedInstanceTemplateData` by including
    additional fields that describe the initial state and non-fluents.

    Attributes:
        non_fluents (List[str]): A list of non-fluents.
        init_state (List[str]): A list of state-fluents representing the initial state.
    """

    non_fluents: List[str]
    init_state: List[str]

    @classmethod
    def from_ungrounded(
        cls,
        ungrounded_data: UngroundedInstanceTemplateData,
        non_fluents: List[str],
        init_state: List[str],
    ) -> "GroundedInstanceTemplateData":
        """
        Create a GroundedInstanceTemplateData instance inhereting the shared attributes
        from the UngroundedInstanceTemplateData instance.

        Args:
            ungrounded_data (UngroundedInstanceTemplateData): An instance of
                UngroundedInstanceTemplateData.
            non_fluents (List[str]): A list of non-fluent predicates in the domain.
            init_state (List[str]): A list of predicates representing the initial state
                of the domain.

        Returns:
            GroundedInstanceTemplate: An instance of GroundedInstanceTemplateData.
        """
        return cls(
            # domain_name=ungrounded_data.domain_name,
            identifier=ungrounded_data.identifier,
            domain_alias=ungrounded_data.domain_alias,
            types=ungrounded_data.types,
            object_lengths=ungrounded_data.object_lengths,
            non_fluents=non_fluents,
            init_state=init_state,
        )


def get_instance_template(
    search_path: str = "rddl_instance_generator", template_file: str = "template.jinja2"
) -> Template:
    """
    Loads a Jinja2 template from the specified file within a given directory.

    This function sets up a Jinja2 environment to load and return a template
    from a specified directory. The template can then be rendered with
    specific context data to generate dynamic content.

    Args:
        search_path (str, optional): The directory path where the template file
            is located. Defaults to "rddl_instance_generator".
        template_file (str, optional): The name of the template file to be loaded.
            Defaults to "template.jinja2".

    Returns:
        Template: A Jinja2 Template object that can be used to render content
        with the specified template.
    """
    env = Environment(loader=FileSystemLoader(searchpath=search_path))
    template = env.get_template(name=template_file)
    return template
