import random
from itertools import combinations_with_replacement, cycle, islice, permutations
from pathlib import Path
from typing import Dict, Generator, List, Optional, Set, Tuple, TypedDict

from jinja2 import Environment, FileSystemLoader
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    InstanceOf,
    computed_field,
)

from rddl_instance_generator.domain import Domain, ObjectType
from memory_profiler import profile


class InstanceTemplateData(TypedDict):
    domain_name: str
    domain_alias: str
    file_id: str
    types: List[ObjectType]
    object_length: Dict[str, int]


class Instance(BaseModel):
    identifier: str
    size: int = Field(gt=0)
    template_path: Optional[FilePath] = None
    object_lengths: Dict[str, int]


class InstanceGenerator(BaseModel):
    domain: InstanceOf["Domain"]
    num_instances: int = Field(gt=0)
    size: int = Field(gt=0)
    seed: int = Field(default=42)

    @property
    def num_objects(self) -> int:
        return len(self.domain.types)

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
        templates_path = Path(
            "domains", str(self.domain.name), "data", "templates", f"size_{self.size}"
        )
        templates_path.mkdir(parents=True, exist_ok=True)

        # load jinja2 template
        # TODO refactor code: extract fucntion
        env = Environment(loader=FileSystemLoader("rddl_instance_generator"))
        template = env.get_template("template.jinja2")

        file_id = "_".join(map(str, object_combination))
        filename = f"instance_{file_id}.rddl"
        filepath = templates_path / filename

        object_length_mapping = self.get_object_length_mapping(object_combination)

        instance = Instance(
            identifier=file_id,
            size=self.size,
            object_lengths=object_length_mapping,
        )

        context: InstanceTemplateData = {
            "domain_name": self.domain.name.lower(),
            "domain_alias": self.domain.domain_alias,
            "file_id": file_id,
            "types": self.domain.types,
            "object_length": object_length_mapping,
        }

        instance_template = template.render(context)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(instance_template)

        instance.template_path = filepath

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
