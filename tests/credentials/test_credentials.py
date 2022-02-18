import json

from datetime import datetime
from pathlib import Path

from kshalopy.credentials.credentials import AppCredentials

test_path = str(Path.joinpath(Path(__file__).parent, "test_credentials.json"))
test_path_partial = str(Path.joinpath(Path(__file__).parent, "test_partial_credentials.json"))


def test_loaded_credentials():
    credentials = AppCredentials.load_credentials(test_path)
    assert credentials.aws_credentials.secret_key == "fake_secret_key"
    assert credentials.id_token == "fake_id_token"
    assert credentials.expiration_dt == datetime(2022, 2, 18, 11, 46, 17)
    assert credentials.ttl == 0

    credentials.expiration = datetime.now().timestamp() + 3600
    assert 3600 > credentials.ttl > 3599


def test_partial_loaded_credentials():
    credentials = AppCredentials.load_credentials(test_path_partial)
    assert not credentials.aws_credentials
    assert not credentials.app_config
    assert credentials.id_token == "fake_id_token"
