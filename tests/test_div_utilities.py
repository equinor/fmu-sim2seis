from pathlib import Path

import numpy as np
import pytest
import xtgeo

from fmu.sim2seis.utilities import dump_result_objects, retrieve_result_objects


@pytest.fixture
def test_surfaces():
    """Fixture providing test surface dictionary."""
    nx, ny = 5, 5
    xinc, yinc = 100.0, 100.0
    xori, yori = 0.0, 0.0
    values = np.ones((ny, nx))

    surf1 = xtgeo.RegularSurface(
        ncol=nx,
        nrow=ny,
        xori=xori,
        yori=yori,
        xinc=xinc,
        yinc=yinc,
        values=values,  # type: ignore
    )

    surf2 = xtgeo.RegularSurface(
        ncol=nx,
        nrow=ny,
        xori=xori,
        yori=yori,
        xinc=xinc,
        yinc=yinc,
        values=values * 2,  # type: ignore
    )

    return {"surface1": surf1, "surface2": surf2}


def verify_loaded_surfaces(loaded_dict, original_dict):
    """Verify that loaded surfaces match the original ones."""
    assert isinstance(loaded_dict, dict)
    assert set(loaded_dict.keys()) == set(original_dict.keys())
    for key in original_dict:
        assert isinstance(loaded_dict[key], xtgeo.RegularSurface)
        np.testing.assert_array_equal(
            loaded_dict[key].values, original_dict[key].values
        )


def test_absolute_paths(tmp_path, test_surfaces, monkeypatch):
    """Test dumping and retrieving with absolute paths."""
    monkeypatch.chdir(tmp_path)

    output_dir = tmp_path / "results"
    file_name = Path("test_surfaces.pkl")

    dump_result_objects(output_dir.absolute(), file_name, test_surfaces)

    assert output_dir.exists()
    assert (output_dir / file_name).exists()

    loaded_dict = retrieve_result_objects(output_dir.absolute(), file_name)
    verify_loaded_surfaces(loaded_dict, test_surfaces)


def test_relative_paths(tmp_path, test_surfaces, monkeypatch):
    """Test dumping and retrieving with relative paths."""
    monkeypatch.chdir(tmp_path)

    output_dir = Path("./results")
    file_name = Path("test_surfaces.pkl")

    dump_result_objects(output_dir, file_name, test_surfaces)

    assert output_dir.exists()
    assert (output_dir / file_name).exists()

    loaded_dict = retrieve_result_objects(output_dir, file_name)
    verify_loaded_surfaces(loaded_dict, test_surfaces)


def test_error_on_readonly_dump(tmp_path):
    """Test error handling with read-only directory for dump."""
    output_dir = tmp_path / "readonly"
    output_dir.mkdir()
    output_dir.chmod(0o444)  # Read-only

    with pytest.raises(ValueError, match="unable to dump pickle objects"):
        dump_result_objects(output_dir, Path("test.pkl"), {"test": "data"})


def test_error_on_missing_file_retrieve(tmp_path):
    """Test error handling when trying to retrieve non-existent file."""
    with pytest.raises(ValueError, match="unable to load pickle objects"):
        retrieve_result_objects(tmp_path, Path("nonexistent.pkl"))
