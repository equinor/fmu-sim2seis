import os
import time

import xtgeo
from si4ti import compute_impedance

from fmu.sim2seis.utilities import link_and_folder_utils as libgen


def run_by_si4ti():

    os.chdir(r"/scratch/fmu/hfle/fmu_sim2seis_pem/realization-0/iter-0/sim2seis/output/seismic_forward")

    start = time.time()
    cube1 = xtgeo.cube_from_file("syntseis--amplitude_far_depth--19960701.segy")
    cube2 = xtgeo.cube_from_file("syntseis--amplitude_far_depth--20110701.segy")

    _, _ = compute_impedance(
        input_cubes=[cube1, cube2],
    )
    end = time.time()
    elapsed = end - start
    print(f"si4ti: {elapsed:.2f} seconds")


def run_by_impedance():
    os.chdir(
        r"/scratch/fmu/hfle/fmu_sim2seis_pem/realization-0/iter-0/sim2seis/output/seismic_forward"
    )
    # run simpli
    start = time.time()
    _ = libgen.run_external_silent(
        [
            "/private/hfle/PycharmProjects/fmu-sim2seis/tests/data/sim2seis/bin/impedance",
            "-L 0.05",  # Lateral smoothing 4d
            "-D 0.001",  # Damping 3D
            "-d 0.001",  # Damping 4D
            "-l 0.01",  # Lateral smoothing 3D
            "-m 100",  # Max iterations
            "-s 1",  # Segments
            "-O",  # Output names
            "tmp_ai1",
            "tmp_ai2",
            "tmp_dsyn1",
            "tmp_dsyn2",
            "--",  # inputs
            "syntseis--amplitude_far_depth--19960701.segy",
            "syntseis--amplitude_far_depth--20110701.segy",
        ],
    )
    end = time.time()
    elapsed = end - start
    print(f"disk-based impedance: {elapsed:.2f} seconds")


if __name__ == "__main__":
    run_by_impedance()
    run_by_si4ti()
