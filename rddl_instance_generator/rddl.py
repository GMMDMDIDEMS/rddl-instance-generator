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
    GroundedInstanceTemplate,
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
        return Path(
            str(self.domain.get_template_folder()).replace("templates", ""),
            f"size_{self.instance.size}",
        )

    def get_random_sample(
        self,
        pvars: List[str],
        min_range: Union[float, int],
        max_range: Union[float, int],
    ) -> List[str]:
        # TODO pvar must be of type bool, as we define percentage ranges

        num_vars = len(pvars)
        num_min = int(min_range * num_vars)
        num_max = int(max_range * num_vars)

        random.seed(self.seed)
        # number of grounded vars which will be set to True
        num = random.randint(num_min, num_max)
        num = max(1, num)

        # indexes of grounded vars which will be set to True
        indexes = random.sample(range(num_vars), num)

        return [str(pvars[index]) for index in sorted(indexes)]

    def set_pvar_groundings(self) -> Tuple[List[str], List[str]]:
        nfs: List[str] = []
        sfs: List[str] = []

        for nf in self.domain.non_fluents:
            nf_name = nf.name
            min_range = nf.sampling_range["min"]
            max_range = nf.sampling_range["max"]

            # extract only parameterizable pvars
            if self.variable_params[nf_name] != []:
                nf_variables = self.variable_groundings[nf_name]
                converted_nf_variables = list(
                    map(self.convert_grounded_to_instance, nf_variables)
                )

                nfs.extend(
                    self.get_random_sample(
                        pvars=converted_nf_variables,
                        min_range=min_range,
                        max_range=max_range,
                    )
                )

        # set init-state
        for sf in self.domain.state_fluents:
            sf_name = sf.name
            min_range = sf.sampling_range["min"]
            max_range = sf.sampling_range["max"]

            # extract only parameterizable pvars
            if self.variable_params[sf_name] != []:
                sf_variables = self.variable_groundings[sf_name]
                converted_sf_variables = list(
                    map(self.convert_grounded_to_instance, sf_variables)
                )

                sfs.extend(
                    self.get_random_sample(
                        pvars=converted_sf_variables,
                        min_range=min_range,
                        max_range=max_range,
                    )
                )

        return nfs, sfs

    def write_instance(self) -> None:
        template: Template = get_instance_template()

        file_name = f"instance_{self.instance.identifier}_{self.seed}.rddl"
        filepath = self.get_file_path() / file_name

        nfs, sfs = self.set_pvar_groundings()

        context: GroundedInstanceTemplate = {
            "domain_name": self.domain.name.lower(),
            "domain_alias": self.domain.domain_alias,
            "file_id": self.instance.identifier,
            "types": self.domain.types,
            "object_length": self.instance.object_lengths,
            "non_fluents": nfs,
            "init_state": sfs,
        }

        instance_file = template.render(context)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(instance_file)

        del nfs, sfs
