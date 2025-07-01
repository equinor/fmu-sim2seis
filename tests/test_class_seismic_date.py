import pytest

from fmu.sim2seis.utilities import SeismicDate


def test_seismic_date_single():
    date = "20100101"
    date_obj = SeismicDate(date)
    assert date_obj.date == date


def test_seismic_date_fail():
    wrong_date = "20191399"
    with pytest.raises(ValueError):
        SeismicDate(wrong_date)


def test_seismic_date_diff():
    date = "20100101_20090101"
    date_obj = SeismicDate(date)
    assert date_obj.date == date


def test_date_setter():
    date = "20100101"
    date_obj = SeismicDate(date)
    assert date_obj.date == date
    new_date = "20200101"
    date_obj.date = new_date
    assert date_obj.date == new_date


def test_date_sort():
    monitor = "20100101"
    base = "20090101"
    unsorted_date = base + "_" + monitor
    sorted_date = monitor + "_" + base
    date_obj = SeismicDate(unsorted_date)
    assert date_obj.date == sorted_date
