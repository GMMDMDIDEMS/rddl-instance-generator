from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, Union

import yaml
from pydantic import (
    BaseModel,
    DirectoryPath,
    FilePath,
    computed_field,
    field_validator,
    model_validator,
)
from pyRDDLGym.core.compiler.model import RDDLLiftedModel

from rddl_instance_generator.utils.helper import find_shortest_unique_prefix

DOMAINS_PATHS = Path("data")


class ObjectType(BaseModel):
    name: str
    kind: Literal["object"]
    alias: str

    @classmethod
    def from_lifted_model(cls, model: RDDLLiftedModel) -> List["ObjectType"]:
        object_types: List[ObjectType] = []

        objects: List[str] = list(model.type_to_objects.keys())
        obj_aliases = find_shortest_unique_prefix(objects)

        for obj in objects:
            object_types.append(
                ObjectType(name=obj, kind="object", alias=obj_aliases[obj])
            )

        return object_types


class Fluent(BaseModel):
    name: str
    type_value: Literal["bool", "int", "float"]
    default: Union[int, float, bool]
    value_range: Optional[Dict[Literal["min", "max"], Union[int, float]]] = None
    non_default_ratio: Optional[Dict[Literal["min", "max"], float]] = None

    # TODO add support for 'object' and 'enumerable' type_value

    @field_validator("non_default_ratio")
    @classmethod
    def validate_non_default_ratio(
        cls, v: Optional[Dict[Literal["min", "max"], float]]
    ) -> Optional[Dict[Literal["min", "max"], float]]:
        if v is not None:
            # TODO if non_default_ratio is defined, can the min and max value be None?
            # If yes, should we return a default value or issue an error?
            min_val = v.get("min", 0.0)
            max_val = v.get("max", 1.0)

            if not 0.0 <= min_val <= 1.0:
                raise ValueError(f"Min value {min_val} must be in [0.0, 1.0].")
            if not 0.0 <= max_val <= 1.0:
                raise ValueError(f"Max value {max_val} must be in [0.0, 1.0].")
            if min_val > max_val:
                raise ValueError(
                    f"Min value '{min_val}' must not be greater than max value '{max_val}'."
                )

        return v

    @model_validator(mode="after")
    def ensure_matching_types(self) -> "Fluent":
        default_type = type(self.default)

        if isinstance(self.default, bool):
            if self.value_range is not None:
                raise ValueError(
                    "Fluent with default type 'bool' must not have a 'value range'."
                )

        elif self.value_range is not None:
            if (
                "min" not in self.value_range.keys()
                or "max" not in self.value_range.keys()
            ):
                raise ValueError("Value range must contain 'min' and 'max' keys.")
            for k, v in self.value_range.items():
                if not isinstance(v, default_type):
                    raise ValueError(
                        f"Type of value_range value '{v}' for key '{k}' "
                        f"does not match the type of default value '{self.default}' "
                        f"(expected type: {default_type.__name__}, got: {type(v).__name__})"
                    )
        else:
            raise ValueError(
                f"Fluent of default type {self.default} must define a 'value range'."
            )
        return self

    @classmethod
    def from_lifted_model(
        cls, model: RDDLLiftedModel
    ) -> Tuple[List["NonFluent"], List["StateFluent"]]:
        non_fluents: List[NonFluent] = []
        state_fluents: List[StateFluent] = []

        for i, fluents in enumerate([model.non_fluents, model.state_fluents]):
            for var in fluents:
                # set default value of optional attrs
                value_range = None
                non_default_ratio = None

                var_range = model.variable_ranges[var]
                type_value = "float" if var_range == "real" else str(var_range)

                default = model.variable_defaults[var]

                if not isinstance(default, bool):
                    value_range = {"min": default, "max": default}

                # check whether fluent is parameterizable
                if model.variable_params[var] != []:
                    non_default_ratio = {"min": 0.5, "max": 0.5}

                fluent = cls(
                    name=var,
                    type_value=type_value,
                    default=default,
                    value_range=value_range,
                    non_default_ratio=non_default_ratio,
                )

                # must be non-fluent
                if i == 0:
                    non_fluents.append(
                        NonFluent(
                            **fluent.model_dump(),
                            type_fluent="non_fluent",
                        )
                    )

                else:
                    state_fluents.append(
                        StateFluent(
                            **fluent.model_dump(),
                            type_fluent="state_fluent",
                        )
                    )

        return (non_fluents, state_fluents)


class NonFluent(Fluent):
    _type_fluent: Literal["non_fluent"] = "non_fluent"


class StateFluent(Fluent):
    _type_fluent: Literal["state_fluent"] = "state_fluent"


class Domain(BaseModel):
    name: str
    domain_alias: str
    types: List[ObjectType]
    non_fluents: List[NonFluent]
    state_fluents: List[StateFluent]

    @classmethod
    def from_yaml(cls, file_path: DirectoryPath) -> "Domain":
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = yaml.safe_load(file)
                return cls(**data)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error loading YAML file: {e}")

    @classmethod
    def from_lifted_model(cls, name: str, model: RDDLLiftedModel) -> "Domain":
        non_fluents, state_fluents = Fluent.from_lifted_model(model=model)

        return cls(
            name=name,
            domain_alias=model.domain_name,
            types=ObjectType.from_lifted_model(model=model),
            non_fluents=non_fluents,
            state_fluents=state_fluents,
        )

    def to_yaml(self, file_path: Path) -> None:
        """Serializes the domain to a YAML file."""
        data = self.model_dump(
            exclude={"domain_file_path"},
            exclude_none=True,
        )

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                yaml.dump(data, file, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise IOError(f"Error writing YAML file: {e}") from e

    @computed_field
    def domain_file_path(self) -> FilePath:
        path = DOMAINS_PATHS / self.name / "domain.rddl"
        assert path.exists(), f"'domain.rddl' file does not exist at {path}"
        return path

    def get_template_folder(self) -> FilePath:
        return Path("domains", self.name, "data/templates")
