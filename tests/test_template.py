from typing import List

from pydantic import ValidationError
import pytest
from rddl_instance_generator.domain import ObjectType
from rddl_instance_generator.helper.templater import UngroundedInstanceTemplateData


class TestUngroundedInstanceTemplateData:
    def test_domain_alias(
        self, ungrounded_template_data: UngroundedInstanceTemplateData
    ):
        assert ungrounded_template_data.domain_alias == "test_domain"

    def test_identifier(self, ungrounded_template_data: UngroundedInstanceTemplateData):
        assert ungrounded_template_data.identifier == "5_10"

    def test_types(
        self,
        ungrounded_template_data: UngroundedInstanceTemplateData,
        domain_types: List[ObjectType],
    ):
        assert ungrounded_template_data.types == domain_types

    def test_object_lengths(
        self,
        ungrounded_template_data: UngroundedInstanceTemplateData,
    ):
        assert ungrounded_template_data.object_lengths == {
            "object_1": 5,
            "object_2": 10,
        }

    def test_instance_object_lengths_empty(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(
            ValidationError, match="Value error, object_lengths dict must not be empty."
        ):
            UngroundedInstanceTemplateData(
                domain_alias="test_domain",
                identifier="5_10",
                types=domain_types,
                object_lengths={},
            )

    def test_invalid_identifier(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(
            ValidationError, match="String should have at least 1 character"
        ):
            UngroundedInstanceTemplateData(
                identifier="",
                domain_alias="test_domain",
                types=domain_types,
                object_lengths={
                    "object_1": 5,
                    "object_2": 10,
                },
            )

    def test_invalid_domain_alias(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(
            ValidationError, match="String should have at least 3 characters"
        ):
            UngroundedInstanceTemplateData(
                identifier="id",
                domain_alias="",
                types=domain_types,
                object_lengths={
                    "object_1": 5,
                    "object_2": 10,
                },
            )

    def test_object_lengths_zero(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(
            ValidationError,
            match="Value error, Value for key 'object_1' must be greater than 0, but got '0'.",
        ):
            UngroundedInstanceTemplateData(
                identifier="id",
                domain_alias="test_domain",
                types=domain_types,
                object_lengths={
                    "object_1": 0,
                    "object_2": 10,
                },
            )

    def test_object_lengths_invalid_value_type(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(
            ValidationError,
            match="Value error, Value for key 'object_2' must be of type 'int', but got 'str'.",
        ):
            UngroundedInstanceTemplateData(
                identifier="id",
                domain_alias="test_domain",
                types=domain_types,
                object_lengths={
                    "object_1": 5,
                    "object_2": "10",  # type: ignore [pylance]
                },
            )

    def test_invalid_object_length_key_type(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(
            ValidationError,
            match="Value error, Key '2' must be of type 'str', but got 'int'.",
        ):
            UngroundedInstanceTemplateData(
                identifier="id",
                domain_alias="test_domain",
                types=domain_types,
                object_lengths={
                    "object_1": 5,
                    2: 10,  # type: ignore [pylance]
                },
            )

    def test_not_matching_types(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(
            ValueError,
            match=r"Value error, Mismatch between defined objects: \['object_1', 'object_2'\] != \['object_1', 'object_3'\]",
        ):
            UngroundedInstanceTemplateData(
                identifier="id",
                domain_alias="test_domain",
                types=domain_types,
                object_lengths={
                    "object_1": 5,
                    "object_3": 10,
                },
            )

    def test_different_number_of_types(
        self,
        domain_types: List[ObjectType],
    ):
        with pytest.raises(ValidationError) as exc_info:
            UngroundedInstanceTemplateData(
                identifier="id",
                domain_alias="test_domain",
                types=domain_types,
                object_lengths={
                    "object_1": 5,
                    "object_2": 5,
                    "object_3": 5,
                },
            )

        assert exc_info.value.errors(
            include_context=False, include_input=False, include_url=False
        ) == [
            {
                "type": "value_error",
                "loc": (),
                "msg": "Value error, Mismatch between 'types' and 'object_lengths'. Expected the same number of entries, but got 2 types (['object_1', 'object_2']) and 3 object lengths (['object_1', 'object_2', 'object_3']).",
            }
        ]
