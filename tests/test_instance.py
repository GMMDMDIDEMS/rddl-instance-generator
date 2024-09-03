from pathlib import Path
from pydantic import ValidationError
import pytest
from rddl_instance_generator.instance import Instance, InstanceGenerator


def test_instance_valid():
    instance = Instance(
        identifier="5_10",
        size=10,
        template_path=None,
        object_lengths={"object1": 5, "object2": 10},
    )
    assert isinstance(instance.identifier, str)
    assert instance.identifier == "5_10"
    assert instance.size == 10
    assert instance.template_path is None
    assert instance.object_lengths == {"object1": 5, "object2": 10}


def test_instance_with_valid_template_path(tmp_path: Path):
    template_file = tmp_path / "instance_template.rddl"
    template_file.touch()
    instance = Instance(
        identifier="2_3",
        size=5,
        template_path=template_file,
        object_lengths={"object_1": 2, "type2": 3},
    )
    assert instance.template_path == template_file


def test_instance_invalid_size():
    # invalid size: size must be greater than 0
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        Instance(
            identifier="5_10",
            size=0,
            template_path=None,
            object_lengths={"object1": 5, "object2": 10},
        )


def test_instance_invalid_template_path():
    with pytest.raises(ValidationError):
        Instance(
            identifier="5_10",
            size=10,
            template_path=Path("invalid/path/to/template"),
            object_lengths={"object1": 5, "object2": 10},
        )


def test_instance_object_lengths_empty():
    with pytest.raises(ValidationError, match="object_length dict must not be empty."):
        Instance(
            identifier="test_instance",
            size=5,
            object_lengths={},
        )


def test_instance_object_lengths_negative():
    with pytest.raises(ValidationError, match="Value must be greater than 0."):
        Instance(
            identifier="test_instance",
            size=5,
            object_lengths={"object_1": 0},
        )


def test_instance_invalid_identifier():
    with pytest.raises(
        ValidationError, match="String should have at least 3 characters"
    ):
        Instance(
            identifier="id",
            size=5,
            object_lengths={"object_1": 1},
        )


def test_instance_invalid_object_length_key_type():
    with pytest.raises(ValueError, match="Value error, '1' must be of type 'str'"):
        Instance(
            identifier="valid_id",
            size=5,
            object_lengths={1: 1},  # type: ignore [pylance]
        )


def test_instance_invalid_object_length_value():
    with pytest.raises(
        ValueError, match="Value error, 'invalid_value' must be of type 'int'."
    ):
        Instance(
            identifier="valid_id",
            size=5,
            object_lengths={"object_1": "invalid_value"},  # type: ignore [pylance]
        )


def test_instance_undefined_identifier():
    with pytest.raises(ValueError, match="Field required"):
        Instance(  # type: ignore [pylance]
            size=5,
            object_lengths={"object_1": 2, "type2": 3},
        )


def test_instance_undefined_size():
    with pytest.raises(ValueError, match="Field required"):
        Instance(  # type: ignore [pylance]
            identifier="2_3",
            object_lengths={"object_1": 2, "type2": 3},
        )


def test_instance_undefined_object_length():
    with pytest.raises(
        ValueError, match="Value error, object_length dict must not be empty."
    ):
        Instance(  # type: ignore [pylance]
            identifier="2_3",
            size=5,
        )


def test_instance_valid_size():
    instance = Instance(
        identifier="2_3",
        size=1,
        object_lengths={"object_1": 2, "type2": 3},
    )
    assert instance.size == 1


def test_template_folder_path(tmp_path: Path):
    template_file: Path = tmp_path / "instance_2_3.rddl"
    template_file.touch()
    instance = Instance(
        identifier="2_3",
        size=5,
        template_path=template_file,
        object_lengths={"object_1": 2, "type2": 3},
    )
    assert instance.template_path.name.startswith("instance_")
    assert instance.template_path.suffix == ".rddl"
    assert instance.identifier in instance.template_path.name


def test_invalid_template_path_name(tmp_path: Path):
    template_file: Path = tmp_path / "invalid.rddl"
    template_file.touch()
    with pytest.raises(
        ValueError, match="Instance template must start with 'instance'."
    ):
        Instance(
            identifier="2_3",
            size=5,
            template_path=template_file,
            object_lengths={"object_1": 2, "type2": 3},
        )


def test_invalid_template_path_suffix(tmp_path: Path):
    template_file: Path = tmp_path / "instance.txt"
    template_file.touch()
    with pytest.raises(
        ValueError, match="Instance template must have file type '.rddl'."
    ):
        Instance(
            identifier="2_3",
            size=5,
            template_path=template_file,
            object_lengths={"object_1": 2, "type2": 3},
        )


def test_instance_generator_template_folder(instance_generator: InstanceGenerator):
    path: Path = instance_generator.template_folder_path
