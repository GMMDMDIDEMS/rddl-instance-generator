import pytest
from rddl_instance_generator.domain import Domain, NonFluent, ObjectType, StateFluent
from rddl_instance_generator.instance import InstanceGenerator


@pytest.fixture
def domain(tmp_path):
    # Create ObjectType instances
    object_types = [
        ObjectType(name="object_1", kind="object", alias="obj1"),
        ObjectType(name="object_2", kind="object", alias="obj2"),
    ]

    # Create NonFluent instances
    non_fluents = [
        NonFluent(
            name="non_fluent",
            type_value="float",
            default=20.0,
            sampling_range={"min": 20.0, "max": 20.0},
        )
    ]

    # Create StateFluent instances
    state_fluents = [
        StateFluent(
            name="state_fluent",
            type_value="bool",
            default=False,
            sampling_range={"min": 0.3, "max": 0.7},
        )
    ]

    # Create and return the Domain instance
    domain = Domain(
        name="domain",
        domain_alias="domain",
        types=object_types,
        non_fluents=non_fluents,
        state_fluents=state_fluents,
    )
    # domain.get_template_folder = lambda: tmp_path
    return domain


@pytest.fixture
def instance_generator(domain: Domain):
    return InstanceGenerator(domain=domain, num_instances=1, size=2, seed=42)
