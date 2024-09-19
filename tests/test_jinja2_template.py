import pytest
from jinja2 import Template

from rddl_instance_generator.utils.templater import get_instance_template


def test_get_instance_template():
    # Test with a valid template path and file name
    template = get_instance_template(
        search_path="rddl_instance_generator", template_file="template.jinja2"
    )
    assert isinstance(template, Template)

    # Test with an invalid template path (expecting an exception)
    with pytest.raises(Exception):
        get_instance_template(
            search_path="invalid_path", template_file="template.jinja2"
        )

    # Test with an invalid template file name (expecting an exception)
    with pytest.raises(Exception):
        get_instance_template(
            search_path="rddl_instance_generator",
            template_file="invalid_template.jinja2",
        )
