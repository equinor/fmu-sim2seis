from pathlib import Path

import yaml

from fmu.pem.pem_utilities import get_global_params_and_dates

from .obs_data_config_validation import ObservedDataConfig
from .sim2seis_config_validation import Sim2SeisConfig


def read_yaml_file(
    file_name: Path,
    start_dir: Path,
    update_with_global: bool = True,
    parse_inputs: bool = True,
) -> Sim2SeisConfig | ObservedDataConfig | dict:
    """Read the YAML file and return the configuration."""

    with open(file_name) as f:

        def join(loader, node):
            seq = loader.construct_sequence(node)
            return "".join([str(i) for i in seq])

        # register the tag handler
        yaml.add_constructor("!join", join)
        data = yaml.load(f, Loader=yaml.Loader)
        # add information about the config file name
        data["config_file_name"] = file_name

        if not parse_inputs:
            return data

        if "observed_depth_surf" in data:
            conf = ObservedDataConfig(**data)
        elif "seismic_fwd" in data:
            conf = Sim2SeisConfig(**data)
        else:
            raise ValueError("Configuration not recognized")

        # Read necessary part of global configurations and parameters
        if update_with_global:
            conf.update_with_global(
                get_global_params_and_dates(start_dir, conf.rel_path_global_config)
            )

    return conf
