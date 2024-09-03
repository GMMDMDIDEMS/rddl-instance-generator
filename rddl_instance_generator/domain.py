from pathlib import Path
from typing import Any, Dict, List, Literal, Union

import yaml
from pydantic import (
    BaseModel,
    DirectoryPath,
    FilePath,
    computed_field,
    model_validator,
)


class ObjectType(BaseModel):
    name: str
    kind: Literal["object"]
    alias: str


class Fluent(BaseModel):
    name: str
    type_value: Literal["bool", "int", "float"]
    default: Union[int, float, bool]
    sampling_range: Dict[Literal["min", "max"], Union[int, float]]

    # TODO check for matching types between type_value and default type
    # TODO add support for 'object' and 'enumerable' type_value

    @model_validator(mode="before")
    @classmethod
    def check_sampling_range(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        sampling_bounds = data.get("sampling_range", {})
        default_type = data.get("default", None)
        if "min" not in sampling_bounds or "max" not in sampling_bounds:
            raise ValueError("Sampling range must contain 'min' and 'max' keys.")
        if isinstance(default_type, bool):
            for v in sampling_bounds.values():
                if not 0.0 <= v <= 1.0:
                    raise ValueError(
                        "Fluent type with default type 'bool' must have sampling"
                        "range values in [0.0, 1.0]"
                    )
        return data

    @model_validator(mode="after")
    def ensure_matching_types(self) -> "Fluent":
        default_type = type(self.default)

        for k, v in self.sampling_range.items():
            if isinstance(self.default, bool):
                if not isinstance(v, float):
                    raise ValueError(
                        "Fluent type with default type 'bool' must have sampling"
                        "range values in [0.0, 1.0]"
                    )
            elif not isinstance(v, default_type):
                raise ValueError(
                    f"Type of sampling_range value '{v}' for key '{k}' "
                    f"does not match the type of default value '{self.default}' "
                    f"(expected type: {default_type.__name__}, got: {type(v).__name__})"
                )
        return self


class NonFluent(Fluent):
    type_fluent: Literal["non_fluent"] = "non_fluent"


class StateFluent(Fluent):
    type_fluent: Literal["state_fluent"] = "state_fluent"


class Domain(BaseModel):
    name: str
    domain_alias: str
    types: List[ObjectType]
    non_fluents: List[NonFluent]
    state_fluents: List[StateFluent]

    @computed_field
    def domain_file_path(self) -> FilePath:
        path = Path("domains", self.name, "domain.rddl")
        assert path.exists(), f"'domain.rddl' file does not exist at {path}"
        return path

    def get_template_folder(self) -> FilePath:
        return Path("domains", self.name, "data/templates")

    @classmethod
    def from_yaml(cls, file_path: DirectoryPath) -> "Domain":
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = yaml.safe_load(file)
                return cls(**data)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error loading YAML file: {e}")
