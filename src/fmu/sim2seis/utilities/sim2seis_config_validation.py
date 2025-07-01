from pathlib import Path
from typing import List, Optional

import xtgeo
from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    FilePath,
    field_validator,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Annotated, Self, get_args

from fmu.pem.pem_utilities.pem_config_validation import FromGlobal

from .sim2seis_class_definitions import (
    AttributeDef,
    DomainDef,
    StackDef,
)

# SkipJsonSchema is used in cases where it is not expected that a user needs to
# modify default values, and the class/property is therefore hidden from the
# interface.

class SeismicForward(BaseModel):
    model_config = ConfigDict(title="Seismic forward modelling")
    attribute: SkipJsonSchema[AttributeDef] = Field(
        default="amplitude",
        description="Default value for results of a seismic forward model "
        "is 'amplitude'",
    )
    pem_output_dir: SkipJsonSchema[DirectoryPath] = Field(
        default=Path("../../sim2seis/output/pem"),
        description="Folder for results from sim2seis. All folder "
        "references in the FMU structure are relative to "
        "./rms/model, where '.' is the top folder in each "
        "realization",
    )
    pickle_file_prefix: SkipJsonSchema[str] = Field(
        default="seismic_fwd",
        description="Pickle files are intermediate save formats in "
        "sim2seis. Each task has its own prefix for "
        "identification",
    )
    segy_depth: SkipJsonSchema[Path] = Field(
        default=Path("syntseis_temp_seismic_depth_stack.segy"),
        description="Seismic forward model writes temporary segy files "
        "to disk. The name must correspond to the setting in "
        "the XML files for each partial or full stack that "
        "is generated. Check the 'stack models' files",
    )
    seismic_output_dir: SkipJsonSchema[DirectoryPath] = Field(
        default=Path("../../share/results/cubes"),
        description="The standard folder for resulting cubes is controlled "
        "through the use of fmu-dataio. This folder refers to "
        "the intermediate files from seismic forward modelling",
    )
    stack_model_path: SkipJsonSchema[DirectoryPath] = Field(
        default=Path("../../sim2seis/model/"),
        description="Folder for the XML model files listed in 'stack_models'",
    )
    stack_models: dict[StackDef, Path] = Field(
        description="XML files describing modelling of partial or full stack. "
        "The parameters in the files should reflect the case, e.g. "
        "settings for Vp, Vs and Density for the depth intervals. "
        "Documentation to XML tags and values are found in  "
        "https://github.com/equinor/seismic-forward/blob/main/doc/Seismic_Forward_usermanual_ver_4.3.pdf"
    )
    twt_model: SkipJsonSchema[FilePath] = Field(
        default=Path("../../sim2seis/model/model_file_twt.xml"),
        description="The first run of seismic forward sets up a depth/time "
        "relationship, and a 2D map in 'storm' format is generated. "
        "This map shows the TWT timeshift if the base case ",
    )

    @field_validator("attribute", mode="before")
    def check_attribute(cls, v: str):
        if v not in get_args(AttributeDef):
            raise ValueError(f"Invalid attribute: {v}")
        return v

    @model_validator(mode="after")
    def check_seismic_fwd(self) -> Self:
        for key, value in self.stack_models.items():
            self.stack_models[key] = self.stack_model_path / value
            if not self.stack_models[key].is_file():
                raise ValueError(
                    f"stack model file {value.name} is not present in "
                    f"directory {self.stack_model_path.name}"
                )
        if not self.pem_output_dir.is_dir():
            raise ValueError(
                f"pem_output_dir: {str(self.seismic_output_dir)} is not a directory"
            )
        if not self.twt_model.is_file():
            raise ValueError(f"twt_model: {str(self.seismic_output_dir)} is not a file")

        return self


class SeismicDiff(BaseModel):
    pickle_file_prefix: str = Field(
        default="seismic_fwd_diff",
        description="Pickle files are intermediate save formats in "
        "sim2seis. Each task has its own prefix for "
        "identification",
    )


class DepthConvertConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, title="Depth Conversion")
    depth_cube_dir: SkipJsonSchema[DirectoryPath] = Field(
        default=Path("../../share/results/cubes"),
        description="The standard folder for resulting cubes is controlled "
        "through the use of fmu-dataio",
    )
    depth_suffix: SkipJsonSchema[str] = Field(
        default="--depth.gri",
        description="Horizon names used in time to depth conversion "
        "have extension '.gri', of type RMS binary, with "
        "name ending on '--depth'",
    )
    horizon_dir: DirectoryPath = Field(
        default=Path("../../share/results/maps"),
        description="The standard folder for horizons both of time and depth domain",
    )
    horizon_names: List[str] = Field(
        description="Horizons should be of type RMS binary, but with extension "
        "'.gri' to avoid confusion with other '.bin' files. "
        "The naming standard is to have lower-case letters "
        "in the name, and a suffix of '--depth' or '--time'"
    )
    min_depth: int = Field(
        description="For the depth converted cubes: minimum depth in meters"
    )
    max_depth: int = Field(
        description="For the depth converted cubes: maximum depth in meters"
    )
    z_inc: int = Field(
        description="For the depth converted cubes: depth increment in meters"
    )
    min_time: int = Field(
        description="For the time converted cubes: minimum time in milliseconds"
    )
    max_time: int = Field(
        description="For the time converted cubes: maximum time in milliseconds"
    )
    t_inc: int = Field(
        description="For the time converted cubes: time increment in milliseconds"
    )
    time_cube_dir: SkipJsonSchema[DirectoryPath] = Field(
        default=Path("../../share/results/cubes"),
        description="The standard folder for resulting cubes is controlled "
        "through the use of fmu-dataio",
    )
    time_suffix: SkipJsonSchema[str] = Field(
        default="--time.gri",
        description="Horizon names used in time to depth conversion "
        "have extension '.gri', of type RMS binary, with "
        "name ending on '--depth'",
    )

    @model_validator(mode="after")
    def check_depth_and_time(self) -> Self:
        max_depth = self.max_depth
        min_depth = self.min_depth
        z_inc = self.z_inc
        if max_depth is not None and min_depth is not None:
            if max_depth <= 0:
                raise ValueError("max_depth must be greater than 0")
            if max_depth <= min_depth:
                raise ValueError("max_depth must be greater than min_depth")
            if (max_depth - min_depth) % z_inc != 0:
                raise ValueError("max_depth minus min_depth must be divisible by z_inc")

        max_time = self.max_time
        min_time = self.min_time
        t_inc = self.t_inc
        if max_time is not None and min_time is not None:
            if max_time <= 0:
                raise ValueError("max_time must be greater than 0")
            if max_time <= min_time:
                raise ValueError("max_time must be greater than min_time")
            if (max_time - min_time) % t_inc != 0:
                raise ValueError("max_time minus min_time must be divisible by t_inc")
        if not self.time_cube_dir.is_dir():
            raise ValueError(
                f"time_cube_dir must be a directory, is {self.time_cube_dir}"
            )
        if not self.depth_cube_dir.is_dir():
            raise ValueError(
                f"depth_cube_dir must be a directory, is {self.depth_cube_dir}"
            )
        return self


class InversionMapConfig(BaseModel):
    attribute: AttributeDef = Field(
        default="relai",
        description="In inversion based attributed, 'relai' is the default prefix. "
        "Changing it to other values may cause downstream problems",
    )
    pickle_file_prefix: str = Field(
        default="relai_maps",
        json_schema_extra={"readOnly": True},
        description="Pickle files are intermediate save formats in "
        "sim2seis. Each task has its own prefix for "
        "identification",
    )


class AmplitudeMapConfig(BaseModel):
    attribute: AttributeDef = Field(
        default="amplitude",
        description="Default value for results of a seismic forward model "
        "is 'amplitude'",
    )
    pickle_file_prefix: str = Field(
        default="amplitude_maps",
        description="Pickle files are intermediate save formats in "
        "sim2seis. Each task has its own prefix for "
        "identification",
    )


class WebvizMap(BaseModel):
    grid_path: DirectoryPath = Field(
        default=Path("../../sim2seis/input/pem"),
        description="This directory is the standard place for grid definition files",
    )
    grid_file: Path = Field(
        default=Path("simgrid.roff"),
        description="The file name for grid definition file, 'roff' format is normally "
        "used"
    )
    zone_file: Path = Field(
        default=Path("simgrid--zone.roff"),
        description="The file name for zone definition file, 'roff' format is normally "
        "used"
    )
    region_file: Path = Field(
        default=Path("simgrid--region.roff"),
        description="The file name for region definition file, 'roff' format is "
        "normally used"
    )
    attribute_error: float | Path = Field(
        description="Attribute error is normally given as a fractional number, "
        "but it can also be given as a surface with polygon information "
        "where each polygon has its own attribute error. Full path and "
        "name to the surface file must be given, and the file format "
        "must be recognised by xtgeo",
    )
    output_path: SkipJsonSchema[DirectoryPath] = Field(
        default=Path(r"../../share/results/tables"),
        description="Ascii files for WebViz or ERT are written to this directory",
    )

    @field_validator("grid_file", mode="before")
    def grid_file_check(cls, v: str, values: ValidationInfo):
        full_name = values.data.get("grid_path").joinpath(v)
        if not full_name.is_file():
            raise ValueError(f"webvisMap: {str(full_name)} is not a file")
        return Path(v)

    @field_validator("zone_file", mode="before")
    def zone_file_check(cls, v: str, values: ValidationInfo):
        full_name = values.data.get("grid_path").joinpath(v)
        if not full_name.is_file():
            raise ValueError(f"webvisMap: {str(full_name)} is not a file")
        return Path(v)

    @field_validator("region_file", mode="before")
    def region_file_check(cls, v: str, values: ValidationInfo):
        full_name = values.data.get("grid_path").joinpath(v)
        if not full_name.is_file():
            raise ValueError(f"webvisMap: {str(full_name)} is not a file")
        return Path(v)

    @field_validator("attribute_error", mode="before")
    def attribute_error_check(cls, v: float | Path):
        if isinstance(v, float):
            assert v > 0.0
            assert v < 1.0
            return v
        assert v.is_file()
        try:
            _ = xtgeo.surface_from_file(v)
        except ValueError:
            raise ValueError(f"attribute error surface file not recognised: {v}")
        return v

    @model_validator(mode="after")
    def output_path_check(self) -> Self:
        if not self.output_path.is_dir():
            raise ValueError(f"output_path: {str(self.output_path)} is not a directory")
        return self


class InversionParameters(BaseModel):
    damping_4d: float = Field(
        gt=0.0,
        lt=1.0,
        default=0.001,
        description="Relative seismic inversion damping effect between seismic "
        "vintages. This sets constraints on the relative acoustic "
        "impedance between vintages",
    )
    damping_3d: float = Field(
        gt=0.0,
        lt=1.0,
        default=0.001,
        description="Relative seismic inversion lateral damping effect. This "
        "constrains the relative acoustic impedance in each vintage so it "
        "does not deviate too much from zero",
    )
    lateral_smoothing_4d: float = Field(
        gt=0.0,
        lt=1.0,
        default=0.05,
        description="Relative seismic inversion lateral smoothing effect between "
        "seismic vintages. This will give perference to a solution with "
        "similar lateral smoothness as corresponding points in the "
        "vintages",
    )
    lateral_smoothing_3d: float = Field(
        gt=0.0,
        lt=1.0,
        default=0.01,
        description="Relative seismic inversion lateral smoothing effect within a "
        "seismic vintage",
    )
    max_iter: int = Field(
        gt=0,
        lt=1000,
        default=100,
        description="Relative seismic inversion maximum number of iterations for the "
        "linear solver",
    )
    segments: int = Field(
        gt=0,
        lt=10,
        default=1,
        description="Relative seismic inversion number of segments. If this parameter "
        "is set, the data is divided into a number of segments. Otherwise "
        "the entire cubes are inverted as once",
    )


class SeismicInversionConfig(BaseModel):
    attribute: AttributeDef = Field(
        default="relai", description="Attribute type for seismic inverted cubes"
    )
    d_syn_0: FilePath = Field(
        default=Path("../../sim2seis/output/seismic_forward/syntseis--d_syn0.sgy"),
        description="Default name for synthetic seismic data for the first vintage"
        "based on the relative inversion results and the wavelet",
    )
    d_syn_1: FilePath = Field(
        default=Path("../../sim2seis/output/seismic_forward/syntseis--d_syn1.sgy"),
        description="Default name for synthetic seismic data for the second vintage"
        "based on the relative inversion results and the wavelet",
    )
    rel_ai_0: FilePath = Field(
        default=Path("../../sim2seis/output/seismic_forward/syntseis--relai_0.sgy"),
        description="Default name for relative acoustic impedance for the first "
        "vintage",
    )
    rel_ai_1: FilePath = Field(
        default=Path("../../sim2seis/output/seismic_forward/syntseis--relai_1.sgy"),
        description="Default name for relative acoustic impedance for the second "
        "vintage",
    )
    domain: DomainDef = Field(
        default="time",
        description="Relative seismic inversion should only be run in time domain",
    )
    path: DirectoryPath = Field(
        default=Path("../../share/results/cubes"),
        description="Default directory for intermediate results",
    )
    pickle_file_prefix: str = Field(
        default="relai_diff",
        description="Pickle files are intermediate save formats in "
        "sim2seis. Each task has its own prefix for "
        "identification",
    )
    remove_unused_files: bool = Field(
        default=True,
        description="Control removal of intermediate files",
    )
    inversion_binary: FilePath = Field(
        default=Path("../../sim2seis/bin/impedance"),
        description="Directory where the binary file for relative seismic impedance "
        "is stored. This parameter will likely be removed in a coming "
        "release",
    )
    inversion_parameters: InversionParameters = Field(
        default_factory=InversionParameters
    )


class Sim2SeisConfig(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, title="Sim2Seis Configuration"
    )
    flowsim_is_prediction: bool = Field(
        description="The simulation run is either a history matching or a "
        "prediction. Setting this parameter will decide which "
        "global parameter file will be added to the sim2seis "
        "parameters"
    )
    config_file_name: SkipJsonSchema[Path] = Field(
        description="Full file name is added to the config structure",
        default=Path(r"../../sim2seis/model/sim2seis_config.yml")
    )
    seismic_fwd: SeismicForward
    amplitude_map: SkipJsonSchema[AmplitudeMapConfig] = Field(
        default_factory=AmplitudeMapConfig
    )
    attribute_definition_file: Path = Field(
        description="Yaml file with definition of all intervals for calculating "
        "attributes of forward seismic and relative inversion cubes. "
        "It is assumed to be placed in the same directory as the "
        "Yaml file for all sim2seis parameters"
    )
    depth_conversion: DepthConvertConfig
    global_params: SkipJsonSchema[FromGlobal | None] = Field(
        default=None,
    )
    inversion_map: SkipJsonSchema[InversionMapConfig] = Field(
        default_factory=InversionMapConfig
    )
    pickle_file_output_path: SkipJsonSchema[DirectoryPath] = Field(
        default=Path(r"../../share/results/pickle_files"),
        description="Directory for storing all module results in pickle format",
    )
    rel_path_global_config: SkipJsonSchema[DirectoryPath] = Field(
        default=Path(r"../../fmuconfig/output"),
        description="Relative path name for the directory where the global "
        "parameter file is stored",
    )
    seismic_diff: SkipJsonSchema[SeismicDiff] = Field(
        default_factory=SeismicDiff,
        description="Settings for calculating differences between vintages "
        "of forward model and relative seismic impedance",
    )
    seismic_inversion: SkipJsonSchema[SeismicInversionConfig] = Field(
        default_factory=SeismicInversionConfig,
        # json_schema_extra={"json_schema": SkipJsonSchema}
    )
    webviz_map: SkipJsonSchema[WebvizMap]

    @model_validator(mode="after")
    def check_sim2seis_config(self):
        if not self.attribute_definition_file.is_file():
            if self.config_file_name.parent.joinpath(
                self.attribute_definition_file
            ).is_file():
                pass
            else:
                raise ValueError(
                    f"{self.attribute_definition_file} is not recognised as a file"
                )
        return self

    # Add global parameters used in the PEM
    def update_with_global(self, global_params: dict):
        self.global_params = FromGlobal(**global_params)
        return self

    @property
    def global_config_file(self) -> FilePath:
        """Dynamically determine the global_config_file based on
        flowsim_is_prediction."""
        if self.flowsim_is_prediction:
            return FilePath("../../fmuconfig/output/global_variables_pred.yml")
        return FilePath("../../fmuconfig/output/global_variables.yml")
