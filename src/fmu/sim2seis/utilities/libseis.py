"""
Various common routines related to seismic work flows.

NB! When editing this, always save the full project to make edits available!

JRIV
"""

from typing import List


def get_listed_seis_dates(dates: List[str]) -> List[str]:
    """Make dates as list of dates on form ["YYYYMMDD", ...]."""

    return [str(s_date).replace("-", "") for s_date in dates]


def get_listed_seis_diff_dates(diff_dates):
    """Make diff dates as list of date pairs in list as [["YYYYMMDD","YYYYMMDD], ...]"""

    return [
        [str(sdate).replace("-", "") for sdate in date_pairs]
        for date_pairs in diff_dates
    ]
