from unittest.mock import Mock, patch

import pytest
import xtgeo

from fmu.sim2seis.utilities import SeismicName, SingleSeismic
from fmu.sim2seis.utilities.interval_parser import populate_seismic_attributes


@pytest.fixture
def real_yaml_config():
    return {
        "global": {
            "gridhorizon_path": "../../share/observations/maps",
            "attributes": ["rms", "mean", "min"],
            "scale_factor": 1.0,
            "workflow": "rms/sim2seis",
            "access_ssdl": {"rep_include": False, "access_level": "asset"},
            "export_subfolder": "prm",
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "relai_depth": {
                "cube_prefix": "seismic--relai_depth--",
                "filename_tag_prefix": "relai_depth",
                "seismic_path": "../../share/observations/seismic",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
                    "volantis": {
                        "top_horizon": "topvolantis",
                        "bottom_horizon": "basevolantis",
                        "top_surface_shift": -5,
                        "base_surface_shift": 10,
                        "rms": {
                            "top_horizon": "topvolantis",
                            "bottom_horizon": "basevolantis",
                            "top_surface_shift": -15,
                            "scale_factor": 1.02,
                        },
                    }
                },
            },
            "amplitude_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "../../share/observations/seismic",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
                    "volantis": {
                        "top_horizon": "topvolantis",
                        "bottom_horizon": "basevolantis",
                        "top_surface_shift": -17,
                        "base_surface_shift": -2,
                        "mean": {
                            "top_horizon": "topvolantis",
                            "bottom_horizon": "basevolantis",
                            "top_surface_shift": -10,
                            "base_surface_shift": -5,
                        },
                        "min": {"scale_factor": 1.5},
                    }
                },
            },
        },
    }


@pytest.fixture
def mock_surfaces():
    top_surface = Mock(spec=xtgeo.RegularSurface)
    base_surface = Mock(spec=xtgeo.RegularSurface)
    return {
        "topvolantis--depth.gri": top_surface,
        "basevolantis--depth.gri": base_surface,
    }


@pytest.fixture
def mock_cubes():
    relai_seismic = Mock(spec=SingleSeismic)
    amplitude_seismic = Mock(spec=SingleSeismic)
    return {
        SeismicName(
            process="seismic", attribute="relai", domain="depth", date="20200101"
        ): relai_seismic,
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): amplitude_seismic,
    }


def test_basic_attribute_creation(real_yaml_config, mock_surfaces, mock_cubes):
    mock_surface = Mock(spec=xtgeo.RegularSurface)
    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        return_value=mock_surface,
    ):
        result = populate_seismic_attributes(
            config=real_yaml_config, cubes=mock_cubes, surfaces=mock_surfaces
        )

        # There are 3 global attributes and 2 cubes.
        # We get 2 and not 3 attributes from the relai_depth cube because 'mean' and
        # 'min' have the exact same interval settings. We get 3 attributes from the
        # amplitude_depth cube because all attributes have different interval settings.
        assert len(result) == 5
