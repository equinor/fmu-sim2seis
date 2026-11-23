import pytest
import yaml

from fmu.sim2seis.utilities.editor_schema import interval_definition_schema
from fmu.sim2seis.utilities.interval_parser import RootConfig
from fmu.sim2seis.utilities.sim2seis_config_validation import Sim2SeisPaths


def test_interval_schema_matches_yaml_layout(data_dir):
    """The JSON schema must describe the YAML file as written, including the
    per-attribute override blocks that live next to the window fields."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = interval_definition_schema()

    assert set(schema["properties"]) == {"global", "cubes"}
    assert schema["$defs"]["GlobalConfig"]["properties"]["gridhorizon_path"][
        "default"
    ] == str(Sim2SeisPaths.model_fields["depth_horizon_dir"].default)
    assert (
        schema["$defs"]["GlobalConfig"]["properties"]["surface_postfix"]["default"]
        == "--depth.gri"
    )
    assert (
        schema["$defs"]["GlobalConfig"]["properties"]["scale_factor"]["default"] == 1.0
    )
    for model in ("GlobalConfig", "CubeConfig", "WindowSettings"):
        assert schema["$defs"][model]["properties"]["error"]["$ref"] == (
            "#/$defs/ErrorConfig"
        )
    assert "default" not in schema["$defs"]["ErrorConfig"]["properties"]["minimum"]
    window = schema["$defs"]["WindowSettings"]
    assert "attribute_overrides" not in window["properties"]
    assert window["additionalProperties"] == {"$ref": "#/$defs/AttributeOverride"}
    assert set(window["propertyNames"]["enum"]) >= {"rms", "top_horizon"}
    override = schema["$defs"]["AttributeOverride"]
    assert set(override["properties"]).isdisjoint({"zone", "position", "error"})
    assert "anyOf" not in override["properties"]["window_length"]
    # optional fields are plain properties, not anyOf-with-null
    assert "anyOf" not in window["properties"]["bottom_horizon"]

    example = yaml.safe_load(
        (data_dir / "sim2seis" / "model" / "data_intervals_drogon.yml").read_text()
    )
    jsonschema.validate(example, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {"global": example["global"], "cubes": [{"cube_prefix": "x"}]},
            schema,
        )


def test_interval_schema_observation_error_is_optional(data_dir):
    """The form hides observation error settings behind checkboxes, so neither
    the editor schema nor ``RootConfig`` may require them."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = interval_definition_schema()
    definitions = schema["$defs"]

    assert {"error", "error_path"}.isdisjoint(
        definitions["GlobalConfig"].get("required", [])
    )
    for model in ("CubeConfig", "WindowSettings"):
        assert "error" not in definitions[model].get("required", [])

    example = yaml.safe_load(
        (data_dir / "sim2seis" / "model" / "data_intervals_drogon.yml").read_text()
    )
    example["global"].pop("error", None)
    example["global"].pop("error_path", None)
    for cube in example["cubes"]:
        cube.pop("error", None)
        for window in cube["windows"].values():
            window.pop("error", None)

    jsonschema.validate(example, schema)
    config = RootConfig.model_validate(example, context={"validate_paths": False})
    assert config.global_config.error is None
    assert config.global_config.error_path is None
    assert all(cube.error is None for cube in config.cubes)
    assert all(
        window.error is None
        for cube in config.cubes
        for window in cube.windows.values()
    )
