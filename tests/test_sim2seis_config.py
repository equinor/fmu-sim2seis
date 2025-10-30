import pytest
from fmu.sim2seis.utilities.sim2seis_config_validation import WebvizMap

def setup_dirs(tmp_path):
    tmp_path.mkdir("grid_path")
    tmp_path.

@pytest.mark.parametrize("config, error_message",[
    ({"grid_path" : "non-existant",
      "grid_file" : "my-file",
      "zone_file" : "my_zone",
      "region_file" : "my_region",
      "attribute-error": "10",
      "output_path": "my_output"}, "")
])
def test_webvizmap_validation(tmp_path, monkeypatch, config, error_message):
    monkeypatch.chdir(tmp_path)

    #with pytest.raises(ValueError, match=error_message):
    WebvizMap(**config)

