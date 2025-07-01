"""
Class definitions for sim2seis workflow
"""

import copy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import (
    Literal,
    Optional,
    Self,
    Tuple,
    get_args,
)

import numpy as np
import xtgeo


class SeismicDate:
    def __init__(self, value: str):
        self._single_date: datetime | None = None
        self._diff_date: Tuple[datetime, datetime] | None = None
        self._set_dates(value)

    def _set_dates(self, value: str | Self):
        try:
            if isinstance(value, SeismicDate):
                self._copy_from_other_date(value)
            elif "_" in value:
                self._parse_differential_date(value)
            else:
                self._parse_single_date(value)
        except ValueError as e:
            raise ValueError(f"Error parsing date: {e}")

    def _copy_from_other_date(self, other: Self):
        self._single_date = other._single_date
        self._diff_date = other._diff_date

    def _parse_single_date(self, value: str):
        self._single_date = datetime.strptime(value, "%Y%m%d")
        self._diff_date = None

    def _parse_differential_date(self, value: str):
        dates = value.split("_")
        if len(dates) != 2:
            raise ValueError("Invalid date range format - must have exactly two dates")

        date1 = datetime.strptime(dates[0], "%Y%m%d")
        date2 = datetime.strptime(dates[1], "%Y%m%d")

        # Monitor date is the later date, base date is the earlier date
        monitor_date = max(date1, date2)
        base_date = min(date1, date2)

        self._diff_date = (monitor_date, base_date)
        self._single_date = None

    @property
    def date(self) -> str:
        if self._single_date:
            return self._single_date.strftime("%Y%m%d")
        if self._diff_date:
            return "_".join(date.strftime("%Y%m%d") for date in self._diff_date)
        return ""

    @date.setter
    def date(self, value: Self | str):
        self._set_dates(value)

    @property
    def monitor_date(self) -> str | None:
        if self._diff_date is not None:
            return self._diff_date[0].strftime("%Y%m%d")
        return None

    @property
    def base_date(self) -> str | None:
        if self._diff_date is not None:
            return self._diff_date[1].strftime("%Y%m%d")
        return None


# Define literals
ProcessDef = Literal["seismic", "syntseis"]
AttributeDef = Literal["amplitude", "relai"]
DomainDef = Literal["time", "depth"]
StackDef = Literal["full", "near", "mid", "far"]


class SeismicName(SeismicDate):
    def __init__(
        self,
        process: ProcessDef,
        attribute: AttributeDef,
        domain: DomainDef,
        date: SeismicDate | str,
        stack: None | StackDef = None,
        ext: str | None = None,
    ):
        super().__init__(date)
        self._process = process
        self._attribute = attribute
        self._domain = domain
        self._stack = stack
        self._ext = ext

    def __str__(self):
        stack = "" if self._stack is None else self._stack + "_"
        date = "" if self.date is None else "--" + self.date
        ext = "" if self._ext is None else "." + self._ext
        return (
            self._process
            + "--"
            + self._attribute
            + "_"
            + stack
            + self._domain
            + date
            + ext
        )

    def __eq__(self, other):
        return (
            (self._process == other.process)
            and (self._attribute == other.attribute)
            and (self._domain == other.domain)
            and (self._stack == other.stack)
            and (self.date == other.date)
        )

    def __iter__(self):
        for prop in (
            self._process,
            self._attribute,
            self._domain,
            self._stack,
            self.date,
        ):
            yield prop

    def __hash__(self):
        return hash(
            (
                self.process,
                self.attribute,
                self.domain,
                self.stack,
                self.date,
            )
        )

    @property
    def process(self) -> ProcessDef:
        return self._process

    @property
    def attribute(self) -> AttributeDef:
        return self._attribute

    @property
    def domain(self) -> DomainDef:
        return self._domain

    @property
    def stack(self) -> None | StackDef:
        if self._stack is None:
            return None
        return self._stack

    @property
    def ext(self) -> None | str:
        if self._ext is None:
            return None
        return self._ext

    def compare_without_date(self, value: str) -> bool:
        if value.endswith("--"):
            value_without_date = value[:-2]
        elif len(value.split("--")[:-1]) == 1:
            value_without_date = value
        else:
            value_without_date = "--".join(value.split("--")[:-1])
        str_without_date = "--".join(str(self).split("--")[:-1])
        return str_without_date == value_without_date

    @staticmethod
    def parse_name(value):
        if isinstance(value, SeismicName):
            return value
        if isinstance(value, str):
            try:
                proc, attr_stack_domain, date_ext = value.split("--")
                date_ext = date_ext.split(".")
                date = date_ext[0]
                ext = date_ext[1] if len(date_ext) > 1 else None
                attr, *stack_domain = attr_stack_domain.split("_")
                stack = stack_domain[0] if len(stack_domain) > 1 else None
                domain = stack_domain[-1]

                # Validate literal types
                if proc not in get_args(ProcessDef):
                    raise ValueError(f"Invalid process: {proc}")
                if attr not in get_args(AttributeDef):
                    raise ValueError(f"Invalid attribute: {attr}")
                if domain not in get_args(DomainDef):
                    raise ValueError(f"Invalid domain: {domain}")
                if not ((stack is None) or (stack in get_args(StackDef))):
                    raise ValueError(f"Invalid domain: {stack}")

                return SeismicName(
                    process=proc,  # type: ignore
                    attribute=attr,  # type: ignore
                    stack=stack,
                    domain=domain,
                    date=date,  # type: ignore
                    ext=ext,
                )
            except ValueError as e:
                raise ValueError(
                    f"{__file__}: could not parse cube name: {value},error message: {e}"
                )
        else:
            raise ValueError(f"wrong argument type: {type(value)}")


class SingleSeismic:
    def __init__(
        self,
        from_dir: Path,
        cube_name: SeismicName,
        cube: xtgeo.Cube,
        date: str | SeismicDate,
    ):
        self._from_dir = from_dir
        self._cube_name = SeismicName.parse_name(cube_name)
        self._cube = cube
        self._date = SeismicDate(date)

    @property
    def date(self) -> str:
        return self._date.date

    @date.setter
    def date(self, value: str | SeismicDate):
        if isinstance(value, SeismicDate):
            self._date = value
        else:
            self._date = SeismicDate(value)

    @property
    def monitor_date(self) -> str | None:
        return self._date.monitor_date

    @property
    def base_date(self) -> str | None:
        return self._date.base_date

    @property
    def from_dir(self) -> Path:
        return self._from_dir

    @from_dir.setter
    def from_dir(self, value: Path):
        self._from_dir = value

    @property
    def cube_name(self) -> SeismicName:
        return self._cube_name

    @cube_name.setter
    def cube_name(self, value: Path):
        self._cube_name = SeismicName.parse_name(value)

    @property
    def cube(self) -> xtgeo.Cube:
        return self._cube

    @cube.setter
    def cube(self, value: xtgeo.Cube):
        self._cube = value


@dataclass
class DifferenceSeismic:
    base: SingleSeismic
    monitor: SingleSeismic
    cube_name: SeismicName | None = None

    def __post_init__(self):
        # Ensure base and monitor are instances of SingleSeismic
        assert isinstance(self.base, SingleSeismic)
        assert isinstance(self.monitor, SingleSeismic)
        # Generate a name property
        self.cube_name = copy.deepcopy(self.monitor.cube_name)
        self.cube_name.date = "_".join([self.monitor.date, self.base.date])

        # Compliance check for base and monitor cubes
        assert np.all(self.base.cube.ilines == self.monitor.cube.ilines)
        assert np.all(self.base.cube.xlines == self.monitor.cube.xlines)
        assert np.all(self.base.cube.dimensions == self.monitor.cube.dimensions)
        assert self.base.cube.xori == self.monitor.cube.xori
        assert self.base.cube.yori == self.monitor.cube.yori
        assert self.base.cube.zori == self.monitor.cube.zori
        assert self.base.cube.rotation == self.monitor.cube.rotation

    @property
    def date(self) -> str:
        return self.cube_name.date

    @property
    def monitor_date(self) -> str:
        return self.monitor.date

    @property
    def base_date(self) -> str:
        return self.base.date

    @property
    def cube(self) -> xtgeo.Cube:
        diff_values = self.monitor.cube.values - self.base.cube.values
        diff_obj = copy.deepcopy(self.monitor)
        diff_obj.cube.values = diff_values
        return diff_obj.cube


KnownAttributes = Literal[
    "max",
    "min",
    "rms",
    "mean",
    "var",
    "maxpos",
    "maxneg",
    "maxabs",
    "sumpos",
    "sumneg",
    "meanabs",
    "meanpos",
    "meanneg",
    "upper",
    "lower",
]


@dataclass
class SeismicAttribute:
    surface: xtgeo.RegularSurface
    calc_types: KnownAttributes | list[KnownAttributes]
    from_cube: SingleSeismic | DifferenceSeismic
    domain: Literal["depth", "time"]
    scale_factor: float = 1.0
    window_length: Optional[float] = None
    base_surface: xtgeo.RegularSurface | None = None
    top_surface_shift: float = 0.0  # Use signed values for shift
    base_surface_shift: float = 0.0  # Use signed values for shift
    info: dict | None = None

    def __post_init__(self):
        # Need to verify that either a base surface or a window length is defined
        # Adjust the top and base surface according to the shift values
        if self.base_surface is None:
            assert self.window_length is not None
            # Calculate the base surface from the top surface and window length.
            # Take the top surface shift into consideration to get the window length
            # correct
            self.base_surface = (
                self.surface + self.top_surface_shift + self.window_length
            )
            # It makes no sense to have a shift value for the base unless it is given
            # as a surface
            self.base_surface_shift = 0.0
        if isinstance(self.calc_types, str):
            assert self.calc_types in get_args(KnownAttributes)
        else:
            for calc in self.calc_types:
                assert calc in get_args(KnownAttributes)

    @property
    def value(self) -> list[xtgeo.RegularSurface]:
        attributes = self.from_cube.cube.compute_attributes_in_window(
            self.surface + self.top_surface_shift,
            self.base_surface + self.base_surface_shift,
        )
        return [attributes[str(calc)] * self.scale_factor for calc in self.calc_types]  # type: ignore
