from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from fmu.sim2seis.utilities import read_yaml_file


def test_read_yaml_config(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(data_dir)
    conf = read_yaml_file(
        sim2seis_config_dir=config_dir,
        sim2seis_config_file=Path("sim2seis_combined_config.yml"),
        global_config_dir=Path("fmuconfig/output"),
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
    monkeypatch.chdir(data_dir)
    config_file = Path("sim2seis_combined_config.yml")
    conf = read_yaml_file(
        sim2seis_config_file=config_file,
        sim2seis_config_dir=config_dir,
        global_config_dir=Path("fmuconfig/output"),
        global_config_file=Path("global_variables.yml"),
        parse_inputs=True,
    )
    # Make some random validations according to default settings
    assert conf.depth_conversion.min_depth < conf.depth_conversion.max_depth
    assert conf.webviz_map.attribute_error == 0.07


def test_attribute_error_minimum(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    sim2seis_config_file_name = Path("sim2seis_combined_config.yml")
    monkeypatch.chdir(data_dir)

    with open(config_dir / sim2seis_config_file_name) as fin:
        data = yaml.safe_load(fin)
        # Modify the config file: add `test_run = True`
        data["webviz_map"]["attribute_error_minimum"] = -0.005
    fout_name = config_dir / Path(
        sim2seis_config_file_name.stem + "_test" + sim2seis_config_file_name.suffix
    )
    with open(fout_name, "w") as fout:
        yaml.safe_dump(data, fout)
    with pytest.raises(ValidationError):
        _ = read_yaml_file(
            sim2seis_config_file=fout_name,
            sim2seis_config_dir=config_dir,
            global_config_dir=Path("fmuconfig/output"),
            global_config_file=Path("global_variables.yml"),
            parse_inputs=True,
        )
    conf = read_yaml_file(
        sim2seis_config_file=sim2seis_config_file_name,
        sim2seis_config_dir=config_dir,
        global_config_dir=Path("fmuconfig/output"),
        global_config_file=Path("global_variables.yml"),
        parse_inputs=True,
    )
    assert conf.webviz_map.attribute_error_minimum == 0.005
