from pathlib import Path
from typing import List
from unittest.mock import MagicMock, PropertyMock, patch
from pydantic import FilePath
import pytest
from rddl_instance_generator.domain import Domain, NonFluent, ObjectType, StateFluent
from rddl_instance_generator.helper.templater import UngroundedInstanceTemplateData
from rddl_instance_generator.instance import Instance, InstanceGenerator


@pytest.fixture(scope="session")
def instance_template_file(tmp_path_factory: pytest.TempPathFactory) -> FilePath:
    file_path = tmp_path_factory.mktemp("tmp_dir") / "instance_42.rddl"
    file_path.touch()
    return file_path


@pytest.fixture(scope="session")
def domain_types() -> List[ObjectType]:
    return [
        ObjectType(name="object_1", kind="object", alias="obj1"),
        ObjectType(name="object_2", kind="object", alias="obj2"),
    ]


@pytest.fixture(scope="session")
def mock_domain(domain_types: List[ObjectType]):
    object_types = domain_types

    non_fluents = [
        NonFluent(
            name="non_fluent",
            type_value="float",
            default=20.0,
            value_range={"min": 20.0, "max": 20.0},
        )
    ]

    state_fluents = [
        StateFluent(
            name="state_fluent",
            type_value="bool",
            default=False,
            non_default_ratio={"min": 0.3, "max": 0.7},
        )
    ]

    return Domain(
        name="domain",
        domain_alias="domain",
        types=object_types,
        non_fluents=non_fluents,
        state_fluents=state_fluents,
    )


@pytest.fixture(scope="session")
def ungrounded_template_data(
    domain_types: List[ObjectType],
) -> UngroundedInstanceTemplateData:
    return UngroundedInstanceTemplateData(
        domain_alias="test_domain",
        identifier="5_10",
        types=domain_types,
        object_lengths={"object_1": 5, "object_2": 10},
    )


@pytest.fixture(scope="session")
def instance(
    ungrounded_template_data: UngroundedInstanceTemplateData,
    instance_template_file: FilePath,
) -> Instance:
    return Instance.from_ungrounded(
        ungrounded_data=ungrounded_template_data,
        size=15,
        template_path=instance_template_file,
    )


@pytest.fixture(scope="session")
def instance_generator(mock_domain: Domain):
    # with patch("rddl_instance_generator.instance.Path.mkdir"):
    return InstanceGenerator(domain=mock_domain, num_instances=1, size=2)
