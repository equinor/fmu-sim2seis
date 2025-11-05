import logging
from unittest.mock import Mock, patch

import pytest
import xtgeo

from fmu.sim2seis.utilities import SeismicName, SingleSeismic
from fmu.sim2seis.utilities.interval_parser import (
    GlobalConfig,
    _get_attribute_interval_settings,
    _get_formation_settings,
    _get_matching_cubes,
    _group_attributes_by_interval,
    populate_seismic_attributes,
)


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


def test_window_length_creates_virtual_base_surface(recwarn, caplog):
    """
    Tests that if window length is provided, then the bottom_horizon is ignored,
    and no warning is emitted.
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
                "cube_prefix": "seismic--window_depth--",
                "filename_tag_prefix": "window_depth",
                "seismic_path": "/seismic",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
                    "alpha": {
                        "top_horizon": "topalpha",
                        "bottom_horizon": "basealpha",
                        "window_length": 25.0,
                    }
                },
            }
        },
    }
    top_surface = Mock(spec=xtgeo.RegularSurface)
    top_surface.__add__ = Mock(return_value=Mock(spec=xtgeo.RegularSurface))
    surfaces = {"topalpha--depth.gri": top_surface}
    cubes = {
        SeismicName(
            process="seismic", attribute="window", domain="depth", date="20200101"
        ): Mock(spec=SingleSeismic)
    }

    with caplog.at_level(logging.WARNING), patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file"
    ) as surface_from_file:
        result = populate_seismic_attributes(
            config=config, cubes=cubes, surfaces=surfaces
        )

    # Assert that code emits no warnings, despite ignoring one config option
    warning_messages = [
        record.message for record in caplog.records if record.levelno >= logging.WARNING
    ]
    assert len(warning_messages) == 0, (
        f"Expected no warnings, but got: {warning_messages}"
    )
    assert len(recwarn) == 0

    assert surface_from_file.call_count == 1
    assert surface_from_file.call_args[0][0] == "/grids/topalpha--depth.gri"
    top_surface.__add__.assert_called_once_with(25.0)
    assert result[0].base_surface is top_surface.__add__.return_value


def test_missing_surfaces_are_loaded_from_disk():
    """
    Tests that if the surfaces are not provided to `populate_seismic_attributes`
    then they are loaded to disk as
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
                "cube_prefix": "seismic--amp_depth--",
                "filename_tag_prefix": "amp_depth",
                "seismic_path": "/seismic",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
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
            process="seismic", attribute="amp", domain="depth", date="20200101"
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


def test_populate_raises_when_no_matching_cubes(real_yaml_config, mock_surfaces):
    """
    Should maybe be a more specific error message?
    """
    with pytest.raises(ValueError, match="No attributes generated"):
        populate_seismic_attributes(
            config=real_yaml_config, cubes={}, surfaces=mock_surfaces
        )


def test_attribute_specific_scale_factor_override(
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
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
    real_yaml_config, mock_surfaces, mock_cubes, patch_surface_loader
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


def test_value_property_applies_shifts_and_scale():
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
                    "gamma": {
                        "top_horizon": "topgamma",
                        "bottom_horizon": "basegamma",
                        "top_surface_shift": -3.0,
                        "base_surface_shift": 7.0,
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


def test_missing_surface_raises_value_error():
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
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

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=missing_loader,
    ), pytest.raises(ValueError, match="Surface file not found"):
        populate_seismic_attributes(config, cubes, surfaces)


def test_multiple_cubes_same_prefix_duplicate_attributes():
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
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


def test_empty_attributes_in_formation_raises_value_error():
    """
    If one specifies the attributes section underneath a formation, then
    that will override the global.attributes. Should probably not be allowed?
    """
    config = {
        "global": {
            "gridhorizon_path": "/grids",
            "attributes": ["rms"],  # global default
            "scale_factor": 1.0,
            "surface_postfix": "--depth.gri",
        },
        "cubes": {
            "amp_depth": {
                "cube_prefix": "seismic--amplitude_depth--",
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
                    "theta": {
                        "top_horizon": "toptheta",
                        "bottom_horizon": "basetheta",
                        "attributes": [],  # explicitly empty
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
    surf = Mock(spec=xtgeo.RegularSurface)
    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        return_value=surf,
    ), pytest.raises(ValueError, match="No attributes generated"):
        populate_seismic_attributes(config, cubes, surfaces)


def test_window_interval_retains_base_surface_shift_current_behavior(
    patch_surface_loader,
):
    """
    Document current (possibly unintended) behavior:
    base_surface_shift not zeroed when window_length used
    """
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
                    "iota": {
                        "top_horizon": "topiota",
                        "bottom_horizon": "baseiota",
                        "window_length": 12.0,
                        "top_surface_shift": 2.0,
                        "base_surface_shift": 5.0,  # retained
                    }
                },
            }
        },
    }
    top = Mock(spec=xtgeo.RegularSurface)
    top.__add__ = Mock(return_value=Mock(spec=xtgeo.RegularSurface))
    surfaces = {"topiota--depth.gri": top}
    cubes = {
        SeismicName(
            process="seismic", attribute="amplitude", domain="depth", date="20200101"
        ): Mock(spec=SingleSeismic)
    }

    seismic_attr_list = populate_seismic_attributes(config, cubes, surfaces)

    assert len(seismic_attr_list) == 1
    attr = seismic_attr_list[0]
    assert attr.window_length == 12.0
    assert attr.base_surface_shift == 5.0


@pytest.mark.parametrize(
    "formation_info,expected_values",
    [
        # No overrides - all use defaults
        (
            {},
            {
                "top_horizon": "tophorizon",
                "bottom_horizon": "basehorizon",
                "top_surface_shift": 5.0,
                "base_surface_shift": 10.0,
                "window_length": None,
                "scale_factor": 2.0,
            },
        ),
        # All overrides
        (
            {
                "rms": {
                    "top_horizon": "custom_top",
                    "bottom_horizon": "custom_base",
                    "top_surface_shift": -20.0,
                    "base_surface_shift": 15.0,
                    "window_length": 30.0,
                    "scale_factor": 3.5,
                }
            },
            {
                "top_horizon": "custom_top",
                "bottom_horizon": "custom_base",
                "top_surface_shift": -20.0,
                "base_surface_shift": 15.0,
                "window_length": 30.0,
                "scale_factor": 3.5,
            },
        ),
        # Partial overrides
        (
            {"rms": {"top_surface_shift": -8.0, "scale_factor": 1.8}},
            {
                "top_horizon": "tophorizon",
                "bottom_horizon": "basehorizon",
                "top_surface_shift": -8.0,
                "base_surface_shift": 10.0,
                "window_length": None,
                "scale_factor": 1.8,
            },
        ),
    ],
    ids=["no_overrides", "all_overrides", "partial_overrides"],
)
def test_get_attribute_interval_settings(formation_info, expected_values):
    defaults = {
        "top_horizon": "tophorizon",
        "bottom_horizon": "basehorizon",
        "top_surface_shift": 5.0,
        "base_surface_shift": 10.0,
        "window_length": None,
        "scale_factor": 2.0,
    }
    result = _get_attribute_interval_settings("rms", formation_info, defaults)

    assert result.top_horizon == expected_values["top_horizon"]
    assert result.bottom_horizon == expected_values["bottom_horizon"]
    assert result.top_surface_shift == expected_values["top_surface_shift"]
    assert result.base_surface_shift == expected_values["base_surface_shift"]
    assert result.window_length == expected_values["window_length"]
    assert result.scale_factor == expected_values["scale_factor"]


def test_group_attributes_by_interval_all_same():
    global_config = GlobalConfig(
        gridhorizon_path="/grids",
        attributes=["rms", "mean", "min"],
        surface_postfix="--depth.gri",
        scale_factor=1.0,
    )
    formation_info = {}
    result = _group_attributes_by_interval(
        attributes=["rms", "mean", "min"],
        formation_info=formation_info,
        top_horizon="top",
        bottom_horizon="base",
        top_surface_shift=0.0,
        base_surface_shift=0.0,
        window_length=None,
        global_config=global_config,
    )
    assert len(result) == 1
    interval_key = list(result.keys())[0]
    assert sorted(result[interval_key]) == ["mean", "min", "rms"]


def test_group_attributes_by_interval_all_different():
    global_config = GlobalConfig(
        gridhorizon_path="/grids",
        attributes=["rms", "mean", "min"],
        surface_postfix="--depth.gri",
        scale_factor=1.0,
    )
    formation_info = {
        "rms": {"scale_factor": 1.5},
        "mean": {"top_surface_shift": -5.0},
        "min": {"base_surface_shift": 10.0},
    }
    result = _group_attributes_by_interval(
        attributes=["rms", "mean", "min"],
        formation_info=formation_info,
        top_horizon="top",
        bottom_horizon="base",
        top_surface_shift=0.0,
        base_surface_shift=0.0,
        window_length=None,
        global_config=global_config,
    )
    assert len(result) == 3


@pytest.mark.parametrize(
    "formation_info,expected_values",
    [
        # All defaults
        (
            {},
            {
                "top_horizon": "/grids",  # Does it make sense to default to this?
                "bottom_horizon": "/grids",
                "top_surface_shift": 0,
                "base_surface_shift": 0,
                "window_length": None,
                "attributes": ["rms", "mean"],
            },
        ),
        # With overrides
        (
            {
                "top_horizon": "custom_top",
                "bottom_horizon": "custom_base",
                "top_surface_shift": -5.0,
                "base_surface_shift": 10.0,
                "window_length": 25.0,
            },
            {
                "top_horizon": "custom_top",
                "bottom_horizon": "custom_base",
                "top_surface_shift": -5.0,
                "base_surface_shift": 10.0,
                "window_length": 25.0,
                "attributes": ["rms", "mean"],  # Still uses global default
            },
        ),
    ],
    ids=["all_defaults", "with_overrides"],
)
def test_get_formation_settings(formation_info, expected_values):
    global_config = GlobalConfig(
        gridhorizon_path="/grids",
        attributes=["rms", "mean"],
        surface_postfix="--depth.gri",
        scale_factor=1.0,
    )
    settings = _get_formation_settings(formation_info, global_config)

    assert settings.top_horizon == expected_values["top_horizon"]
    assert settings.bottom_horizon == expected_values["bottom_horizon"]
    assert settings.top_surface_shift == expected_values["top_surface_shift"]
    assert settings.base_surface_shift == expected_values["base_surface_shift"]
    assert settings.window_length == expected_values["window_length"]
    assert settings.attributes == expected_values["attributes"]


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


def test_multiple_formations_in_single_cube():
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
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


def test_attribute_with_only_horizon_override():
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
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


def test_surface_loaded_only_once_when_reused():
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
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
    assert load_count["topnu"] == 2
    assert load_count["basenu"] == 1
    assert load_count["basexi"] == 1


def test_attribute_with_window_length_override():
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
                "filename_tag_prefix": "amplitude_depth",
                "seismic_path": "/seis",
                "vertical_domain": "depth",
                "depth_reference": "msl",
                "offset": "full",
                "formations": {
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

    top_surf = Mock(spec=xtgeo.RegularSurface)
    base_surf = Mock(spec=xtgeo.RegularSurface)
    virtual_base = Mock(spec=xtgeo.RegularSurface)
    top_surf.__add__ = Mock(return_value=virtual_base)

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

    with patch(
        "fmu.sim2seis.utilities.interval_parser.xtgeo.surface_from_file",
        side_effect=lambda path: surfaces.get(
            path.split("/")[-1], Mock(spec=xtgeo.RegularSurface)
        ),
    ):
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
