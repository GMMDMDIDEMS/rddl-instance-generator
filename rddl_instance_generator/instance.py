import random
from itertools import combinations_with_replacement, cycle, islice, permutations
from typing import Any, Dict, Generator, Set, Tuple

from jinja2 import Template
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    InstanceOf,
    computed_field,
    field_validator,
    model_validator,
)

from rddl_instance_generator.domain import Domain
from rddl_instance_generator.helper.templater import (
    UngroundedInstanceTemplateData,
    get_instance_template,
)


class Instance(UngroundedInstanceTemplateData):
    size: int = Field(gt=0)
    template_path: FilePath

    @model_validator(mode="before")
    @classmethod
    def validate_matching_size(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        size = data.get("size")
        object_lengths = data.get("object_lengths", {})

        expected_size = sum(object_lengths.values())

        if size != expected_size:
            raise ValueError(
                (
                    f"The instance size {size} must match the sum of the "
                    f"object lengths {expected_size}."
                )
            )

        return data

    @field_validator("template_path")
    @classmethod
    def validate_template_path(cls, v: FilePath) -> FilePath:
        if not v.name.startswith("instance"):
            raise ValueError("Instance template must start with 'instance'.")
        if v.suffix != ".rddl":
            raise ValueError("Instance template must have file type '.rddl'.")
        return v

    @classmethod
    def from_ungrounded(
        cls,
        ungrounded_data: UngroundedInstanceTemplateData,
        template_path: FilePath,
        size: int = Field(gt=0),
    ) -> "Instance":
        return cls(
            identifier=ungrounded_data.identifier,
            domain_alias=ungrounded_data.domain_alias,
            types=ungrounded_data.types,
            object_lengths=ungrounded_data.object_lengths,
            size=size,
            template_path=template_path,
        )


class InstanceGenerator(BaseModel):
    domain: InstanceOf["Domain"]
    num_instances: int = Field(gt=0)
    size: int = Field(gt=0)
    seed: int = Field(default=42)

    @property
    def num_objects(self) -> int:
        return len(self.domain.types)

    @property
    def template_folder_path(self) -> FilePath:
        templates_path = self.domain.get_template_folder() / f"size_{self.size}"
        templates_path.mkdir(parents=True, exist_ok=True)
        return templates_path

    @computed_field
    @property
    def combinations(self) -> Set[Tuple[int, ...]]:
        combinations: Set[Tuple[int, ...]] = set()

        for combination in combinations_with_replacement(
            range(1, self.size + 1), self.num_objects
        ):
            if sum(combination) == self.size:
                for permutation in permutations(combination):
                    combinations.add(permutation)

        return combinations

    def get_object_length_mapping(self, combination: Tuple[int, ...]) -> Dict[str, int]:
        object_length_mapping: Dict[str, int] = {}
        for obj_name, length in zip(self.domain.types, combination):
            object_length_mapping[obj_name.name] = length
        return object_length_mapping

    @computed_field
    @property
    def random_seeds(self) -> list[int]:
        random.seed(self.seed)
        seeds = [random.randint(1, 10_000) for _ in range(self.num_instances)]
        return seeds

    def generate_template(self, object_combination: Tuple[int, ...]) -> Instance:
        assert sum(object_combination) == self.size

        template: Template = get_instance_template()

        file_id = "_".join(map(str, object_combination))
        filename = f"instance_{file_id}.rddl"
        filepath = self.template_folder_path / filename

        object_length_mapping = self.get_object_length_mapping(object_combination)

        context = UngroundedInstanceTemplateData(
            # domain_name=self.domain.name.lower(),
            identifier=file_id,
            domain_alias=self.domain.domain_alias,
            types=self.domain.types,
            object_lengths=object_length_mapping,
        )

        instance_template = template.render(context)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(instance_template)

        instance = Instance.from_ungrounded(
            ungrounded_data=context,
            size=self.size,
            template_path=filepath,
        )

        return instance

    def generate_instances(
        self,
    ) -> Generator[Tuple[Instance, int], None, None]:
        instance_distribution = list(
            islice(cycle(self.combinations), self.num_instances)
        )

        for index, combination in enumerate(instance_distribution):
            instance = self.generate_template(combination)
            instance_seed = self.random_seeds[index]

            yield (instance, instance_seed)
