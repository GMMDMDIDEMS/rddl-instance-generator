from dataclasses import dataclass
from pathlib import Path
import random
from typing import List, Tuple, Union

from jinja2 import Template
from pyRDDLGym.core.compiler.model import RDDLLiftedModel
from pyRDDLGym.core.parser.parser import RDDLParser
from pyRDDLGym.core.parser.reader import RDDLReader
from pydantic import FilePath

from rddl_instance_generator.domain import Domain
from rddl_instance_generator.helper.templater import (
    GroundedInstanceTemplateData,
    get_instance_template,
)
from rddl_instance_generator.instance import Instance


@dataclass
class RDDL:
    domain: "Domain"
    instance: "Instance"
    seed: int

    def __post_init__(self):
        self.model = self.generate_lifted_model()
        self.non_fluents = getattr(self.model, "non_fluents", {})
        self.state_fluents = getattr(self.model, "state_fluents", {})
        self.variable_params = getattr(self.model, "variable_params", {})
        self.variable_groundings = getattr(self.model, "variable_groundings", {})

    def generate_lifted_model(self) -> RDDLLiftedModel:  # pragma: no cover
        """Generates the lifted model from the RDDL domain and instance."""
        reader = RDDLReader(self.domain.domain_file_path, self.instance.template_path)
        rddl_txt = reader.rddltxt
        parser = RDDLParser(lexer=None, verbose=False)
        parser.build()
        rddl_ast = parser.parse(rddl_txt)
        return RDDLLiftedModel(rddl_ast)

    @staticmethod
    def convert_grounded_to_instance(v: str):
        return v.replace("___", "(").replace("__", ",") + ")"

    def get_file_path(self) -> FilePath:
        path = Path(
            str(self.domain.get_template_folder()).replace("templates", ""),
            f"size_{self.instance.size}",
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_random_sample(
        self,
        pvars: List[str],
        min_range: Union[float, int],
        max_range: Union[float, int],
        seed: int,
    ) -> List[str]:
        num_vars = len(pvars)
        num_min = int(min_range * num_vars)
        num_max = int(max_range * num_vars)

        random.seed(seed)
        # number of grounded vars which will be set to True
        num = random.randint(num_min, num_max)
        num = max(1, num)

        # indexes of grounded vars which will be set to True
        indexes = random.sample(range(num_vars), num)
        # print(indexes)

        return [str(pvars[index]) for index in sorted(indexes)]

    def get_random_float_sample(
        self,
        pvars: List[str],
        min_range: Union[float, int],
        max_range: Union[float, int],
        seed: int,
    ) -> List[str]:
        num_vars = len(pvars)

        random.seed(seed)

        num = random.randint(1, num_vars)

        indexes = random.sample(range(num_vars), num)

        sampled_vars: List[str] = []

        for index in sorted(indexes):
            sampled_value = random.uniform(min_range, max_range)
            sampled_vars.append(f"{pvars[index]} = {sampled_value}")

        return sampled_vars

    def set_pvar_groundings(self) -> Tuple[List[str], List[str]]:
        nfs: List[str] = []
        sfs: List[str] = []

        # set instance seed and sample fluent seeds
        random.seed(self.seed)
        seeds = random.sample(
            range(10_000), len(self.non_fluents) + len(self.state_fluents)
        )
        seed_index = 0

        for nf in self.domain.non_fluents:
            nf_name = nf.name
            type_value = nf.type_value
            min_range = nf.sampling_range["min"]
            max_range = nf.sampling_range["max"]

            # extract only parameterizable pvars
            if self.variable_params[nf_name] != []:
                nf_variables = self.variable_groundings[nf_name]
                converted_nf_variables = list(
                    map(self.convert_grounded_to_instance, nf_variables)
                )

                if type_value == "bool":
                    nfs.extend(
                        self.get_random_sample(
                            pvars=converted_nf_variables,
                            min_range=min_range,
                            max_range=max_range,
                            seed=seeds[seed_index],
                        )
                    )
                else:
                    nfs.extend(
                        self.get_random_float_sample(
                            pvars=converted_nf_variables,
                            min_range=min_range,
                            max_range=max_range,
                            seed=seeds[seed_index],
                        )
                    )
            else:
                if min_range != max_range:
                    nfs.extend([f"{nf_name} = {random.uniform(min_range, max_range)}"])
                else:
                    pass

            seed_index += 1

        # set init-state
        for sf in self.domain.state_fluents:
            sf_name = sf.name
            type_value = sf.type_value
            min_range = sf.sampling_range["min"]
            max_range = sf.sampling_range["max"]

            # extract only parameterizable pvars
            if self.variable_params[sf_name] != []:
                sf_variables = self.variable_groundings[sf_name]
                converted_sf_variables = list(
                    map(self.convert_grounded_to_instance, sf_variables)
                )

                if type_value == "bool":
                    sfs.extend(
                        self.get_random_sample(
                            pvars=converted_sf_variables,
                            min_range=min_range,
                            max_range=max_range,
                            seed=seeds[seed_index],
                        )
                    )
                else:
                    sfs.extend(
                        self.get_random_float_sample(
                            pvars=converted_sf_variables,
                            min_range=min_range,
                            max_range=max_range,
                            seed=seeds[seed_index],
                        )
                    )

            seed_index += 1

        return nfs, sfs

    def write_instance(self) -> None:
        template: Template = get_instance_template()

        file_name = f"instance_{self.instance.identifier}_{self.seed}.rddl"
        filepath = self.get_file_path() / file_name

        nfs, sfs = self.set_pvar_groundings()

        context = GroundedInstanceTemplateData.from_ungrounded(
            self.instance, non_fluents=nfs, init_state=sfs
        )

        instance_file = template.render(context)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(instance_file)

        del nfs, sfs
