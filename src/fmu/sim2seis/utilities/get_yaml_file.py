from pathlib import Path

import yaml

from fmu.pem.pem_utilities import get_global_params_and_dates

from .obs_data_config_validation import ObservedDataConfig
from .sim2seis_config_validation import Sim2SeisConfig


def read_yaml_file(
    sim2seis_config_file: Path,
    sim2seis_config_dir: Path,
    global_config_file: Path | None = None,
    global_config_dir: Path | None = None,
    parse_inputs: bool = True,
) -> Sim2SeisConfig | ObservedDataConfig | dict:
    """Read the YAML file and return the configuration.

    Parameters
    ----------
    sim2seis_config_file : Path
        configuration file in yaml format
    sim2seis_config_dir : Path
        directory of configuration file
    global_config_file : Path
        global configuration file in yaml format
    global_config_dir : Path
        directory of global configuration file
    parse_inputs : bool, optional
        if this is set to false, file is read, but there is no parsing of
        parameter object, by default True

    Returns
    -------
    Sim2SeisConfig | ObservedDataConfig | dict
        pydantic validation objects

    Raises
    ------
    ValueError
        raises ValueError in case it is not possible to parse the yaml file content
    """

    with open(sim2seis_config_dir / sim2seis_config_file) as f:

        def join(loader, node):
            seq = loader.construct_sequence(node)
            return "".join([str(i) for i in seq])

        # register the tag handler
        yaml.add_constructor("!join", join)
        data = yaml.load(f, Loader=yaml.Loader)
        # add information about the config file name
        data["config_file_name"] = sim2seis_config_file

        # If there is not information about global configuration, we can't
        # parse the information, just return a dict from the yaml file
        if not global_config_file:
            assert not parse_inputs

        if not parse_inputs:
            return data

        # if "observed_depth_surf" in data:
        #     conf = ObservedDataConfig(**data)
        # elif "seismic_fwd" in data:
        #     conf = Sim2SeisConfig(**data)
        # else:
        #     raise ValueError("Configuration not recognized")
        conf = Sim2SeisConfig(**data)

        # Read necessary part of global configurations and parameters
        conf.update_with_global(
            get_global_params_and_dates(
                global_config_dir=sim2seis_config_dir / global_config_dir,
                global_conf_file=global_config_file,
            )
        )

    return conf
