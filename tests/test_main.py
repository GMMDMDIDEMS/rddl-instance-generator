from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch
from click import BadParameter
import pytest
import typer
from typer.testing import CliRunner
import yaml

from rddl_instance_generator.main import (
    app,
    domain_callback,
    load_config,
    num_instances_callback,
    size_callback,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config():
    return {
        "types": [
            {"name": "object_1", "alias": "obj_1"},
            {"name": "object_2", "alias": "obj_2"},
        ]
    }


def test_valid_command(runner):
    result = runner.invoke(
        app,
        [
            "--domain-name",
            "Wildfire",
            "--num-instances",
            "1",
            "--size",
            "10",
            "--seed",
            "42",
        ],
    )
    assert result.exit_code == 0

    # test print_summary()
    assert "Instance Generation Summary" in result.stdout
    assert "Domain Name" in result.stdout
    assert "Number of Instances" in result.stdout
    assert "Number of Objects" in result.stdout
    assert "Seed" in result.stdout
    assert "Wildfire" in result.stdout
    assert "1" in result.stdout
    assert "10" in result.stdout
    assert "42" in result.stdout


def test_valid_command_short_option_names(runner):
    result = runner.invoke(
        app,
        [
            "-d",
            "Wildfire",
            "-n",
            "1",
            "-o",
            "10",
            "-s",
            "42",
        ],
    )
    assert result.exit_code == 0


def test_command_invalid_domain(runner):
    result = runner.invoke(
        app,
        [
            "--domain-name",
            "invalid_domain",
            "--num-instances",
            "5",
            "--size",
            "10",
        ],
    )
    assert result.exit_code != 0
    assert "Unsupported domain" in result.stdout


def test_domain_callback(monkeypatch):
    # Mock Path objects with the `name` attribute
    mock_domain = MagicMock(spec=Path)
    mock_domain.name = "domain"

    # Mock the iterdir method to return the mocked Path(s)
    monkeypatch.setattr(Path, "iterdir", lambda _: [mock_domain])
    assert domain_callback("domain") == "domain"

    with pytest.raises(typer.BadParameter):
        domain_callback("invalid_domain")


def test_num_instances_callback():
    assert num_instances_callback(5) == 5

    # Invalid number of instances
    with pytest.raises(typer.BadParameter):
        num_instances_callback(0)


def test_load_config(tmp_path):
    # tmp_path fixture will provide a temporary
    # directory unique to the test invocation
    config_data = {"key": "value"}
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    assert load_config(config_file) == config_data


def test_size_callback_invalid_config():
    invalid_yaml = """
        types:
        - name: object_1
        - name: object_2
        invalid: [ "unclosed_string
        """

    # intercepts any attempt by load_config to open a file, instead of trying to open
    # an actual file on disk, it uses the mock_open object, which returns the invalid_yaml
    # string as if it were the contents of dummy_config.yaml
    with patch("builtins.open", mock_open(read_data=invalid_yaml)), pytest.raises(
        yaml.YAMLError
    ):
        load_config(Path("dummy_config.yaml"))


def test_size_callback():
    ctx = MagicMock()
    ctx.params = {"domain_name": "test_domain"}

    # Mock the Path.exists() method to always return True
    with patch("pathlib.Path.exists", return_value=True):
        # Mock the load_config function
        with patch("rddl_instance_generator.main.load_config") as mock_load_config:
            # Set up the mock to return a config with 2 types
            mock_load_config.return_value = {
                "types": [
                    {"name": "type1", "alias": "t1"},
                    {"name": "type2", "alias": "t2"},
                ]
            }

            # Test with valid size
            assert size_callback(ctx, 3) == 3
            assert size_callback(ctx, 2) == 2

            # Test with invalid size (less than number of types)
            with pytest.raises(BadParameter):
                size_callback(ctx, 1)

    # Test when config file doesn't exist
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(AssertionError, match="config.yaml does not exist"):
            size_callback(ctx, 3)
