from .sim2seis_config_validation import Sim2SeisConfig

"""
Originally from libseis by JRIV
"""


def get_pred_or_hist_seis_diff_dates(global_config: Sim2SeisConfig):
    """Get correct diffdates as list of date pairs as [["YYYYMMDD","YYYYMMDD"], ...]."""

    try:
        get_listed_seis_diff_dates(
            global_config["global"]["dates"]["SEISMIC_PRED_DIFFDATES"]
        )
    except KeyError:
        get_listed_seis_diff_dates(
            global_config["global"]["dates"]["SEISMIC_HIST_DIFFDATES"]
        )


def get_listed_seis_diff_dates(diff_dates):
    """Make diff dates as list of date pairs in list as [["YYYYMMDD","YYYYMMDD], ...]"""

    return [
        [str(sdate).replace("-", "") for sdate in date_pairs]
        for date_pairs in diff_dates
    ]


def get_listed_seis_dates(dates: list[str]) -> list[str]:
    """Make dates as list of dates on form ["YYYYMMDD", ...]."""

    return [str(s_date).replace("-", "") for s_date in dates]
