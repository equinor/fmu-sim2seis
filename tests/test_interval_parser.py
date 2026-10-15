import re
import warnings
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import xtgeo
from pydantic import ValidationError

from fmu.sim2seis.utilities import (
    SeismicAttribute,
    SeismicName,
    SingleSeismic,
    export_with_dataio,
)
from fmu.sim2seis.utilities.interval_parser import (
    CubeConfig,
    GlobalConfig,
    RootConfig,
    WindowSettings,
    _get_matching_cubes,
    _group_attributes_by_interval,
    _resolve_error_block,
    populate_seismic_attributes,
)
from fmu.sim2seis.utilities.sim2seis_class_definitions import ErrorConfig


@pytest.fixture
def patch_directory_validation():
    """Patch Path.is_dir() to allow non-existent directories in tests"""
    with patch.object(Path, "is_dir", return_value=True):
        yield


@pytest.fixture
def create_chainable_surface():
    """Create a mock surface that supports chained additions."""

    def _create():
        surface = Mock(spec=xtgeo.RegularSurface)
        intermediate = Mock(spec=xtgeo.RegularSurface)
        final = Mock(spec=xtgeo.RegularSurface)

        surface.__add__ = Mock(return_value=intermediate)
        intermediate.__add__ = Mock(return_value=final)

        return surface, intermediate, final

    return _create


@pytest.fixture
def real_yaml_config(tmp_path):
    grid_path = tmp_path / "maps"
    grid_path.mkdir()
    return {
        "global": {
            "gridhorizon_path": f"{grid_path}",
            "attributes": ["rms", "mean", "min"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "relai_depth": {
                "cube_prefix": "seismic--relai_depth--",
                "windows": {
                    "volantis": {
                        "top_horizon": "topvolantis",
                        "bottom_horizon": "basevolantis",
                        "top_surface_shift": -5,
                        "bottom_surface_shift": 10,
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
                "windows": {
                    "volantis": {
                        "top_horizon": "topvolantis",
                        "bottom_horizon": "basevolantis",
                        "top_surface_shift": -17,
                        "bottom_surface_shift": -2,
                        "mean": {
                            "top_horizon": "topvolantis",
                            "bottom_horizon": "basevolantis",
                            "top_surface_shift": -10,
                            "bottom_surface_shift": -5,
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


@pytest.fixture
def patch_surface_loader():
    """
    Patches xtgeo.surface_from_file to return a generic mock.
    """
    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        return_value=Mock(spec=xtgeo.RegularSurface),
    ) as mock:
        yield mock


def test_basic_attribute_creation(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
):
    result = populate_seismic_attributes(
        config=real_yaml_config, cubes=mock_cubes, surfaces=mock_surfaces
    )

    # There are 3 global attributes and 2 cubes.
    # We get 2 and not 3 attributes from the relai_depth cube
    # because 'mean' and 'min' have the exact same interval settings.
    # We get 3 attributes from the amplitude_depth cube because all
    # attributes have different interval settings.
    assert len(result) == 5


def test_identical_interval_attributes_are_grouped(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
):
    result = populate_seismic_attributes(
        config=real_yaml_config, cubes=mock_cubes, surfaces=mock_surfaces
    )

    relai_cube_name = next(key for key in mock_cubes if key.attribute == "relai")
    relai_cube = mock_cubes[relai_cube_name]
    grouped_attr = [
        attr
        for attr in result
        if attr.from_cube is relai_cube and sorted(attr.calc_types) == ["mean", "min"]
    ]

    assert len(grouped_attr) == 1
    assert grouped_attr[0].scale_factor == 1.0


def test_window_length_creates_virtual_bottom_surface(
    recwarn,
    patch_directory_validation,
    create_chainable_surface,
):
    """
    Tests that if window length is provided, then the bottom_horizon is ignored,
    and a warning is emitted.
    """
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "window_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "alpha": {
                        "top_horizon": "topalpha",
                        "bottom_horizon": "basealpha",
                        "window_length": 25.0,
                    }
                },
            }
        },
    }
    top_surface, intermediate, final = create_chainable_surface()
    surfaces = {}
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): Mock(spec=SingleSeismic)
    }

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        return_value=top_surface,
    ) as surface_from_file:
        result = populate_seismic_attributes(
            config=config, cubes=cubes, surfaces=surfaces
        )

    # Assert that code emits a warning, ignoring one config option
    assert len(recwarn) == 1
    assert (
        "Both 'bottom_horizon' ('basealpha') and 'window_length' (25.0) are specified."
        in str(recwarn[0].message)
    )

    assert surface_from_file.call_args[0][0] == "/grids/topalpha--depth.gri"
    top_surface.__add__.assert_called_once_with(0.0)
    intermediate.__add__.assert_called_once_with(25.0)
    assert result[0].bottom_surface is final


def test_missing_surfaces_are_loaded_from_disk(patch_directory_validation):
    """
    Tests that if the surfaces are not provided to `populate_seismic_attributes`
    then they are loaded from disk as
    `gridhorizon_path/{top(bottom)_horizon}{surface_postfix}`
    """
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "beta": {
                        "top_horizon": "topbeta",
                        "bottom_horizon": "basebeta",
                    }
                },
            }
        },
    }
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): Mock(spec=SingleSeismic)
    }
    surfaces: dict[str, xtgeo.RegularSurface] = {}
    loaded_surfaces = {
        "topbeta": Mock(),
        "basebeta": Mock(),
    }

    def surface_loader(path: str):
        if path.endswith("topbeta--depth.gri"):
            return loaded_surfaces["topbeta"]
        if path.endswith("basebeta--depth.gri"):
            return loaded_surfaces["basebeta"]
        raise AssertionError(f"Unexpected surface request: {path}")

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=surface_loader,
    ) as surface_from_file:
        result = populate_seismic_attributes(
            config=config, cubes=cubes, surfaces=surfaces
        )

    assert len(result) == 1
    paths = [args[0][0] for args in surface_from_file.call_args_list]
    assert paths == [
        "/grids/topbeta--depth.gri",
        "/grids/basebeta--depth.gri",
    ]
    assert loaded_surfaces["topbeta"].name == "topbeta"
    assert loaded_surfaces["basebeta"].name == "basebeta"


def test_populate_raises_when_no_matching_cubes(
    real_yaml_config, mock_surfaces, patch_directory_validation
):
    """
    Should maybe be a more specific error message?
    """
    with pytest.raises(ValueError, match="No attributes generated"):
        populate_seismic_attributes(
            config=real_yaml_config, cubes={}, surfaces=mock_surfaces
        )


def test_attribute_specific_scale_factor_override(
    real_yaml_config,
    mock_surfaces,
    mock_cubes,
    patch_surface_loader,
    patch_directory_validation,
):
    # rms in relai_depth has scale_factor override = 1.02 while global is 1.0
    attrs = populate_seismic_attributes(real_yaml_config, mock_cubes, mock_surfaces)
    rms_attr = [
        a
        for a in attrs
        if "rms" in a.calc_types
        and any(
            a.from_cube is mock_cubes[name] and name.attribute == "relai"
            for name in mock_cubes
        )
    ]
    assert len(rms_attr) == 1
    assert rms_attr[0].scale_factor == 1.02


def test_different_attribute_overrides_result_in_separate_groups(
    real_yaml_config,
    mock_surfaces,
    mock_cubes,
    patch_surface_loader,
    patch_directory_validation,
):
    # In amplitude_depth:
    # mean overrides top/base shifts, min only scale_factor
    # => different interval configs
    attrs = populate_seismic_attributes(real_yaml_config, mock_cubes, mock_surfaces)
    amplitude_cube = next(
        c for n, c in mock_cubes.items() if n.attribute == "amplitude"
    )
    amp_attrs = [a for a in attrs if a.from_cube is amplitude_cube]
    # Expect 3 interval groups:
    # mean, min, and rms inherited from global attributes list but no overrides
    assert len(amp_attrs) == 3
    for attr in amp_attrs:
        assert len(attr.calc_types) == 1
    all_calc_types = {attr.calc_types[0] for attr in amp_attrs}
    assert all_calc_types == {"mean", "min", "rms"}


def test_value_property_applies_shifts_and_scale(patch_directory_validation):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],
            "scale_factor": 2.5,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "gamma": {
                        "top_horizon": "topgamma",
                        "bottom_horizon": "basegamma",
                        "top_surface_shift": -3.0,
                        "bottom_surface_shift": 7.0,
                    }
                },
            }
        },
    }

    top = Mock(spec=xtgeo.RegularSurface)
    bottom = Mock(spec=xtgeo.RegularSurface)

    top.__add__ = Mock(side_effect=lambda x: top)
    bottom.__add__ = Mock(side_effect=lambda x: bottom)

    surfaces = {
        "topgamma--depth.gri": top,
        "basegamma--depth.gri": bottom,
    }

    cube_obj = Mock()

    def compute_attributes(window_top, window_base):
        # Ensure called with shifted surfaces (top shift -3, base shift +7)
        assert window_top is top
        assert window_base is bottom
        return {"rms": 4.0}

    cube_obj.compute_attributes_in_window = Mock(side_effect=compute_attributes)
    seismic = Mock(spec=SingleSeismic)
    seismic.cube = cube_obj

    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): seismic
    }

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=lambda path: surfaces[path.split("/")[-1]],
    ):
        attrs = populate_seismic_attributes(config, cubes, surfaces)

    assert len(attrs) == 1
    val_list = attrs[0].value
    # scale_factor 2.5 * raw 4.0 = 10.0
    assert val_list == [10.0]
    cube_obj.compute_attributes_in_window.assert_called_once()


def test_observed_data_attributes_are_not_scaled(patch_directory_validation):
    """Observed data defines the reference level, so scale_factor must not be
    applied to it even when the configuration sets one; only modelled attributes
    are scaled."""
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],
            "scale_factor": 2.5,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "gamma": {
                        "top_horizon": "topgamma",
                        "bottom_horizon": "basegamma",
                        "top_surface_shift": -3.0,
                        "bottom_surface_shift": 7.0,
                    }
                },
            }
        },
    }

    top = Mock(spec=xtgeo.RegularSurface)
    bottom = Mock(spec=xtgeo.RegularSurface)
    top.__add__ = Mock(side_effect=lambda x: top)
    bottom.__add__ = Mock(side_effect=lambda x: bottom)

    surfaces = {
        "topgamma--depth.gri": top,
        "basegamma--depth.gri": bottom,
    }

    cube_obj = Mock()
    cube_obj.compute_attributes_in_window = Mock(return_value={"rms": 4.0})
    seismic = Mock(spec=SingleSeismic)
    seismic.cube = cube_obj

    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): seismic
    }

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=lambda path: surfaces[path.split("/")[-1]],
    ):
        modelled = populate_seismic_attributes(config, cubes, surfaces)
        observed = populate_seismic_attributes(
            config, cubes, surfaces, is_observed=True
        )

    assert modelled[0].scale_factor == 2.5
    assert observed[0].scale_factor == 1.0
    # Modelled attributes are scaled (2.5 * 4.0), observed are left unscaled (4.0)
    assert modelled[0].value == [10.0]
    assert observed[0].value == [4.0]


def test_missing_surface_raises_value_error(patch_directory_validation):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "x_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "zeta": {
                        "top_horizon": "topzeta",
                        "bottom_horizon": "basezeta",
                    }
                },
            }
        },
    }
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): Mock(spec=SingleSeismic)
    }
    surfaces = {}

    def missing_loader(path: str):
        raise FileNotFoundError(path)

    with (
        patch(
            "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
            side_effect=missing_loader,
        ),
        pytest.raises(ValueError, match="Surface file not found"),
    ):
        populate_seismic_attributes(config, cubes, surfaces)


def test_multiple_cubes_same_prefix_duplicate_attributes(patch_directory_validation):
    """
    One cube_prefix can match on several cubes.
    """
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms", "mean"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "eta": {
                        "top_horizon": "topeta",
                        "bottom_horizon": "baseeta",
                    }
                },
            }
        },
    }
    top = Mock(spec=xtgeo.RegularSurface)
    bottom = Mock(spec=xtgeo.RegularSurface)
    surfaces = {
        "topeta--depth.gri": top,
        "baseeta--depth.gri": bottom,
    }

    cube1 = Mock(spec=SingleSeismic)
    cube2 = Mock(spec=SingleSeismic)
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): cube1,
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200201"
        ): cube2,
    }

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=lambda path: surfaces[path.split("/")[-1]],
    ):
        attrs = populate_seismic_attributes(config, cubes, surfaces)

    # Grouping: rms+mean together for each cube => 2 attributes objects
    assert len(attrs) == 2
    # Ensure each cube represented once
    cubes_in_attrs = {id(a.from_cube) for a in attrs}
    expected_cubes = {id(c) for c in [cube1, cube2]}
    assert cubes_in_attrs == expected_cubes


def test_window_interval_zeros_out_bottom_surface_shift(
    patch_surface_loader,
    patch_directory_validation,
    create_chainable_surface,
):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "win_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "iota": {
                        "top_horizon": "topiota",
                        "bottom_horizon": "baseiota",
                        "window_length": 12.0,
                        "top_surface_shift": 2.0,
                        "bottom_surface_shift": 5.0,  # This should be zeroed
                    }
                },
            }
        },
    }
    top, _intermediate, _final = create_chainable_surface()
    surfaces = {"topiota--depth.gri": top}
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): Mock(spec=SingleSeismic)
    }

    with pytest.warns(UserWarning):
        seismic_attr_list = populate_seismic_attributes(config, cubes, surfaces)

    assert len(seismic_attr_list) == 1
    attr = seismic_attr_list[0]
    assert attr.window_length == 12.0
    assert attr.bottom_surface_shift == 0.0


def test_group_attributes_by_interval_all_same(patch_directory_validation):
    global_config = GlobalConfig(
        gridhorizon_path="/grids",
        attributes=["rms", "mean", "min"],
        surface_postfix="--depth.gri",
        scale_factor=1.0,
    )
    window_settings = WindowSettings(
        top_horizon="top",
        bottom_horizon="base",
        top_surface_shift=0.0,
        bottom_surface_shift=0.0,
        window_length=None,
    )
    result = _group_attributes_by_interval(
        window_settings=window_settings,
        global_config=global_config,
        window_name="my_window",
        cube_name="my_cube",
    )
    assert len(result) == 1
    interval_key = next(iter(result.keys()))
    assert sorted(result[interval_key]) == ["mean", "min", "rms"]


def test_group_attributes_by_interval_all_different(patch_directory_validation):
    global_config = GlobalConfig(
        gridhorizon_path="/grids",
        attributes=["rms", "mean", "min"],
        surface_postfix="--depth.gri",
        scale_factor=1.0,
    )
    window_settings = WindowSettings(
        top_horizon="top",
        bottom_horizon="base",
        top_surface_shift=0.0,
        bottom_surface_shift=0.0,
        window_length=None,
        # Overrides go at top level, not in attribute_overrides!
        rms={"scale_factor": 1.5},
        mean={"top_surface_shift": -5.0},
        min={"bottom_surface_shift": 10.0},
    )
    result = _group_attributes_by_interval(
        window_settings=window_settings,
        global_config=global_config,
        window_name="my_window",
        cube_name="my_cube",
    )
    assert len(result) == 3


@pytest.mark.parametrize(
    "match_results,expected_count",
    [
        ([True, False], 1),
        ([True, True, False], 2),
        ([False, False], 0),
    ],
    ids=["single_match", "multiple_matches", "no_matches"],
)
def test_get_matching_cubes(match_results, expected_count):
    cubes = {}
    expected_cubes = []

    for i, should_match in enumerate(match_results):
        cube = Mock(spec=SingleSeismic)
        name = Mock(spec=SeismicName)
        name.compare_without_date = Mock(return_value=should_match)
        cubes[name] = cube

        if should_match:
            expected_cubes.append(cube)

    result = _get_matching_cubes(cubes, "prefix")

    assert len(result) == expected_count
    for cube in expected_cubes:
        assert cube in result


def test_multiple_windows_in_single_cube(patch_directory_validation):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "alpha": {
                        "top_horizon": "topalpha",
                        "bottom_horizon": "basealpha",
                    },
                    "beta": {
                        "top_horizon": "topbeta",
                        "bottom_horizon": "basebeta",
                    },
                },
            }
        },
    }

    surfaces = {}
    for name in ["topalpha", "basealpha", "topbeta", "basebeta"]:
        surf = Mock(spec=xtgeo.RegularSurface)
        surfaces[f"{name}--depth.gri"] = surf

    cube = Mock(spec=SingleSeismic)
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): cube
    }

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=lambda path: surfaces.get(
            path.split("/")[-1], Mock(spec=xtgeo.RegularSurface)
        ),
    ):
        attrs = populate_seismic_attributes(config, cubes, surfaces)

    assert len(attrs) == 2
    assert all(a.from_cube is cube for a in attrs)


def test_attribute_with_only_horizon_override(patch_directory_validation):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms", "mean"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "kappa": {
                        "top_horizon": "topkappa",
                        "bottom_horizon": "basekappa",
                        "rms": {
                            "top_horizon": "alternate_top",
                        },
                    }
                },
            }
        },
    }

    surfaces = {
        "topkappa--depth.gri": Mock(spec=xtgeo.RegularSurface),
        "basekappa--depth.gri": Mock(spec=xtgeo.RegularSurface),
        "alternate_top--depth.gri": Mock(spec=xtgeo.RegularSurface),
    }

    cube = Mock(spec=SingleSeismic)
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): cube
    }

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=lambda path: surfaces.get(
            path.split("/")[-1], Mock(spec=xtgeo.RegularSurface)
        ),
    ):
        attrs = populate_seismic_attributes(config, cubes, surfaces)

    assert len(attrs) == 2
    rms_attrs = [a for a in attrs if "rms" in a.calc_types]
    mean_attrs = [a for a in attrs if "mean" in a.calc_types]
    assert len(rms_attrs) == 1
    assert len(mean_attrs) == 1


def test_surface_loaded_only_once_when_reused(patch_directory_validation):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms", "mean"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "nu": {
                        "top_horizon": "topnu",
                        "bottom_horizon": "basenu",
                    },
                    "xi": {
                        "top_horizon": "topnu",
                        "bottom_horizon": "basexi",
                    },
                },
            }
        },
    }

    surfaces = {}
    load_count = {"topnu": 0, "basenu": 0, "basexi": 0}

    def surface_loader(path: str):
        for name in load_count:
            if path.endswith(f"{name}--depth.gri"):
                load_count[name] += 1
                return Mock(spec=xtgeo.RegularSurface)
        raise AssertionError(f"Unexpected path: {path}")

    cube = Mock(spec=SingleSeismic)
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): cube
    }

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=surface_loader,
    ):
        attrs = populate_seismic_attributes(config, cubes, surfaces)

    assert len(attrs) == 2
    assert load_count["topnu"] == 1
    assert load_count["basenu"] == 1
    assert load_count["basexi"] == 1


def test_attribute_with_window_length_override(
    patch_directory_validation,
    create_chainable_surface,
):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms", "mean"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "omicron": {
                        "top_horizon": "topomicron",
                        "bottom_horizon": "baseomicron",
                        "mean": {
                            "window_length": 50.0,
                        },
                    }
                },
            }
        },
    }

    top_surf, _inter, _final = create_chainable_surface()
    base_surf = Mock(spec=xtgeo.RegularSurface)

    surfaces = {
        "topomicron--depth.gri": top_surf,
        "baseomicron--depth.gri": base_surf,
    }

    cube = Mock(spec=SingleSeismic)
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): cube
    }

    with (
        patch(
            "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
            side_effect=lambda path: surfaces.get(
                path.split("/")[-1], Mock(spec=xtgeo.RegularSurface)
            ),
        ),
        warnings.catch_warnings(),
    ):
        # The override replaces the window base, so no precedence warning
        warnings.simplefilter("error")
        attrs = populate_seismic_attributes(config, cubes, surfaces)

    assert len(attrs) == 2
    mean_attrs = [
        a for a in attrs if "mean" in a.calc_types and "rms" not in a.calc_types
    ]
    rms_attrs = [
        a for a in attrs if "rms" in a.calc_types and "mean" not in a.calc_types
    ]

    assert len(mean_attrs) == 1
    assert len(rms_attrs) == 1
    assert mean_attrs[0].window_length == 50.0
    assert rms_attrs[0].window_length is None


def test_attribute_override_rejects_null():
    with pytest.raises(ValidationError, match="must not be null"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            window_length=25.0,
            mean={"window_length": None},
        )


def test_attribute_override_bottom_horizon_replaces_window_length():
    window = WindowSettings(
        top_horizon="top",
        window_length=25.0,
        mean={"bottom_horizon": "base"},
    )

    interval = window.build_interval_config("mean", 1.0, "window", "cube")

    assert interval.bottom_horizon == "base"
    assert interval.window_length is None


def test_attribute_override_with_both_bounds_prefers_window_length():
    window = WindowSettings(
        top_horizon="top",
        bottom_horizon="base",
        mean={"bottom_horizon": "other", "window_length": 10.0},
    )

    with pytest.warns(UserWarning, match="'window_length' will take precedence"):
        interval = window.build_interval_config("mean", 1.0, "window", "cube")

    assert interval.bottom_horizon == "other"
    assert interval.window_length == 10.0


@pytest.mark.parametrize("window_length", [0, -1])
def test_attribute_override_window_length_must_be_positive(window_length):
    with pytest.raises(ValidationError, match="greater than 0"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            mean={"window_length": window_length},
        )


# ---------------------------------------------------------------------------
# Observation error configuration
# ---------------------------------------------------------------------------


def test_error_config_requires_exactly_one_source():
    with pytest.raises(ValidationError):
        ErrorConfig(type="relative")  # neither value nor error_surface
    with pytest.raises(ValidationError):
        ErrorConfig(type="relative", value=0.1, error_surface=Path("err.gri"))


@pytest.mark.parametrize("error_surface", ["", "   "])
def test_error_config_rejects_blank_surface(error_surface):
    with pytest.raises(ValidationError, match="error_surface must be a non-empty"):
        ErrorConfig(type="absolute", error_surface=error_surface)


def test_error_config_rejects_negative_values():
    with pytest.raises(ValidationError):
        ErrorConfig(type="relative", value=-0.1)
    with pytest.raises(ValidationError):
        ErrorConfig(type="absolute", value=0.1, minimum=-0.1)


def test_error_config_rejects_unknown_type():
    with pytest.raises(ValidationError):
        ErrorConfig(type="bogus", value=0.1)


def _global_config(tmp_path, **error_kwargs):
    grid_path = tmp_path / "maps"
    grid_path.mkdir(exist_ok=True)
    return GlobalConfig(
        gridhorizon_path=str(grid_path),
        attributes=["rms"],
        scale_factor=1.0,
        surface_postfix="--depth.gri",
        **error_kwargs,
    )


@pytest.mark.parametrize("field", ["gridhorizon_path", "error_path"])
def test_global_config_requires_existing_directories(tmp_path, field):
    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()
    config = {
        "gridhorizon_path": existing_dir,
        "attributes": ["rms"],
        "surface_postfix": "--depth.gri",
        "scale_factor": 1.0,
        "error_path": existing_dir,
    }
    config[field] = tmp_path / "missing"

    with pytest.raises(ValidationError, match=field):
        GlobalConfig.model_validate(config)


def test_global_config_path_validation_can_be_skipped(tmp_path):
    config = {
        "gridhorizon_path": tmp_path / "missing-grid",
        "attributes": ["rms"],
        "surface_postfix": "--depth.gri",
        "scale_factor": 1.0,
        "error_path": tmp_path / "missing-errors",
    }

    GlobalConfig.model_validate(config, context={"validate_paths": False})


def _root_config_dict(tmp_path, error, error_path=None):
    grid_path = tmp_path / "maps"
    grid_path.mkdir(exist_ok=True)
    global_section = {
        "gridhorizon_path": str(grid_path),
        "attributes": ["rms"],
        "scale_factor": 1.0,
        "surface_postfix": "--depth.gri",
    }
    if error is not None:
        global_section["error"] = error
    if error_path is not None:
        global_section["error_path"] = str(error_path)
    return {
        "global": global_section,
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "beta": {"top_horizon": "topbeta", "bottom_horizon": "basebeta"}
                },
            }
        },
    }


def test_error_override_precedence(tmp_path):
    global_config = _global_config(tmp_path, error={"type": "relative", "value": 0.07})
    prefix = "seismic--amplitude_depth--"
    cube_with_error = CubeConfig(
        cube_prefix=prefix, windows={}, error={"type": "absolute", "value": 0.1}
    )
    cube_without_error = CubeConfig(cube_prefix=prefix, windows={})
    window_with_error = WindowSettings(
        top_horizon="t", bottom_horizon="b", error={"type": "relative", "value": 0.2}
    )
    window_without_error = WindowSettings(top_horizon="t", bottom_horizon="b")
    assert cube_with_error.error.minimum == 0.0
    assert window_with_error.error.minimum == 0.0

    # Window wins over cube and global
    resolved = _resolve_error_block(global_config, cube_with_error, window_with_error)
    assert resolved.value == 0.2

    # Cube wins over global when window has no error
    resolved = _resolve_error_block(
        global_config, cube_with_error, window_without_error
    )
    assert resolved.value == 0.1

    # Global applies when neither cube nor window set an error
    resolved = _resolve_error_block(
        global_config, cube_without_error, window_without_error
    )
    assert resolved.value == 0.07

    # No error anywhere resolves to None
    resolved = _resolve_error_block(
        _global_config(tmp_path), cube_without_error, window_without_error
    )
    assert resolved is None


def test_error_fields_accept_error_config_instances(tmp_path):
    error = ErrorConfig(type="relative", value=0.1)

    assert _global_config(tmp_path, error=error).error == error
    cube = CubeConfig(cube_prefix="seismic--amplitude_depth--", windows={}, error=error)
    assert cube.error == error
    assert WindowSettings(top_horizon="t", bottom_horizon="b", error=error).error == (
        error
    )


@pytest.mark.parametrize(
    ("section", "key", "path"),
    [
        ("global", "error", "global.error"),
        ("window", "window_length", "cubes.amp_depth.windows.beta.window_length"),
        ("window", "error", "cubes.amp_depth.windows.beta.error"),
    ],
)
def test_root_config_rejects_null_values(tmp_path, section, key, path):
    config = _root_config_dict(tmp_path, error=None)
    target = (
        config["global"]
        if section == "global"
        else config["cubes"]["amp_depth"]["windows"]["beta"]
    )
    target[key] = None

    with pytest.raises(ValidationError, match=re.escape(path)):
        RootConfig.model_validate(config)


@pytest.mark.parametrize("level", ["global", "cube", "window"])
def test_error_surface_resolved_against_error_path(tmp_path, level):
    error_dir = tmp_path / "errors"
    error_dir.mkdir()
    error_file = error_dir / "err.gri"
    error_file.write_bytes(b"x")

    config = _root_config_dict(tmp_path, error=None, error_path=error_dir)
    error = {"type": "absolute", "error_surface": "err.gri"}
    if level == "global":
        config["global"]["error"] = error
    elif level == "cube":
        config["cubes"]["amp_depth"]["error"] = error
    else:
        config["cubes"]["amp_depth"]["windows"]["beta"]["error"] = error

    root = RootConfig.model_validate(config)
    if level == "global":
        resolved_error = root.global_config.error
    elif level == "cube":
        resolved_error = root.cubes["amp_depth"].error
    else:
        resolved_error = root.cubes["amp_depth"].windows["beta"].error
    assert resolved_error.error_surface == error_file.resolve()


def test_error_surface_missing_file_raises(tmp_path):
    error_dir = tmp_path / "errors"
    error_dir.mkdir()
    config = _root_config_dict(
        tmp_path,
        error={"type": "absolute", "error_surface": "missing.gri"},
        error_path=error_dir,
    )
    with pytest.raises(ValidationError, match="Error surface file not found"):
        RootConfig.model_validate(config)


@pytest.mark.parametrize("level", ["global", "cube", "window"])
def test_error_surface_without_error_path_raises(tmp_path, level):
    config = _root_config_dict(tmp_path, error=None)
    error = {"type": "absolute", "error_surface": "err.gri"}
    if level == "global":
        config["global"]["error"] = error
    elif level == "cube":
        config["cubes"]["amp_depth"]["error"] = error
    else:
        config["cubes"]["amp_depth"]["windows"]["beta"]["error"] = error

    with pytest.raises(ValidationError, match="error_path"):
        RootConfig.model_validate(config)


def test_error_propagated_to_seismic_attribute(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
):
    real_yaml_config["global"]["error"] = {
        "type": "relative",
        "value": 0.07,
        "minimum": 0.005,
    }
    attrs = populate_seismic_attributes(real_yaml_config, mock_cubes, mock_surfaces)
    assert attrs
    assert all(a.error is not None for a in attrs)
    assert all(a.error.type == "relative" for a in attrs)
    assert all(a.error.value == 0.07 for a in attrs)
    assert all(a.error.minimum == 0.005 for a in attrs)


# ---------------------------------------------------------------------------
# Zone / vertical sampling position configuration
# ---------------------------------------------------------------------------


def test_zone_position_default_when_omitted(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
):
    """When zone/position are omitted, attributes get the documented defaults."""
    attrs = populate_seismic_attributes(real_yaml_config, mock_cubes, mock_surfaces)
    assert attrs
    assert all(a.zone == "" for a in attrs)
    assert all(a.position == "center" for a in attrs)


def test_window_zone_position_propagate_to_attribute(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
):
    """Window-level zone/position propagate to every attribute of that
    window, including attributes that override other interval settings."""
    for cube in real_yaml_config["cubes"].values():
        cube["windows"]["volantis"]["zone"] = "Valysar"
        cube["windows"]["volantis"]["position"] = "top"

    attrs = populate_seismic_attributes(real_yaml_config, mock_cubes, mock_surfaces)
    assert attrs
    assert all(a.zone == "Valysar" for a in attrs)
    assert all(a.position == "top" for a in attrs)


@pytest.mark.parametrize("position", ["top", "center", "base"])
def test_all_positions_are_accepted(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader, position
):
    for cube in real_yaml_config["cubes"].values():
        cube["windows"]["volantis"]["position"] = position

    attrs = populate_seismic_attributes(real_yaml_config, mock_cubes, mock_surfaces)
    assert attrs
    assert all(a.position == position for a in attrs)


def test_invalid_position_is_rejected(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
):
    real_yaml_config["cubes"]["relai_depth"]["windows"]["volantis"]["position"] = (
        "middle"
    )
    with pytest.raises(ValidationError):
        populate_seismic_attributes(real_yaml_config, mock_cubes, mock_surfaces)


@pytest.mark.parametrize("field", ["zone", "position", "error"])
def test_window_only_fields_rejected_in_override(field):
    """`zone`, `position` and `error` apply to the whole window and cannot be
    adjusted per attribute."""
    values = {
        "zone": "Therys",
        "position": "base",
        "error": {"type": "absolute", "value": 0.1},
    }
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            mean={field: values[field]},
        )


def test_override_for_unlisted_attribute_rejected(patch_directory_validation):
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms", "mean"],
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp": {
                "cube_prefix": "seismic--amplitude_depth--",
                "windows": {
                    "win": {
                        "top_horizon": "top",
                        "bottom_horizon": "base",
                        "max": {"scale_factor": 2.0},
                    }
                },
            }
        },
    }
    with pytest.raises(ValidationError, match=r"cube 'amp', window 'win'.*\['max'\]"):
        RootConfig.model_validate(config)


def test_window_requires_top_horizon_and_base():
    with pytest.raises(ValidationError, match="top_horizon"):
        WindowSettings(bottom_horizon="base")
    with pytest.raises(ValidationError, match="at least 1 character"):
        WindowSettings(top_horizon="", bottom_horizon="base")
    with pytest.raises(ValidationError, match="match pattern"):
        WindowSettings(top_horizon=" ", bottom_horizon="base")
    with pytest.raises(ValidationError, match="at least 1 character"):
        WindowSettings(top_horizon="top", bottom_horizon="")
    with pytest.raises(ValidationError, match="match pattern"):
        WindowSettings(top_horizon="top", bottom_horizon=" ")
    with pytest.raises(ValidationError, match=r"bottom_horizon.*window_length"):
        WindowSettings(top_horizon="top")
    with pytest.raises(ValidationError, match="greater than 0"):
        WindowSettings(top_horizon="top", window_length=-10.0)

    with pytest.raises(ValidationError, match="at least 1 character"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            mean={"top_horizon": ""},
        )
    with pytest.raises(ValidationError, match="match pattern"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            mean={"top_horizon": " "},
        )
    with pytest.raises(ValidationError, match="at least 1 character"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            mean={"bottom_horizon": ""},
        )
    with pytest.raises(ValidationError, match="match pattern"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            mean={"bottom_horizon": " "},
        )


@pytest.mark.parametrize("key", ["botom_horizon", "rsm"])
def test_unknown_window_key_rejected(key):
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WindowSettings(top_horizon="top", bottom_horizon="base", **{key: 1})


def test_extract_attributes_does_not_mutate_input():
    window_data = {
        "top_horizon": "top",
        "bottom_horizon": "base",
        "rms": {"top_surface_shift": -15},
    }

    window = WindowSettings.model_validate(window_data)

    assert window_data == {
        "top_horizon": "top",
        "bottom_horizon": "base",
        "rms": {"top_surface_shift": -15},
    }
    assert window.attribute_overrides["rms"].top_surface_shift == -15


def test_internal_attribute_overrides_key_rejected():
    with pytest.raises(ValidationError, match=r"attribute_overrides.*is internal"):
        WindowSettings(
            top_horizon="top",
            bottom_horizon="base",
            attribute_overrides={"rms": {"top_horizon": "other"}},
        )


@pytest.mark.parametrize(
    "prefix, valid",
    [
        ("seismic--relai_full_depth--", True),
        ("seismic--amplitude_depth--", True),
        ("seismic--amplitude_near_time", True),
        ("seismic--relai_fulldepth--", False),
        ("relai_full_depth", False),
        ("seismic--relai_full_depth--20200101", False),
    ],
)
def test_cube_prefix_pattern(prefix, valid):
    if valid:
        assert CubeConfig(cube_prefix=prefix, windows={}).cube_prefix == prefix
    else:
        with pytest.raises(ValidationError, match="should match pattern"):
            CubeConfig(cube_prefix=prefix, windows={})


def test_attribute_export_forwards_zone_position_tuple():
    """`attribute_export` must forward each attribute's (zone, position) as the
    `position` tuple into `sample_attributes_for_sim2seis`."""
    attr = Mock(spec=SeismicAttribute)
    attr.zone = "Valysar"
    attr.position = "top"
    attr.calc_types = ["rms"]
    attr.value = [Mock(spec=xtgeo.RegularSurface)]
    attr.error = None
    attr.from_cube = MagicMock()
    attr.from_cube.cube_name.attribute = "amplitude"
    attr.from_cube.cube_name.stack = "full"
    attr.from_cube.cube_name.domain = "depth"
    attr.from_cube.monitor_date = "20200701"
    attr.from_cube.base_date = "20180101"

    config = MagicMock()
    captured = {}

    class _Stop(Exception):
        """Sentinel to halt export right after the forwarded sample call."""

    def fake_sample(**kwargs):
        captured["position"] = kwargs["position"]
        raise _Stop

    zone_def = Mock()
    zone_def.codes = {1: "Valysar"}
    with (
        patch.object(export_with_dataio, "restore_dir"),
        patch.object(
            export_with_dataio,
            "_get_grid_info",
            return_value=(Mock(), zone_def, Mock()),
        ),
        patch.object(export_with_dataio, "dataio"),
        patch.object(
            export_with_dataio.tools,
            "sample_attributes_for_sim2seis",
            side_effect=fake_sample,
        ),
        pytest.raises(_Stop),
    ):
        export_with_dataio.attribute_export(
            config_file=config,
            export_attributes=[attr],
            is_observed=False,
        )

    assert captured["position"] == ("Valysar", "top")


def test_attribute_export_rejects_unknown_zone():
    """A requested zone absent from the zone file fails fast with a clear error,
    before any sampling is attempted."""
    attr = Mock(spec=SeismicAttribute)
    attr.zone = "Nonexistent"
    attr.position = "top"

    zone_def = Mock()
    zone_def.codes = {1: "Valysar", 2: "Therys"}
    sample = Mock()
    with (
        patch.object(export_with_dataio, "restore_dir"),
        patch.object(
            export_with_dataio,
            "_get_grid_info",
            return_value=(Mock(), zone_def, Mock()),
        ),
        patch.object(export_with_dataio, "dataio"),
        patch.object(
            export_with_dataio.tools,
            "sample_attributes_for_sim2seis",
            sample,
        ),
        pytest.raises(ValueError, match="Nonexistent"),
    ):
        export_with_dataio.attribute_export(
            config_file=MagicMock(),
            export_attributes=[attr],
            is_observed=False,
        )
    sample.assert_not_called()
