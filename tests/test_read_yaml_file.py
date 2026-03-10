import shutil
from pathlib import Path

import pytest
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


def test_read_yaml_pre_experiment_skips_filesystem_checks(
    monkeypatch, testdata, tmp_path
):
    """pre_experiment=True validates config-resident files but skips realization dirs.

    Files that live in sim2seis/model (stack_models, twt_model,
    attribute_map_definition_file) and sim2seis/input (WebvizMap grid files) are
    validated against the shared config directory.  Realization-specific directories
    (pem output, seismic cubes, etc.) are not checked.

    This mirrors the conditions at ERT's validate_pre_experiment stage: only the
    shared config and input files are present, none of the output/results directories
    have been created yet.
    """
    # Set up a bare config directory mirroring the shared sim2seis tree:
    #   <tmp>/sim2seis/model/   — YAML and XML model files
    #   <tmp>/sim2seis/input/pem/  — grid roff files (WebvizMap)
    config_dir = tmp_path / "sim2seis" / "model"
    config_dir.mkdir(parents=True)
    src_model_dir = testdata / "sim2seis" / "model"
    for f in src_model_dir.iterdir():
        shutil.copy2(f, config_dir / f.name)

    # Copy WebvizMap grid files so config-dir validation can find them.
    grid_dir = tmp_path / "sim2seis" / "input" / "pem"
    grid_dir.mkdir(parents=True)
    src_grid_dir = testdata / "sim2seis" / "input" / "pem"
    for f in src_grid_dir.iterdir():
        shutil.copy2(f, grid_dir / f.name)

    # Also copy the global variables file that is referenced by the config.
    fmuconfig_dir = tmp_path / "fmuconfig" / "output"
    fmuconfig_dir.mkdir(parents=True)
    src_fmu_dir = testdata / "fmuconfig" / "output"
    for f in src_fmu_dir.iterdir():
        shutil.copy2(f, fmuconfig_dir / f.name)

    monkeypatch.chdir(tmp_path)

    # Without pre_experiment=True this must raise a pydantic ValidationError
    # because the realization output directories (e.g. pem_output_dir) do not
    # exist under tmp_path.
    with pytest.raises(ValidationError, match="is not an existing directory"):
        read_yaml_file(
            sim2seis_config_dir=config_dir,
            sim2seis_config_file=Path("sim2seis_combined_config.yml"),
            global_config_dir=Path("fmuconfig/output"),
            global_config_file=Path("global_variables.yml"),
            parse_inputs=True,
            pre_experiment=False,
        )

    # With pre_experiment=True, config-resident files are still validated but
    # realization-specific directory checks are skipped.
    conf = read_yaml_file(
        sim2seis_config_dir=config_dir,
        sim2seis_config_file=Path("sim2seis_combined_config.yml"),
        global_config_dir=Path("fmuconfig/output"),
        global_config_file=Path("global_variables.yml"),
        parse_inputs=True,
        pre_experiment=True,
    )

    # Non-filesystem validators must still have run.
    assert conf.depth_conversion.max_depth > conf.depth_conversion.min_depth
    # stack_models are resolved to absolute paths against config_dir.
    assert len(conf.seismic_fwd.stack_models) >= 1
    for path in conf.seismic_fwd.stack_models.values():
        assert path.is_absolute()
        assert path.is_file()
    # twt_model is resolved to an absolute path against config_dir.
    assert conf.seismic_fwd.twt_model.is_absolute()
    assert conf.seismic_fwd.twt_model.is_file()
    # attribute_map_definition_file must also be present.
    resolved_attr = config_dir / conf.attribute_map_definition_file
    assert resolved_attr.is_file() or conf.attribute_map_definition_file.is_file()
