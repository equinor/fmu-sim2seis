import os
from pathlib import Path
from shutil import copy2

from fmu.sim2seis.utilities import clear_result_objects


def test_pickle_cleanup(monkeypatch, data_dir):
    monkeypatch.chdir(data_dir / r"share/results/pickle_files")
    pickle_dir = Path.cwd()

    # Ensure that there is something to remove
    pickle_dir.joinpath("relai_123456789.pkl").touch()
    pickle_dir.joinpath("amplitude_123456789.pkl").touch()

    clear_result_objects(output_path=pickle_dir, prefix_list=["relai", "amplitude"])
    assert (not list(pickle_dir.glob("relai*.pkl")) and
            not list(pickle_dir.glob("amplitude*.pkl")))

def test_pickle_cleanup_all(monkeypatch, data_dir):
    monkeypatch.chdir(data_dir  / r"share/results/pickle_files")
    pickle_dir = Path.cwd()

    # Ensure that there is something to remove
    pickle_dir.joinpath("relai_123456789.pkl").touch()
    pickle_dir.joinpath("amplitude_123456789.pkl").touch()
    pickle_dir.joinpath("not_a_likely_name_123456789.pkl").touch()

    clear_result_objects(output_path=pickle_dir)
    assert not list(pickle_dir.glob("*.pkl"))


def test_pickle_cleanup_observed_data(monkeypatch, data_dir):
    monkeypatch.chdir(data_dir  / r"share/results/pickle_files")
    pickle_dir = Path.cwd()

    # Ensure that there is something to remove
    pickle_dir.joinpath("observed_data_123456789.pkl").touch()
    pickle_dir.joinpath("not_a_likely_name_123456789.pkl").touch()

    clear_result_objects(output_path=pickle_dir)
    assert not list(pickle_dir.glob("*.pkl"))


def test_pickle_cleanup_main_script(monkeypatch, data_dir):
    import subprocess
    monkeypatch.chdir(data_dir / "rms/model")
    status = subprocess.run([
        "sim2seis_cleanup",
        "--startdir", data_dir / "rms/model",
        "--configdir",
        "../../sim2seis/model",
        "--configfile",
        "sim2seis_config.yml",
        "--prefixlist",
        "relai"
    ])
    assert status.returncode == 0
