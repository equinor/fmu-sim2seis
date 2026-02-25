from pathlib import Path

from fmu.sim2seis.utilities import read_yaml_file


def test_read_yaml_config(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(config_dir)
    conf = read_yaml_file(
        sim2seis_config_dir=config_dir,
        sim2seis_config_file=Path("sim2seis_config.yml"),
        global_config_dir=Path("../../fmuconfig/output"),
        global_config_file=Path("global_variables.yml"),
        parse_inputs=True,
    )

    # Make some random validations according to default settings
    assert conf.depth_conversion.max_depth > conf.depth_conversion.min_depth
    assert len(conf.seismic_fwd.stack_models.keys()) >= 1
    for key, value in conf.seismic_fwd.stack_models.items():
        assert value.is_file()
    assert conf.model_json_schema()


def test_read_comb_data_yaml_file(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(config_dir)
    config_file = Path("sim2seis_combined_config.yml")
    conf = read_yaml_file(
        sim2seis_config_file=config_file,
        sim2seis_config_dir=config_dir,
        global_config_dir=Path("../../fmuconfig/output"),
        global_config_file=Path("global_variables.yml"),
        parse_inputs=True,
    )
    # Make some random validations according to default settings
    assert conf.depth_conversion.min_depth < conf.depth_conversion.max_depth
    assert conf.webviz_map.attribute_error == 0.07


def test_read_seismic_fwd_only_config(monkeypatch, data_dir):
    """Test that a config with only seismic_fwd section is valid.

    Ref. issue #45: users should be able to work with one section at a time,
    starting with seismic_forward before adding depth_conversion, webviz_map
    and attribute_map_definition_file.
    """
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(config_dir)
    config_file = Path("sim2seis_seismic_fwd_only_config.yml")
    conf = read_yaml_file(
        sim2seis_config_file=config_file,
        sim2seis_config_dir=config_dir,
        parse_inputs=True,
    )
    # seismic_fwd section is present and stack_models are set
    assert conf.seismic_fwd is not None
    assert len(conf.seismic_fwd.stack_models) >= 1
    # Optional sections are absent (None) when not provided
    assert conf.depth_conversion is None
    assert conf.webviz_map is None
    assert conf.attribute_map_definition_file is None
