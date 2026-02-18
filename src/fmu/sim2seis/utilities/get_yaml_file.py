from pathlib import Path

import yaml

from fmu.pem.pem_utilities import get_global_params_and_dates

from .sim2seis_config_validation import Sim2SeisConfig, Sim2SeisPaths


def _resolve_fmu_rootpath(config_dir: Path) -> Path:
    # Ensure config_dir is absolute before computing the FMU root to avoid
    # depending on the current working directory (common in CLI entrypoints).
    resolved_config_dir = (
        config_dir if config_dir.is_absolute() else config_dir.resolve()
    )

    # The sim2seis config directory is expected to be at ./sim2seis/model
    # relative to the FMU root, so we move up two levels. Use parents[1]
    # instead of appending "../.." to avoid mis-resolution of relative paths.
    try:
        return resolved_config_dir.parents[1]
    except IndexError:
        # Fallback for unexpected shallow directory structures: use the
        # immediate parent rather than failing outright.
        return resolved_config_dir.parent


def read_yaml_file(
    sim2seis_config_file: Path,
    sim2seis_config_dir: Path,
    global_config_file: Path | None = None,
    global_config_dir: Path | None = None,
    parse_inputs: bool = True,
    obs_prefix: str | None = None,
    mod_prefix: str | None = None,
) -> Sim2SeisConfig | dict:
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
        data = yaml.safe_load(f)
        # add information about the config file name
        data["config_file_name"] = sim2seis_config_file

        # If there is no information about global configuration, we can either
        # return a dict which is not parsed at all, or parse the YAML file without
        # adding the global configuration
        if not parse_inputs:
            return data

        # Build paths by merging YAML overrides with defaults
        paths_data = data.get("paths", {})
        paths_obj = Sim2SeisPaths.model_validate(paths_data)
        paths_obj.config_dir_sim2seis = sim2seis_config_dir
        paths_obj.fmu_rootpath = _resolve_fmu_rootpath(sim2seis_config_dir)
        data["paths"] = paths_obj

        conf = Sim2SeisConfig.model_validate(data, context={"paths": paths_obj})

        # Read necessary part of global configurations and parameters if there is
        # information about global file
        if global_config_dir and global_config_file:
            conf.update_with_global(
                get_global_params_and_dates(
                    global_config_dir=sim2seis_config_dir / global_config_dir,
                    global_conf_file=global_config_file,
                    obs_prefix=obs_prefix,
                    mod_prefix=mod_prefix,
                )
            )

    return conf
