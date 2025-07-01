import pytest

from fmu.sim2seis.utilities import SeismicName

date = "20200101"
domain = "depth"
stack = "full"
attribute = "relai"
process = "seismic"
ext = "segy"


def test_seismic_name_init():
    seis_name_obj = SeismicName(
        date=date,
        process=process,  # type: ignore
        stack=stack,  # type: ignore
        domain=domain,  # type: ignore
        attribute=attribute  # type: ignore
    )
    assert isinstance(seis_name_obj,SeismicName)
    assert seis_name_obj.attribute == attribute
    assert seis_name_obj.date == date
    assert seis_name_obj.domain == domain
    assert seis_name_obj.process == process
    assert seis_name_obj.stack == stack


def test_seismic_name_parse_str():
    name_str = "seismic--relai_depth--20101001.segy"
    seis_name_obj = SeismicName.parse_name(name_str)
    assert str(seis_name_obj) == name_str


def test_seismic_name_errors():
    name_str = "synthetic--relai_depth--20101001.segy"
    with pytest.raises(ValueError):
        SeismicName.parse_name(name_str)


def test_seismic_name_property_types():
    seis_name_obj = SeismicName(
        date=date,
        process=process,  # type: ignore
        stack=stack,  # type: ignore
        domain=domain,  # type: ignore
        attribute=attribute,  # type: ignore
        ext=ext,
    )
    assert isinstance(seis_name_obj.process, str) and (
        seis_name_obj.process == process
    )
    assert isinstance(seis_name_obj.attribute, str) and (
        seis_name_obj.attribute == attribute
    )
    assert isinstance(seis_name_obj.domain, str) and (
        seis_name_obj.domain == domain
    )
    assert isinstance(seis_name_obj.date, str) and (
        seis_name_obj.date == date
    )
    assert isinstance(seis_name_obj.ext, str) and (
        seis_name_obj.ext == ext
    )


def test_seismic_name_hash():
    name1 = SeismicName(
        date="20200101",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )
    name2 = SeismicName(
        date="20200101",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )
    name3 = SeismicName(
        date="20200102",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )

    # Check that the hash values of name1 and name2 are the same
    assert hash(name1) == hash(name2)

    # Check that the hash values of name1 and name3 are different
    assert hash(name1) != hash(name3)


def test_seismic_name_str():
    name_str = "seismic--relai_full_depth--20200101.segy"
    seis_name_obj = SeismicName(
        date="20200101",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )
    assert str(seis_name_obj) == name_str


def test_seismic_name_eq():
    name1 = SeismicName(
        date="20200101",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )
    name2 = SeismicName(
        date="20200101",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )
    name3 = SeismicName(
        date="20200102",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )

    assert name1 == name2
    assert name1 != name3


def test_seismic_name_iter():
    seis_name_obj = SeismicName(
        date="20200101",
        process="seismic",  # type: ignore
        stack="full",  # type: ignore
        domain="depth",  # type: ignore
        attribute="relai",  # type: ignore
        ext="segy"
    )
    properties = list(seis_name_obj)
    expected_properties = ["seismic", "relai", "depth", "full", "20200101"]
    assert properties == expected_properties


def test_compare_without_date():
    name_str = "seismic--relai_full_depth--20200101.segy"
    seis_name_obj = SeismicName.parse_name(name_str)

    # Test with matching string without date
    assert seis_name_obj.compare_without_date("seismic--relai_full_depth")

    # Test with string that has no date
    assert not seis_name_obj.compare_without_date("syntseis--relai_full_depth")

    # Test with matching string with trailing dashes
    assert seis_name_obj.compare_without_date("seismic--relai_full_depth--")

    # Test with a date in the name, both the same and different date should match
    name1 = "seismic--relai_full_depth--20200707.segy"  # Different date
    name2 = "seismic--relai_full_depth--20200101.segy"  # Same date
    assert seis_name_obj.compare_without_date(name1)
    assert seis_name_obj.compare_without_date(name2)


def test_compare_without_date_different_dates():
    name_str1 = "seismic--relai_full_depth--20200101.segy"
    name_str2 = "seismic--relai_full_depth--20200102.segy"
    seis_name_obj1 = SeismicName.parse_name(name_str1)
    seis_name_obj2 = SeismicName.parse_name(name_str2)

    # Test that the comparison without date returns True
    assert seis_name_obj1.compare_without_date(str(seis_name_obj2))
    assert seis_name_obj2.compare_without_date(str(seis_name_obj1))
