from pathlib import Path
from pydantic import FilePath, ValidationError
import pytest
from rddl_instance_generator.helper.templater import UngroundedInstanceTemplateData
from rddl_instance_generator.instance import Instance, InstanceGenerator


class TestInstance:
    def test_instance_identifier(self, instance: Instance):
        assert instance.identifier == "5_10"

    def test_instance_size(self, instance: Instance):
        assert instance.size == 15

    def test_instance_template_file_path(
        self, instance: Instance, instance_template_file: FilePath
    ):
        assert instance.template_path == instance_template_file

    def test_object_lengths(self, instance: Instance):
        assert instance.object_lengths == {"object_1": 5, "object_2": 10}

    def test_instance_incorrect_size(
        self,
        instance_template_file: FilePath,
        ungrounded_template_data: UngroundedInstanceTemplateData,
    ):
        with pytest.raises(ValidationError) as exc_info:
            Instance.from_ungrounded(
                ungrounded_data=ungrounded_template_data,
                size=14,
                template_path=instance_template_file,
            )

        assert exc_info.value.errors(
            include_context=False, include_input=False, include_url=False
        ) == [
            {
                "type": "value_error",
                "loc": (),
                "msg": "Value error, The instance size 14 must match the sum of the object lengths 15.",
            }
        ]

    def test_instance_invalid_template_path(
        self,
        ungrounded_template_data: UngroundedInstanceTemplateData,
    ):
        with pytest.raises(ValidationError):
            Instance.from_ungrounded(
                ungrounded_data=ungrounded_template_data,
                size=15,
                template_path=Path("invalid/path/to/template"),
            )

    def test_invalid_template_path_name(
        self, tmp_path: Path, ungrounded_template_data: UngroundedInstanceTemplateData
    ):
        template_file: Path = tmp_path / "invalid.rddl"
        template_file.touch()
        with pytest.raises(ValidationError) as exc_info:
            Instance.from_ungrounded(
                ungrounded_data=ungrounded_template_data,
                size=15,
                template_path=template_file,
            )

        assert exc_info.value.errors(
            include_context=False, include_input=False, include_url=False
        ) == [
            {
                "type": "value_error",
                "loc": ("template_path",),
                "msg": "Value error, Instance template must start with 'instance'.",
            }
        ]

    def test_invalid_template_path_suffix(
        self,
        tmp_path: Path,
        ungrounded_template_data: UngroundedInstanceTemplateData,
    ):
        template_file: Path = tmp_path / "instance.txt"
        template_file.touch()
        with pytest.raises(ValidationError) as exc_info:
            Instance.from_ungrounded(
                ungrounded_data=ungrounded_template_data,
                size=15,
                template_path=template_file,
            )

        assert exc_info.value.errors(
            include_context=False, include_input=False, include_url=False
        ) == [
            {
                "type": "value_error",
                "loc": ("template_path",),
                "msg": "Value error, Instance template must have file type '.rddl'.",
            }
        ]
