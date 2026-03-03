import shutil
from pathlib import Path

import pytest

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


def test_read_yaml_pre_experiment_skips_filesystem_checks(
    monkeypatch, testdata, tmp_path
):
    """pre_experiment=True must succeed even when realization directories don't exist.

    This mirrors the conditions at ERT's validate_pre_experiment stage: only the
    model config files are present, none of the output/results directories have
    been created yet.
    """
    # Set up a bare config directory with only the model YAML files and no
    # realization subdirectories (pem output, seismic cubes, maps, …).

    config_dir = tmp_path / "sim2seis" / "model"
    config_dir.mkdir(parents=True)
    src_model_dir = testdata / "sim2seis" / "model"
    for f in src_model_dir.iterdir():
        shutil.copy2(f, config_dir / f.name)

    # Also copy the global variables file that is referenced by the config.
    fmuconfig_dir = tmp_path / "fmuconfig" / "output"
    fmuconfig_dir.mkdir(parents=True)
    src_fmu_dir = testdata / "fmuconfig" / "output"
    for f in src_fmu_dir.iterdir():
        shutil.copy2(f, fmuconfig_dir / f.name)

    monkeypatch.chdir(config_dir)

    # Without pre_experiment=True this would fail because directories such as
    # ../../sim2seis/output/pem do not exist under tmp_path.
    with pytest.raises(Exception):
        read_yaml_file(
            sim2seis_config_dir=config_dir,
            sim2seis_config_file=Path("sim2seis_config.yml"),
            global_config_dir=Path("../../fmuconfig/output"),
            global_config_file=Path("global_variables.yml"),
            parse_inputs=True,
            pre_experiment=False,
        )

    # With pre_experiment=True all filesystem checks are bypassed; only
    # non-path parameter validation runs.
    conf = read_yaml_file(
        sim2seis_config_dir=config_dir,
        sim2seis_config_file=Path("sim2seis_config.yml"),
        global_config_dir=Path("../../fmuconfig/output"),
        global_config_file=Path("global_variables.yml"),
        parse_inputs=True,
        pre_experiment=True,
    )

    # Non-filesystem validators must still have run.
    assert conf.depth_conversion.max_depth > conf.depth_conversion.min_depth
    assert len(conf.seismic_fwd.stack_models) >= 1
