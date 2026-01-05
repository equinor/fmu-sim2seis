from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import xtgeo

from fmu.sim2seis.utilities import SeismicName, SingleSeismic
from fmu.sim2seis.utilities.interval_parser import (
    FormationSettings,
    GlobalConfig,
    _get_matching_cubes,
    _group_attributes_by_interval,
    populate_seismic_attributes,
)


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
                "formations": {
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
                "formations": {
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
                "cube_prefix": "seismic--window_depth--",
                "formations": {
                    "alpha": {
                        "bottom_horizon": "basealpha",
                        "window_length": 25.0,
                        "rms": {
                            "top_horizon": "topalpha",
                        },
                    }
                },
            }
        },
    }
    top_surface, intermediate, final = create_chainable_surface()
    surfaces = {}
    cubes = {
        SeismicName(
            process="seismic", attribute="window", domain="depth", date="20200101"
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
                "cube_prefix": "seismic--amp_depth--",
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
                "formations": {
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
                "formations": {
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
    formation_settings = FormationSettings(
        top_horizon="top",
        bottom_horizon="base",
        top_surface_shift=0.0,
        bottom_surface_shift=0.0,
        window_length=None,
    )
    result = _group_attributes_by_interval(
        formation_settings=formation_settings,
        global_config=global_config,
        formation_name="my_formation",
        cube_name="my_cube",
    )
    assert len(result) == 1
    interval_key = list(result.keys())[0]
    assert sorted(result[interval_key]) == ["mean", "min", "rms"]


def test_group_attributes_by_interval_all_different(patch_directory_validation):
    global_config = GlobalConfig(
        gridhorizon_path="/grids",
        attributes=["rms", "mean", "min"],
        surface_postfix="--depth.gri",
        scale_factor=1.0,
    )
    formation_settings = FormationSettings(
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
        formation_settings=formation_settings,
        global_config=global_config,
        formation_name="my_formation",
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


def test_multiple_formations_in_single_cube(patch_directory_validation):
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
