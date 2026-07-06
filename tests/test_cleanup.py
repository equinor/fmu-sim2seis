from pathlib import Path

from fmu.sim2seis.cleanup import main as run_cleanup
from fmu.sim2seis.utilities import clear_result_objects

CONFIG_FILE = "sim2seis/model/sim2seis_combined_config.yml"

# A single-date cube is an intermediate file and should be removed by the
# cleanup, while a difference (two-date) cube is a final product and is kept.
SINGLE_DATE_CUBE = "seismic--amplitude_full_time--20200101.segy"
DIFF_CUBE = "seismic--amplitude_full_time--20200701_20200101.segy"


def _make_pickle_files(pickle_dir: Path) -> None:
    pickle_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "relai_123456789.pkl",
        "amplitude_123456789.pkl",
        "observed_data_123456789.pkl",
    ):
        pickle_dir.joinpath(name).touch()


def _make_cube_files(cube_dir: Path) -> None:
    cube_dir.mkdir(parents=True, exist_ok=True)
    cube_dir.joinpath(SINGLE_DATE_CUBE).touch()
    cube_dir.joinpath(DIFF_CUBE).touch()


def test_clear_result_objects_removes_all_pickle_files(data_dir):
    """All pickle files are removed - selective removal is no longer supported."""
    pickle_dir = data_dir / "share/results/pickle_files"
    _make_pickle_files(pickle_dir)
    pickle_dir.joinpath("not_a_likely_name_123456789.pkl").touch()

    clear_result_objects(output_path=pickle_dir)

    assert not list(pickle_dir.glob("*.pkl"))


def test_cleanup_default_removes_pickle_and_single_date_seismic(monkeypatch, data_dir):
    """Default run: remove pickle files and single-date seismic, keep difference."""
    monkeypatch.chdir(data_dir)
    pickle_dir = data_dir / "share/results/pickle_files"
    cube_dir = data_dir / "share/results/cubes"
    _make_pickle_files(pickle_dir)
    _make_cube_files(cube_dir)

    run_cleanup(["--config-file", CONFIG_FILE])

    assert not list(pickle_dir.glob("*.pkl"))
    assert not cube_dir.joinpath(SINGLE_DATE_CUBE).exists()
    assert cube_dir.joinpath(DIFF_CUBE).exists()

    cube_dir.joinpath(DIFF_CUBE).unlink()


def test_cleanup_include_seismic_false_keeps_seismic(monkeypatch, data_dir):
    """With --include-seismic false: pickle files are removed, cubes are kept."""
    monkeypatch.chdir(data_dir)
    pickle_dir = data_dir / "share/results/pickle_files"
    cube_dir = data_dir / "share/results/cubes"
    _make_pickle_files(pickle_dir)
    _make_cube_files(cube_dir)

    run_cleanup(["--config-file", CONFIG_FILE, "--include-seismic", "false"])

    assert not list(pickle_dir.glob("*.pkl"))
    assert cube_dir.joinpath(SINGLE_DATE_CUBE).exists()
    assert cube_dir.joinpath(DIFF_CUBE).exists()

    cube_dir.joinpath(SINGLE_DATE_CUBE).unlink()
    cube_dir.joinpath(DIFF_CUBE).unlink()


def test_cleanup_ensemble_removes_pickle_and_single_date_seismic(monkeypatch, data_dir):
    """Ensemble run: remove intermediate files in every realisation/iteration."""
    monkeypatch.chdir(data_dir)
    realisations = ["realization-0/iter-0", "realization-1/iter-0"]
    pickle_dirs = [
        data_dir / real / "share/results/pickle_files" for real in realisations
    ]
    cube_dirs = [data_dir / real / "share/results/cubes" for real in realisations]
    for pickle_dir in pickle_dirs:
        _make_pickle_files(pickle_dir)
    for cube_dir in cube_dirs:
        _make_cube_files(cube_dir)

    run_cleanup(["--config-file", CONFIG_FILE, "--is_ensemble", "true"])

    for pickle_dir in pickle_dirs:
        assert not list(pickle_dir.glob("*.pkl"))
    for cube_dir in cube_dirs:
        assert not cube_dir.joinpath(SINGLE_DATE_CUBE).exists()
        assert cube_dir.joinpath(DIFF_CUBE).exists()


def test_cleanup_ensemble_include_seismic_false_keeps_seismic(monkeypatch, data_dir):
    """Ensemble run with --include-seismic false: keep cubes, remove pickle files."""
    monkeypatch.chdir(data_dir)
    realisations = ["realization-0/iter-0", "realization-1/iter-0"]
    pickle_dirs = [
        data_dir / real / "share/results/pickle_files" for real in realisations
    ]
    cube_dirs = [data_dir / real / "share/results/cubes" for real in realisations]
    for pickle_dir in pickle_dirs:
        _make_pickle_files(pickle_dir)
    for cube_dir in cube_dirs:
        _make_cube_files(cube_dir)

    run_cleanup(
        [
            "--config-file",
            CONFIG_FILE,
            "--is_ensemble",
            "true",
            "--include-seismic",
            "false",
        ]
    )

    for pickle_dir in pickle_dirs:
        assert not list(pickle_dir.glob("*.pkl"))
    for cube_dir in cube_dirs:
        assert cube_dir.joinpath(SINGLE_DATE_CUBE).exists()
        assert cube_dir.joinpath(DIFF_CUBE).exists()
