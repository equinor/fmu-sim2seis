from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import xtgeo

from fmu.sim2seis.utilities import (
    export_with_dataio,
    start_s2s_run_log,
    stop_s2s_run_log,
)
from fmu.sim2seis.utilities.sim2seis_class_definitions import (
    SeismicAttribute,
    SeismicName,
)


@pytest.mark.parametrize("is_observed", [False, True])
def test_attribute_export_logs_sampled_table_counts(tmp_path, capsys, is_observed):
    output = tmp_path / "output"
    output.mkdir()
    config = MagicMock()
    config.paths.fmu_rootpath = tmp_path
    config.paths.output_dir_modelled_data = output
    config.paths.output_dir_observed_data = output

    attr = Mock(spec=SeismicAttribute)
    attr.zone = "Valysar"
    attr.position = "top"
    attr.window = "reservoir"
    attr.calc_types = ["rms", "mean"]
    attr.value = [Mock(spec=xtgeo.RegularSurface), Mock(spec=xtgeo.RegularSurface)]
    attr.error = None
    attr.window_length = 20.0
    attr.from_cube = Mock()
    attr.from_cube.cube_name = SeismicName(
        process="seismic",
        attribute="amplitude",
        domain="depth",
        stack="near",
        date="20200701_20180101",
    )
    attr.from_cube.monitor_date = "20200701"
    attr.from_cube.base_date = "20180101"

    frames = [
        pd.DataFrame({"OBS": [1.0, 2.0], "OBS_ERROR": [0.1, 0.2], "REGION": [1, 2]}),
        pd.DataFrame({"OBS": [], "OBS_ERROR": [], "REGION": []}),
    ]
    zone = Mock()
    zone.codes = {1: "Valysar"}
    exporters = []
    for name in ("rms", "mean"):
        exporter = Mock()
        exporter.export.return_value = str(tmp_path / f"{name}.yml")
        exporters.append(exporter)

    start_s2s_run_log()
    try:
        with (
            patch.object(
                export_with_dataio,
                "_get_grid_info",
                return_value=(Mock(), zone, Mock()),
            ),
            patch.object(
                export_with_dataio.dataio, "ExportData", side_effect=exporters
            ),
            patch.object(
                export_with_dataio.tools,
                "sample_attributes_for_sim2seis",
                side_effect=frames,
            ),
        ):
            export_with_dataio.attribute_export(config, [attr], is_observed=is_observed)
    finally:
        stop_s2s_run_log()

    log = capsys.readouterr().out
    identity = "cube=seismic--amplitude_near_depth--20200701_20180101, window=reservoir"
    assert (
        f"{identity}, calculation=rms, zone=Valysar, position=top: "
        "2 valid grid-sampled points" in log
    )
    assert (
        f"{identity}, calculation=mean, zone=Valysar, position=top: "
        "0 valid grid-sampled points" in log
    )

    for name, frame, exporter in zip(("rms", "mean"), frames, exporters):
        assert exporter.export.call_args_list[1].args[0] is frame
        assert len(pd.read_parquet(output / f"{name}.parquet")) == len(frame)
        assert len((output / f"{name}.txt").read_text().splitlines()) == len(frame)
