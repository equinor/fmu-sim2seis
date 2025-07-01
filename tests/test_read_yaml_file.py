from pathlib import Path

from fmu.sim2seis.utilities import read_yaml_file


def test_read_yaml_config(monkeypatch, data_dir):
    start_dir = data_dir / r"rms/model"
    monkeypatch.chdir(start_dir)
    rel_path_conf = Path("../../sim2seis/model")
    config_file = Path("sim2seis_config.yml")
    conf = read_yaml_file(
        file_name=rel_path_conf / config_file,
        start_dir=start_dir,
        update_with_global=True,
        parse_inputs=True
    )

    # Make some random validations according to default settings
    assert not conf.flowsim_is_prediction
    assert conf.depth_conversion.max_depth > conf.depth_conversion.min_depth
    assert len(conf.seismic_fwd.stack_models.keys()) >= 1
    for key, value in conf.seismic_fwd.stack_models.items():
        assert value.is_file()
    assert conf.model_json_schema()


def test_read_obs_data_yaml_file(monkeypatch, data_dir):
    start_dir = data_dir / r"rms/model"
    monkeypatch.chdir(start_dir)
    rel_path_conf = Path("../../sim2seis/model")
    config_file = Path("obs_data_config.yml")
    conf = read_yaml_file(
        file_name=rel_path_conf / config_file,
        start_dir=start_dir,
        update_with_global=True,
        parse_inputs=True
    )
    # Make some random validations according to default settings
    assert conf.depth_conversion.min_depth < conf.depth_conversion.max_depth
    assert conf.webviz_map.attribute_error == 0.07
