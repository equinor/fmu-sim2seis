import os
from pathlib import Path

import yaml

from fmu.pem.pem_utilities import get_global_params_and_dates, restore_dir

from .sim2seis_config_validation import Sim2SeisConfig, Sim2SeisPaths


# ToDo: import this from fmu-pem once it is part of main
def _resolve_fmu_rootpath(config_dir: Path) -> Path:
    # First: establish if we run from ERT, if so use the RUNPATH
    if os.environ.get("_ERT_RUNPATH", None):
        return Path(os.environ.get("_ERT_RUNPATH"))

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
        # If this is the case, the argument for config_dir must be wrong, and
        # it's better to raise an error than to continue
        raise ValueError(
            f"unable to find fmu rootpath from config_dir: {resolved_config_dir}"
        )


def read_yaml_file(
    sim2seis_config_file: Path,
    sim2seis_config_dir: Path,
    global_config_file: Path | None = None,
    global_config_dir: Path | None = None,
    parse_inputs: bool = True,
    obs_prefix: str | None = None,
    mod_prefix: str | None = None,
    pre_experiment: bool = False,
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
    pre_experiment : bool, optional
        when True, file-system validators that depend on realization-specific
        directories or files are skipped. Config-resident paths (e.g. stack
        model XMLs, ``twt_model``, ``attribute_map_definition_file``, WebvizMap
        grid files) are still validated against ``config_dir_sim2seis``. Intended
        for ERT's ``validate_pre_experiment`` hook, where realization directories
        have not yet been created. By default False.

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

        # If there is no information about global configuration, we can either
        # return a dict which is not parsed at all, or parse the YAML file without
        # adding the global configuration
        if not parse_inputs:
            return data

        # Build paths by merging YAML overrides with defaults.
        # In pre_experiment mode, directory-existence checks are skipped so that
        # ERT can validate config parameters before realization dirs are created.
        with restore_dir(_resolve_fmu_rootpath(sim2seis_config_dir)):
            validation_context: dict = {"pre_experiment": pre_experiment}
            paths_data = data.get("paths", {})
            paths_obj = Sim2SeisPaths.model_validate(
                paths_data, context=validation_context
            )
            paths_obj.config_dir_sim2seis = sim2seis_config_dir
            paths_obj.fmu_rootpath = _resolve_fmu_rootpath(sim2seis_config_dir)
            data["paths"] = paths_obj

            validation_context["paths"] = paths_obj
            conf = Sim2SeisConfig.model_validate(data, context=validation_context)

            # Read necessary part of global configurations and parameters if there is
            # information about global file
            if global_config_dir and global_config_file:
                conf.update_with_global(
                    get_global_params_and_dates(
                        global_config_dir=global_config_dir,
                        global_conf_file=global_config_file,
                        obs_prefix=obs_prefix,
                        mod_prefix=mod_prefix,
                    )
                )

    return conf
