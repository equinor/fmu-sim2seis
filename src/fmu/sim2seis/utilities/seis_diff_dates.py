from fmu.pem.pem_utilities import restore_dir

from .libseis import get_listed_seis_diff_dates
from .sim2seis_config_validation import Sim2SeisConfig


def get_pred_or_hist_seis_diff_dates(conf: Sim2SeisConfig):
    """Get correct diffdates as list of date pairs as [["YYYYMMDD","YYYYMMDD"], ...]."""

    with restore_dir(conf.rel_path_global_config):
        if conf.flowsim_is_prediction:
            use_dates = "SEISMIC_PRED_DIFFDATES"
        else:
            use_dates = "SEISMIC_HIST_DIFFDATES"

        global_config = conf.global_params.global_config

        return get_listed_seis_diff_dates(global_config["global"]["dates"][use_dates])
