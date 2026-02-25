import shutil
from pathlib import Path
from typing import ClassVar

import pytest

from fmu.sim2seis.utilities import read_yaml_file
from fmu.sim2seis.utilities.sim2seis_config_validation import (
    DepthConvertConfig,
    Sim2SeisPaths,
)


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


class TestHorizonFileValidation:
    """Tests for validation that horizon files exist on disk."""

    _BASE_DATA: ClassVar[dict] = {
        "depth_suffix": "--depth.gri",
        "time_suffix": "--time.gri",
        "min_depth": 1500,
        "max_depth": 2000,
        "z_inc": 4,
        "min_time": 1500,
        "max_time": 2000,
        "t_inc": 4,
    }

    def _make_paths(self, time_dir: Path, depth_dir: Path) -> Sim2SeisPaths:
        """Build a minimal Sim2SeisPaths with the given horizon directories."""
        paths = Sim2SeisPaths.model_construct()
        paths.time_horizon_dir = time_dir
        paths.depth_horizon_dir = depth_dir
        return paths

    def _validate(self, horizon_names: list[str], paths: Sim2SeisPaths) -> None:
        """Run model_validate on DepthConvertConfig, injecting *paths* via context."""
        DepthConvertConfig.model_validate(
            {**self._BASE_DATA, "horizon_names": horizon_names},
            context={"paths": paths},
        )

    def test_all_horizon_files_present_passes(self, data_dir):
        """All four horizon names used in the test YAML have matching files."""
        horizon_dir = data_dir / "share" / "results" / "maps"
        paths = self._make_paths(horizon_dir, horizon_dir)
        # Should not raise
        self._validate(["MSL", "TopVolantis", "BaseVolantis", "BaseVelmodel"], paths)

    def test_missing_time_horizon_raises_value_error(self, data_dir, tmp_path):
        """A horizon with a missing time file raises a descriptive ValueError."""
        horizon_dir = data_dir / "share" / "results" / "maps"
        time_dir = tmp_path / "time_maps"
        time_dir.mkdir()
        # Copy all existing files except the time variant of 'TopVolantis'
        for f in horizon_dir.iterdir():
            if f.name != "topvolantis--time.gri":
                (time_dir / f.name).write_bytes(f.read_bytes())

        paths = self._make_paths(time_dir, horizon_dir)

        with pytest.raises(ValueError, match=r"topvolantis--time\.gri"):
            self._validate(["TopVolantis"], paths)

    def test_missing_depth_horizon_raises_value_error(self, data_dir, tmp_path):
        """A horizon with a missing depth file raises a descriptive ValueError."""
        horizon_dir = data_dir / "share" / "results" / "maps"
        depth_dir = tmp_path / "depth_maps"
        depth_dir.mkdir()
        # Copy all existing files except the depth variant of 'BaseVolantis'
        for f in horizon_dir.iterdir():
            if f.name != "basevolantis--depth.gri":
                (depth_dir / f.name).write_bytes(f.read_bytes())

        paths = self._make_paths(horizon_dir, depth_dir)

        with pytest.raises(ValueError, match=r"basevolantis--depth\.gri"):
            self._validate(["BaseVolantis"], paths)

    def test_multiple_missing_horizons_reported_together(self, tmp_path):
        """All missing horizon files are reported in a single ValueError."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        paths = self._make_paths(empty_dir, empty_dir)

        with pytest.raises(ValueError) as exc_info:
            self._validate(["HorizonA", "HorizonB"], paths)

        error_message = str(exc_info.value)
        assert "horizona--time.gri" in error_message
        assert "horizona--depth.gri" in error_message
        assert "horizonb--time.gri" in error_message
        assert "horizonb--depth.gri" in error_message

    def test_no_context_skips_check(self):
        """When no validation context is provided the file check is skipped."""
        # model_validate without context — directories don't exist, but no error raised
        DepthConvertConfig.model_validate(
            {**self._BASE_DATA, "horizon_names": ["NonExistentHorizon"]}
        )

    def test_horizon_validation_triggered_via_read_yaml_file(
        self, monkeypatch, data_dir, tmp_path
    ):
        """Horizon file validation is triggered during full YAML parsing."""
        config_dir = data_dir / "sim2seis" / "model"
        monkeypatch.chdir(config_dir)

        # Build a temporary maps directory that is missing one horizon file
        maps_dir = tmp_path / "maps"
        shutil.copytree(data_dir / "share" / "results" / "maps", maps_dir)
        (maps_dir / "msl--time.gri").unlink()

        # Patch Sim2SeisPaths so that time_horizon_dir and depth_horizon_dir point
        # to our incomplete maps directory, while keeping other paths valid.
        original_validate = Sim2SeisPaths.model_validate

        def patched_validate(data, **kwargs):
            obj = original_validate(data, **kwargs)
            obj.time_horizon_dir = maps_dir
            obj.depth_horizon_dir = maps_dir
            return obj

        monkeypatch.setattr(Sim2SeisPaths, "model_validate", patched_validate)

        with pytest.raises(ValueError, match=r"msl--time\.gri"):
            read_yaml_file(
                sim2seis_config_dir=config_dir,
                sim2seis_config_file=Path("sim2seis_config.yml"),
                global_config_dir=Path("../../fmuconfig/output"),
                global_config_file=Path("global_variables.yml"),
                parse_inputs=True,
            )
