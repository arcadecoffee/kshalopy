import json

from src.kshalopy.config import Config, DEFAULT_CONFIG_JSON

with open(DEFAULT_CONFIG_JSON) as infile:
    raw_json = infile.read()
reference = json.loads(raw_json)


def test_config_defaults():
    config = Config.load_defaults()
    assert config.client_id == reference["userappclientid"]
    assert config.region == reference["userpoolid"].split("_")[0]


def test_config_json_file():
    config = Config.from_app_json_file(DEFAULT_CONFIG_JSON)
    assert config.client_id == reference["userappclientid"]
    assert config.region == reference["userpoolid"].split("_")[0]


def test_config_json():
    config = Config.from_app_json(raw_json)
    assert config.client_id == reference["userappclientid"]
    assert config.region == reference["userpoolid"].split("_")[0]
