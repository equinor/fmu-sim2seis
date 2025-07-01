from pathlib import Path
from typing import List, Optional

from pydantic import (
    BaseModel,
    DirectoryPath,
    Field,
    field_validator,
)

from fmu.pem.pem_utilities.pem_config_validation import (
    FromGlobal,
)

from .sim2seis_config_validation import WebvizMap


class DepthSurface(BaseModel):
    """Class for depth surface configuration."""

    horizon_names: List[str]
    suffix_name: str
    depth_dir: DirectoryPath = Path("../../share/observations/maps")


class TimeData(BaseModel):
    """Class for time surfaces and time cubes"""

    time_cube_dir: DirectoryPath = Path("../../share/observations/cubes")
    time_cube_prefix: str = "seismic--"
    time_suffix: str = "--time.gri"
    horizon_dir: DirectoryPath = Path("../../share/observations/maps")


class DepthConversion(BaseModel):
    """Class for depth conversion of observed seismic cubes"""

    min_depth: int = Field(ge=0)
    max_depth: int = Field(gt=0)
    z_inc: int = Field(gt=0)


class ObservedDataConfig(BaseModel):
    attribute_definition_file: Path
    test_run: bool = False
    depth_conversion: DepthConversion
    global_params: Optional[FromGlobal] = None
    observed_depth_surf: DepthSurface
    observed_time_data: TimeData = Field(default_factory=TimeData)
    pickle_file_output_path: DirectoryPath = Path(
        "../../share/observations/pickle_files"
    )
    pickle_file_prefix: str = "observed_data"
    rel_path_global_config: DirectoryPath = Path("../../fmuconfig/output")
    observed_data_path: DirectoryPath = Path("../../share/observations/cubes")
    webviz_map: WebvizMap

    @field_validator("pickle_file_output_path", mode="before")
    def check_pickle_dir_exists(csl, v):
        v.mkdir(parents=True, exist_ok=True)
        return v

    # Add global parameters used in sim2seis
    def update_with_global(self, global_params: dict):
        self.global_params = FromGlobal(**global_params)
        return self
