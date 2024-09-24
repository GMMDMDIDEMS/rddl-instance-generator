from pydantic import FilePath, ValidationError
import pytest

from rddl_instance_generator.domain import Domain
from rddl_instance_generator.instance import InstanceGenerator


class TestInstanceGeneartor:
    def test_instance_generator_domain(
        self, mock_domain: Domain, instance_generator: InstanceGenerator
    ):
        assert instance_generator.domain == mock_domain

    def test_instance_generator_default_seed(
        self, instance_generator: InstanceGenerator
    ):
        assert instance_generator.seed == 42

    def test_instance_generator_template_path(
        self, instance_generator: InstanceGenerator
    ):
        assert (
            instance_generator.template_folder_path.parent
            == instance_generator.domain.get_template_folder()
        )

    def test_instance_generator_template_folder(
        self, instance_generator: InstanceGenerator
    ):
        assert (
            instance_generator.template_folder_path.name
            == f"size_{instance_generator.size}"
        )

    def test_instance_generator_invalid_num_instances(self, mock_domain: Domain):
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            InstanceGenerator(domain=mock_domain, num_instances=0, size=10)

    def test_instance_generator_invalid_size(self, mock_domain: Domain):
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            InstanceGenerator(domain=mock_domain, num_instances=5, size=0)


def test_get_template_folder_components(mock_domain: Domain):
    path: FilePath = mock_domain.get_template_folder()
    assert path.parts == ("domains", f"{mock_domain.name}", "data", "templates")


# def test_instance_generator_templates_path(domain):
#     instance_generator = InstanceGenerator(domain=domain, num_instances=5, size=10)
#     assert (
#         instance_generator.template_folder_path.parent
#         == instance_generator.domain.get_template_folder()
#     )
#     assert instance_generator.template_folder_path.name.startswith("size_")
#     assert int(instance_generator.template_folder_path.name.split("_")[-1]) == 10


# @patch("builtins.open", new_callable=mock_open)
# @patch("rddl_instance_generator.instance.get_instance_template")
# @patch("pathlib.Path.mkdir")
# def test_generate_template(mock_mkdir, mock_get_instance_template, mock_open, domain):
#     mock_template = Mock()
#     mock_template.render.return_value = "Rendered instance template output."
#     mock_get_instance_template.return_value = mock_template

#     instance_generator = InstanceGenerator(domain=domain, num_instances=1, size=5)

#     combination = (2, 3)
#     instance = instance_generator.generate_template(combination)
#     file_id = "_".join(map(str, combination))

#     # Assert directory creation
#     mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

#     # Ensure the template was rendered correctly
#     expected_context = {
#         "domain_name": domain.name.lower(),
#         "domain_alias": domain.domain_alias,
#         "file_id": file_id,
#         "types": domain.types,
#         "object_length": {"object_1": 2, "object_2": 3},
#     }

#     mock_template.render.assert_called_once_with(expected_context)

#     file_path = Path(
#         "domains",
#         str(domain.name),
#         "data",
#         "templates",
#         f"size_{instance_generator.size}",
#         f"instance_{file_id}.rddl",
#     )

#     mock_open.assert_called_once_with(file_path, "w", encoding="utf-8")

#     mock_open().write.assert_called_once_with("Rendered instance template output.")

#     assert instance.template_path == file_path
