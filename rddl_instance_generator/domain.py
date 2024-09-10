from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

import yaml
from pydantic import (
    BaseModel,
    DirectoryPath,
    FilePath,
    computed_field,
    field_validator,
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
    value_range: Optional[Dict[Literal["min", "max"], Union[int, float]]] = None
    non_default_ratio: Optional[Dict[Literal["min", "max"], float]] = None

    # TODO add support for 'object' and 'enumerable' type_value

    @field_validator("non_default_ratio")
    def validate_non_default_ratio(
        self, v: Optional[Dict[Literal["min", "max"], float]]
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

    @classmethod
    def from_yaml(cls, file_path: DirectoryPath) -> "Domain":
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = yaml.safe_load(file)
                return cls(**data)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error loading YAML file: {e}")

    def to_yaml(self, file_path: Path) -> None:
        """Serializes the domain to a YAML file."""
        data = self.model_dump()

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                yaml.dump(data, file, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise IOError(f"Error writing YAML file: {e}") from e

    @computed_field
    def domain_file_path(self) -> FilePath:
        path = Path("domains", self.name, "domain.rddl")
        assert path.exists(), f"'domain.rddl' file does not exist at {path}"
        return path

    def get_template_folder(self) -> FilePath:
        return Path("domains", self.name, "data/templates")
