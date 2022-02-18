import json

from datetime import datetime
from io import TextIOBase
from pathlib import Path

from kshalopy.credentials.credentials import AppCredentials

test_path = str(Path.joinpath(Path(__file__).parent, "test_credentials.json"))
test_path_partial = str(
    Path.joinpath(Path(__file__).parent, "test_partial_credentials.json")
)


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


def test_save_credentials(monkeypatch):
    class FakeFile(TextIOBase):
        with open(test_path) as infile:
            expected = infile.read()

        def write(self, content):
            with open(test_path) as infile:
                assert json.loads(content) == json.loads(self.expected)

    credentials = AppCredentials.load_credentials(test_path)
    monkeypatch.setattr("builtins.open", FakeFile)
    credentials.save_credentials("foo.123.json")
